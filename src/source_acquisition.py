"""Drive-only acquisition, validation and promotion for the eight raw sources.

The module deliberately keeps acquisition records and all temporary bytes below
the declared Drive project root. It never writes source data to the repository.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import re
import shutil
import stat
import subprocess
import urllib.request
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any

import yaml

from src.source_manifest import (
    EXPECTED_ROW_COUNTS,
    EXPECTED_SOURCE_FILES,
    MANIFEST_VERSION,
    SOURCE_NAME_BY_FILE,
)
from src.storage_paths import require_drive_path

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "source_acquisition.yaml"
CHUNK_SIZE_BYTES = 8 * 1024 * 1024
_HTML_MARKERS = (
    "<html",
    "<!doctype",
    "<body",
    "access denied",
    "sign in",
    "login",
    "error 403",
)


class AcquisitionError(RuntimeError):
    """Raised when a source cannot be promoted to the exact raw contract."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _drive_path(path: Path, drive_root: Path, label: str) -> Path:
    return require_drive_path(path, drive_root, label)


def load_acquisition_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    for section in ("dataset", "official", "kaggle", "drive", "policy"):
        if not isinstance(config.get(section), dict):
            raise AcquisitionError(f"Acquisition config is missing section: {section}")
    return config


def resolve_drive_paths(drive_root: Path) -> dict[str, Path]:
    drive = _drive_path(drive_root, drive_root, "--drive-root")
    raw = _drive_path(drive / "01_raw_source", drive, "raw folder")
    docs = _drive_path(drive / "06_source_docs", drive, "docs folder")
    staging = _drive_path(docs / "acquisition_staging", drive, "staging folder")
    return {"drive_root": drive, "raw": raw, "docs": docs, "staging": staging}


