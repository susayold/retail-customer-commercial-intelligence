"""Write the Drive-backed data run manifest and DATA_READY marker."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.export_powerbi import POWERBI_OUTPUT_NAMES
from src.inventory import EXPECTED_FILES
from src.storage_paths import require_drive_path


REQUIRED_PARQUET_FILES = tuple(f"{Path(name).stem}.parquet" for name in EXPECTED_FILES)
REQUIRED_POWERBI_EXPORTS = tuple(
    f"{name}.parquet" for name in POWERBI_OUTPUT_NAMES.values()
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size == 0:
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except (OSError, csv.Error):
        return []


def _has_rows(path: Path) -> bool:
    """Return true when an informational QA export exists and is non-empty."""
    return bool(_read_csv_rows(path))


def _all_pass(path: Path) -> bool:
    rows = _read_csv_rows(path)
    return bool(rows) and all(str(row.get("status", "")).strip().lower() == "pass" for row in rows)


def _all_zero(path: Path, column: str) -> bool:
    """Validate zero-violation QA exports whose contract has no status column."""
    rows = _read_csv_rows(path)
    if not rows:
        return False
    try:
        return all(float(str(row.get(column, "")).strip()) == 0 for row in rows)
    except (TypeError, ValueError):
        return False


def _git_commit(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _file_record(path: Path, relative_to: Path) -> dict[str, Any]:
    relative = str(path.relative_to(relative_to)).replace("\\", "/")
    if not path.is_file():
        return {"path": relative, "status": "MISSING"}
    return {
        "path": relative,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "status": "PRESENT",
    }


def write_data_readiness(
    artifact_root: Path,
    repo_root: Path,
    pipeline_run_id: str,
    started_at: str,
    completed_at: str | None = None,
) -> dict[str, Any]:
    artifact_root = artifact_root.expanduser().resolve()
    repo_root = repo_root.expanduser().resolve()
    completed_at = completed_at or datetime.now(timezone.utc).isoformat()
    raw_root = artifact_root / "01_raw_source"
    curated_root = artifact_root / "02_curated_parquet"
    warehouse_root = artifact_root / "03_duckdb_and_marts"
    qa_root = artifact_root / "04_qa_reports"
    docs_root = artifact_root / "06_source_docs"
    pbi_root = artifact_root / "05_powerbi_exports"
    governed_audit = qa_root / "governed_asset_audit.json"

    raw_files = [
        _file_record(raw_root / name, artifact_root) for name in EXPECTED_FILES
    ]
    parquet_files = [
        _file_record(curated_root / name, artifact_root)
        for name in REQUIRED_PARQUET_FILES
    ]
    database = warehouse_root / "retail_intelligence.duckdb"
    source_ready = _read_json(docs_root / "source_ready.json")
    quality_gate = _read_json(qa_root / "qa_quality_gate.json")
    acquisition_manifest = docs_root / "acquisition_manifest.json"

    source_gate = (
        source_ready.get("status") == "READY"
        and source_ready.get("checksum_status") == "PASS"
        and len(raw_files) == len(EXPECTED_FILES)
        and all(item.get("status") == "PRESENT" for item in raw_files)
    )
    curated_gate = (
        len(parquet_files) == len(REQUIRED_PARQUET_FILES)
        and all(item.get("status") == "PRESENT" for item in parquet_files)
        and _has_rows(qa_root / "qa_source_reconciliation.csv")
    )
    warehouse_gate = (
        database.is_file()
        and database.stat().st_size > 0
        and _all_pass(qa_root / "qa_layer_reconciliation.csv")
        and _all_zero(qa_root / "qa_key_audit.csv", "duplicate_rows")
        and _all_zero(qa_root / "qa_grain_audit.csv", "violating_baskets")
    )
    marts_gate = all(
        (pbi_root / name).is_file() or (pbi_root / name.replace(".parquet", ".csv")).is_file()
        for name in REQUIRED_POWERBI_EXPORTS
    )
    governed_asset_gate = (
        governed_audit.is_file()
        and _read_json(governed_audit).get("status") == "PASS"
    )
    blocking_issues = sum(
        not gate for gate in (source_gate, curated_gate, warehouse_gate, marts_gate, governed_asset_gate)
    )
    data_ready = blocking_issues == 0 and quality_gate.get("ready") is True

    qa_outputs = sorted(
        str(path.relative_to(artifact_root)).replace("\\", "/")
        for path in qa_root.rglob("*")
        if path.is_file() and path.stat().st_size > 0
    )
    export_files = [
        _file_record(path, artifact_root)
        for path in sorted(pbi_root.glob("*.parquet"))
        if path.is_file()
    ]
    output_hashes = {
        item["path"]: item["sha256"]
        for item in export_files
        if item.get("status") == "PRESENT"
    }
    source_manifest_sha = _sha256(acquisition_manifest) if acquisition_manifest.is_file() else ""
    manifest = {
        "source_manifest_sha": source_manifest_sha,
        "source_ready_verified_at": source_ready.get("acquired_at", ""),
        "repo_commit_sha": _git_commit(repo_root),
        "pipeline_run_id": pipeline_run_id,
        "raw_files": raw_files,
        "parquet_files": parquet_files,
        "database_path": str(database.relative_to(artifact_root)).replace("\\", "/"),
        "qa_outputs": qa_outputs,
        "output_files": export_files,
        "output_hashes": output_hashes,
        "governed_asset_audit": _file_record(governed_audit, artifact_root),
        "started_at": started_at,
        "completed_at": completed_at,
        "status": "SUCCESS" if data_ready else "FAILED",
    }
    ready_marker = {
        "status": "DATA_READY" if data_ready else "DATA_NOT_READY",
        "scope": "data_layer_only",
        "source_gate": "PASS" if source_gate else "FAIL",
        "curated_gate": "PASS" if curated_gate else "FAIL",
        "warehouse_gate": "PASS" if warehouse_gate else "FAIL",
        "marts_gate": "PASS" if marts_gate else "FAIL",
        "governed_asset_gate": "PASS" if governed_asset_gate else "FAIL",
        "blocking_issues": blocking_issues,
        "pipeline_run_id": pipeline_run_id,
        "verified_at": completed_at,
        "qa_warnings": quality_gate.get("warnings", []),
    }
    docs_root.mkdir(parents=True, exist_ok=True)
    (docs_root / "data_run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (docs_root / "data_ready.json").write_text(
        json.dumps(ready_marker, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"manifest": manifest, "data_ready": ready_marker}


def main() -> None:
    parser = argparse.ArgumentParser(description="Write Drive-backed data readiness markers.")
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--drive-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--pipeline-run-id", required=True)
    parser.add_argument("--started-at", required=True)
    args = parser.parse_args()

    artifact_root = require_drive_path(args.artifact_root, args.drive_root, "--artifact-root")
    result = write_data_readiness(
        artifact_root=artifact_root,
        repo_root=args.repo_root,
        pipeline_run_id=args.pipeline_run_id,
        started_at=args.started_at,
    )
    print(json.dumps(result["data_ready"], ensure_ascii=False, indent=2, sort_keys=True))
    if result["data_ready"]["status"] != "DATA_READY":
        raise SystemExit("Data readiness failed; inspect 06_source_docs/data_ready.json")


if __name__ == "__main__":
    main()