def sha256_file(path: Path, chunk_size: int = CHUNK_SIZE_BYTES) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _append_log(path: Path, event: str, **details: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": _now(), "event": event, **details}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle), [])


def _contract_map(contracts_path: Path) -> dict[str, dict[str, Any]]:
    raw = yaml.safe_load(contracts_path.read_text(encoding="utf-8")) or {}
    sources = raw.get("sources")
    if not isinstance(sources, dict):
        raise AcquisitionError(f"Invalid source contracts: {contracts_path}")
    result: dict[str, dict[str, Any]] = {}
    for source_name, contract in sources.items():
        if not isinstance(contract, dict) or not contract.get("file"):
            raise AcquisitionError(f"Invalid contract for {source_name}")
        result[str(contract["file"])] = contract
    missing = set(EXPECTED_SOURCE_FILES) - set(result)
    if missing:
        raise AcquisitionError(f"Contracts missing expected files: {sorted(missing)}")
    return result


def csv_header_precheck(
    path: Path,
    required_columns: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    """Return a deterministic header preview without reading the whole source."""
    try:
        header = _read_header(path)
    except (OSError, UnicodeError, csv.Error) as error:
        raise AcquisitionError(f"Unreadable CSV header: {path.name}: {error}") from error
    if not header or any(not str(column).strip() for column in header):
        raise AcquisitionError(f"Empty or invalid CSV header: {path.name}")
    if len(set(header)) != len(header):
        duplicates = sorted({column for column in header if header.count(column) > 1})
        raise AcquisitionError(f"Duplicate CSV headers in {path.name}: {duplicates}")
    required = set(required_columns)
    observed = set(header)
    missing = sorted(required - observed)
    unexpected = sorted(observed - required)
    return {
        "file": path.name,
        "header": header,
        "missing_columns": missing,
        "unexpected_columns": unexpected,
        "status": "PASS" if not missing and not unexpected else "FAIL",
    }


def _csv_sanity_check(path: Path) -> None:
    if not path.is_file() or path.stat().st_size <= 0:
        raise AcquisitionError(f"CSV is missing or zero-byte: {path.name}")
    try:
        with path.open("rb") as binary:
            preview = binary.read(4096).decode("utf-8-sig", errors="strict")
    except (OSError, UnicodeError) as error:
        raise AcquisitionError(f"CSV is not readable UTF-8: {path.name}: {error}") from error
    lower = preview.lstrip().lower()
    if any(lower.startswith(marker) or marker in lower[:512] for marker in _HTML_MARKERS):
        raise AcquisitionError(f"Expected CSV but received HTML/login/error body: {path.name}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            if not header:
                raise AcquisitionError(f"CSV has no header: {path.name}")
            # Read a small preview to catch inaccessible or obviously malformed
            # responses without loading multi-gigabyte sources into memory.
            for _ in range(5):
                next(reader, None)
    except (OSError, UnicodeError, csv.Error) as error:
        raise AcquisitionError(f"CSV sanity check failed: {path.name}: {error}") from error


def validate_csv_file(path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    _csv_sanity_check(path)
    preview = csv_header_precheck(path, contract["required_columns"])
    if preview["status"] != "PASS":
        raise AcquisitionError(
            f"Header contract failed for {path.name}: "
            f"missing={preview['missing_columns']} "
            f"unexpected={preview['unexpected_columns']}"
        )
    return {
        "file": path.name,
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
        "header": preview["header"],
        "expected_row_count": EXPECTED_ROW_COUNTS.get(path.name),
    }


def safe_extract_zip(archive_path: Path, destination: Path) -> list[str]:
    """Extract an archive only when every member stays below destination."""
    if not archive_path.is_file() or archive_path.stat().st_size <= 0:
        raise AcquisitionError(f"Archive is missing or zero-byte: {archive_path}")
    if not zipfile.is_zipfile(archive_path):
        raise AcquisitionError(f"Downloaded file is not a readable ZIP: {archive_path.name}")
    destination.mkdir(parents=True, exist_ok=True)
    extracted: list[str] = []
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                name = info.filename
                normalized = name.replace("\\", "/")
                parts = [part for part in normalized.split("/") if part]
                if (
                    not parts
                    or "\x00" in name
                    or normalized.startswith("/")
                    or PureWindowsPath(name).drive
                    or any(part in ("..", ".") for part in parts)
                ):
                    raise AcquisitionError(f"Unsafe ZIP member path: {name!r}")
                target = (destination / Path(*parts)).resolve()
                if not _inside(target, destination):
                    raise AcquisitionError(f"ZIP member escapes staging directory: {name!r}")
                mode = (info.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(mode):
                    raise AcquisitionError(f"Symlink ZIP member is not allowed: {name!r}")
                if info.is_dir() or normalized.endswith("/"):
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info, "r") as source, target.open("wb") as sink:
                    shutil.copyfileobj(source, sink, length=1024 * 1024)
                extracted.append(str(target))
    except zipfile.BadZipFile as error:
        raise AcquisitionError(f"Corrupt ZIP: {archive_path.name}") from error
    return extracted


def discover_expected_files(extracted_root: Path) -> dict[str, Path]:
    """Find each expected basename exactly once in a recursively extracted tree."""
    all_files = sorted(path for path in extracted_root.rglob("*") if path.is_file())
    result: dict[str, Path] = {}
    duplicates: dict[str, list[str]] = {}
    for expected in EXPECTED_SOURCE_FILES:
        matches = [path for path in all_files if path.name == expected]
        if len(matches) == 1:
            result[expected] = matches[0]
        elif len(matches) > 1:
            duplicates[expected] = [str(path) for path in matches]
    missing = [name for name in EXPECTED_SOURCE_FILES if name not in result and name not in duplicates]
    unexpected_csv = sorted(
        str(path.relative_to(extracted_root))
        for path in all_files
        if path.suffix.lower() == ".csv" and path.name not in EXPECTED_SOURCE_FILES
    )
    if missing or duplicates or unexpected_csv:
        raise AcquisitionError(
            "Archive does not contain the exact expected CSV set: "
            f"missing={missing}, duplicates={duplicates}, "
            f"unexpected_csv={unexpected_csv}"
        )
    return result


def _copy_checked(source: Path, destination: Path) -> None:
    if source.is_symlink():
        raise AcquisitionError(f"Symlink source is not allowed: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _copy_directory_to_staging(source: Path, destination: Path) -> None:
    if _inside(destination, source):
        raise AcquisitionError("Manual input directory cannot contain its own staging destination")
    for path in source.rglob("*"):
        if path.is_file():
            relative = path.relative_to(source)
            _copy_checked(path, destination / relative)


def _download_stream(url: str, target: Path, chunk_size: int) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "retail-customer-commercial-intelligence/1.0"},
        )
        with urllib.request.urlopen(request, timeout=60) as response, target.open("wb") as sink:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                sink.write(chunk)
    except Exception as error:
        target.unlink(missing_ok=True)
        raise AcquisitionError(f"Official source download failed: {url}: {error}") from error
    if not target.is_file() or target.stat().st_size <= 0:
        raise AcquisitionError(f"Official source returned an empty asset: {url}")
    return {"size": target.stat().st_size, "sha256": sha256_file(target)}


def _download_kaggle(slug: str, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["kaggle", "datasets", "download", "-d", slug, "-p", str(target_dir), "--force"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AcquisitionError(
            "Kaggle download failed; confirm Kaggle credentials and terms before retrying: "
            + (result.stderr.strip() or result.stdout.strip())
        )
    archives = sorted(target_dir.glob("*.zip"))
    if len(archives) != 1:
        raise AcquisitionError(
            f"Kaggle provider must produce exactly one ZIP, found {len(archives)}"
        )
    return archives[0]


def _raw_state(raw_dir: Path) -> dict[str, Any]:
    if not raw_dir.exists():
        return {"status": "EMPTY", "files": [], "errors": []}
    entries = list(raw_dir.rglob("*"))
    files = [path for path in entries if path.is_file()]
    directories = [path for path in entries if path.is_dir()]
    relative_files = [str(path.relative_to(raw_dir)) for path in files]
    errors: list[str] = []
    if directories:
        errors.append("nested_directories_present")
    if any(path.stat().st_size <= 0 for path in files):
        errors.append("zero_byte_file_present")
    names = [path.name for path in files]
    if len(names) != len(set(names)):
        errors.append("duplicate_basenames_present")
    if set(names) != set(EXPECTED_SOURCE_FILES):
        errors.append("file_set_is_not_exact")
    if errors:
        return {"status": "INVALID", "files": relative_files, "errors": errors}
    return {"status": "COMPLETE", "files": sorted(relative_files), "errors": []}


def _stage_verified(
    discovered: dict[str, Path],
    verified_dir: Path,
    contracts: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    verified_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for file_name in EXPECTED_SOURCE_FILES:
        source = discovered[file_name]
        destination = verified_dir / file_name
        _copy_checked(source, destination)
        rows.append(validate_csv_file(destination, contracts[file_name]))
    return rows


def _promote_verified_files(
    verified_dir: Path,
    raw_dir: Path,
    run_id: str,
    checksums: dict[str, str],
) -> None:
    existing = _raw_state(raw_dir)
    if existing["status"] != "EMPTY":
        raise AcquisitionError(f"Raw promotion requires an empty raw folder: {existing}")
    raw_dir.parent.mkdir(parents=True, exist_ok=True)
    candidate = raw_dir.parent / f".{raw_dir.name}.candidate-{run_id}"
    if candidate.exists():
        raise AcquisitionError(f"Promotion candidate already exists: {candidate}")
    candidate.mkdir(parents=True)
    try:
        for file_name in EXPECTED_SOURCE_FILES:
            source = verified_dir / file_name
            target = candidate / file_name
            _copy_checked(source, target)
            if sha256_file(target) != checksums[file_name]:
                raise AcquisitionError(f"Promotion checksum mismatch: {file_name}")
        if set(path.name for path in candidate.iterdir()) != set(EXPECTED_SOURCE_FILES):
            raise AcquisitionError("Promotion candidate does not have the exact source set")
        if raw_dir.exists():
            backup = raw_dir.parent / f".{raw_dir.name}.empty-backup-{run_id}"
            raw_dir.rename(backup)
            try:
                candidate.rename(raw_dir)
            except Exception:
                backup.rename(raw_dir)
                raise
            backup.rmdir()
        else:
            candidate.rename(raw_dir)
    except Exception:
        # Preserve the candidate under Drive for diagnosis; it is never treated
        # as an active raw source because it is outside 01_raw_source.
        raise


def _write_checksums(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "size", "sha256"])
        writer.writeheader()
        for row in rows:
            writer.writerow({"file": row["file"], "size": row["size"], "sha256": row["sha256"]})
    os.replace(temporary, path)


def _source_context(
    config: dict[str, Any],
    provider: str,
    run_id: str,
    drive: Path,
    archive: Path | None,
) -> dict[str, Any]:
    official = config["official"]
    archive_metadata: dict[str, Any] | None = None
    if archive is not None and archive.is_file():
        archive_metadata = {
            "file": str(archive.relative_to(drive)),
            "size": archive.stat().st_size,
            "sha256": sha256_file(archive),
        }
    return {
        "run_id": run_id,
        "dataset": config["dataset"]["name"],
        "manifest_version": config["dataset"].get("manifest_version", MANIFEST_VERSION),
        "provider": provider,
        "landing_page": official.get("landing_page", "") if provider == "official" else "",
        "direct_asset_url": official.get("direct_asset_url", "") if provider == "official" else "",
        "acquired_at": _now(),
        "archive": archive_metadata,
    }


def acquire_source(
    provider: str,
    drive_root: Path,
    input_path: Path | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
    contracts_path: Path | None = None,
) -> dict[str, Any]:
    """Acquire, validate and safely promote exactly eight sources under Drive."""
    if provider not in {"official", "kaggle", "manual"}:
        raise AcquisitionError(f"Unsupported provider: {provider}")
    paths = resolve_drive_paths(drive_root)
    config = load_acquisition_config(config_path)
    contracts_file = contracts_path or DEFAULT_CONFIG_PATH.parents[0] / "source_contracts.yaml"
    contracts = _contract_map(contracts_file)
    run_id = "run_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    run_dir = paths["staging"] / run_id
    download_dir = run_dir / "download"
    extracted_dir = run_dir / "extracted"
    verified_dir = run_dir / "verified"
    log_path = paths["docs"] / "acquisition_run.log"
    manifest_path = paths["docs"] / "acquisition_manifest.json"
    base = _source_context(config, provider, run_id, paths["drive_root"], None)
    base.update({
        "status": "RUNNING",
        "staging_run": str(run_dir.relative_to(paths["drive_root"])),
        "raw_state_before": _raw_state(paths["raw"]),
    })
    _write_json(manifest_path, base)
    _append_log(log_path, "acquisition_started", **base)
    archive: Path | None = None
    try:
        if provider == "official":
            url = str(config["official"].get("direct_asset_url", "")).strip()
            if not url:
                raise AcquisitionError("Official direct_asset_url is not configured")
            archive = download_dir / "dunnhumby_The-Complete-Journey.zip"
            _download_stream(url, archive, int(config["policy"].get("chunk_size_bytes", CHUNK_SIZE_BYTES)))
            safe_extract_zip(archive, extracted_dir)
        elif provider == "kaggle":
            slug = str(config["kaggle"].get("dataset_slug", "")).strip()
            if not slug:
                raise AcquisitionError("Kaggle dataset_slug is not configured")
            archive = _download_kaggle(slug, download_dir)
            safe_extract_zip(archive, extracted_dir)
        else:
            if input_path is None:
                raise AcquisitionError("Manual provider requires --input pointing to Drive")
            manual = _drive_path(input_path, paths["drive_root"], "--input")
            if manual.is_file():
                if manual.suffix.lower() != ".zip":
                    raise AcquisitionError("Manual input file must be a ZIP archive")
                archive = download_dir / manual.name
                _copy_checked(manual, archive)
                safe_extract_zip(archive, extracted_dir)
            elif manual.is_dir():
                _copy_directory_to_staging(manual, extracted_dir)
            else:
                raise AcquisitionError(f"Manual input does not exist: {manual}")

        discovered = discover_expected_files(extracted_dir)
        file_rows = _stage_verified(discovered, verified_dir, contracts)
        checksums = {row["file"]: row["sha256"] for row in file_rows}
        raw_state = _raw_state(paths["raw"])
        base["raw_state_before"] = raw_state
        if raw_state["status"] == "INVALID":
            raise AcquisitionError(f"Existing raw folder is not promotable: {raw_state}")
        outcome = "PROMOTED"
        if raw_state["status"] == "COMPLETE":
            current = {
                path.name: sha256_file(path)
                for path in paths["raw"].iterdir()
                if path.is_file()
            }
            if current != checksums:
                raise AcquisitionError(
                    "Existing exact raw set differs from the candidate; "
                    "overwrite_existing=false prevents replacement"
                )
            outcome = "NO_OP"
        else:
            _promote_verified_files(verified_dir, paths["raw"], run_id, checksums)

        final_rows = [
            {
                "file": file_name,
                "size": (paths["raw"] / file_name).stat().st_size,
                "sha256": sha256_file(paths["raw"] / file_name),
            }
            for file_name in EXPECTED_SOURCE_FILES
        ]
        if {row["file"] for row in final_rows} != set(EXPECTED_SOURCE_FILES):
            raise AcquisitionError("Final raw folder failed exact file-set verification")
        if any(row["sha256"] != checksums[row["file"]] for row in final_rows):
            raise AcquisitionError("Final raw checksum verification failed")
        context = _source_context(config, provider, run_id, paths["drive_root"], archive)
        context.update({
            "status": "READY",
            "outcome": outcome,
            "staging_run": str(run_dir.relative_to(paths["drive_root"])),
            "raw_state_before": raw_state,
            "verified_file_count": len(final_rows),
            "files": final_rows,
            "checksum_status": "PASS",
        })
        _write_json(paths["docs"] / "source_provenance.json", context)
        _write_checksums(paths["docs"] / "source_checksums.csv", final_rows)
        _write_json(paths["docs"] / "source_ready.json", {
            "status": "READY",
            "dataset": context["dataset"],
            "provider": provider,
            "verified_file_count": len(final_rows),
            "checksum_status": "PASS",
            "acquired_at": context["acquired_at"],
            "run_id": run_id,
            "outcome": outcome,
        })
        _write_json(manifest_path, context)
        _append_log(log_path, "acquisition_ready", **context)
        return context
    except Exception as error:
        failure = dict(base)
        failure.update({
            "status": "FAIL",
            "error": str(error),
            "archive": (
                {
                    "file": str(archive.relative_to(paths["drive_root"])),
                    "size": archive.stat().st_size,
                    "sha256": sha256_file(archive),
                }
                if archive is not None and archive.is_file()
                else None
            ),
        })
        _write_json(manifest_path, failure)
        _append_log(log_path, "acquisition_failed", **failure)
        if isinstance(error, AcquisitionError):
            raise
        raise AcquisitionError(str(error)) from error


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire the exact eight retail source CSVs into Drive")
    parser.add_argument("--provider", choices=("official", "kaggle", "manual"), required=True)
    parser.add_argument("--drive-root", type=Path, required=True)
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--contracts", type=Path, default=None)
    args = parser.parse_args()
    try:
        result = acquire_source(
            provider=args.provider,
            drive_root=args.drive_root,
            input_path=args.input,
            config_path=args.config,
            contracts_path=args.contracts,
        )
    except AcquisitionError as error:
        raise SystemExit(f"Source acquisition failed: {error}") from error
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
