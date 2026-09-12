"""Fail-closed verifier for a Drive-backed READY source package."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.source_acquisition import sha256_file
from src.source_manifest import EXPECTED_SOURCE_FILES
from src.storage_paths import require_drive_path


def verify_source_ready(
    raw_dir: Path,
    docs_dir: Path,
    expected_files: tuple[str, ...] = EXPECTED_SOURCE_FILES,
) -> dict[str, Any]:
    failures: list[str] = []
    raw = raw_dir.resolve()
    docs = docs_dir.resolve()
    if not raw.is_dir():
        failures.append("raw_folder_missing")
    else:
        entries = list(raw.rglob("*"))
        files = [path for path in entries if path.is_file()]
        directories = [path for path in entries if path.is_dir()]
        if directories:
            failures.append("raw_nested_directories_present")
        relative = [str(path.relative_to(raw)) for path in files]
        if set(relative) != set(expected_files):
            failures.append("raw_exact_file_set_failed")
        if len(relative) != len(set(relative)):
            failures.append("raw_duplicate_paths_present")
        if any(path.stat().st_size <= 0 for path in files):
            failures.append("raw_zero_byte_file_present")
    marker_path = docs / "source_ready.json"
    provenance_path = docs / "source_provenance.json"
    checksums_path = docs / "source_checksums.csv"
    marker: dict[str, Any] = {}
    provenance: dict[str, Any] = {}
    if not marker_path.is_file():
        failures.append("source_ready_marker_missing")
    else:
        try:
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            failures.append(f"source_ready_marker_invalid:{error}")
    if marker.get("status") != "READY":
        failures.append("source_ready_marker_not_READY")
    if marker.get("verified_file_count") != len(expected_files):
        failures.append("source_ready_marker_file_count_failed")
    if marker.get("checksum_status") != "PASS":
        failures.append("source_ready_marker_checksum_failed")
    if not provenance_path.is_file():
        failures.append("source_provenance_missing")
    else:
        try:
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            failures.append(f"source_provenance_invalid:{error}")
    if not provenance.get("provider"):
        failures.append("source_provenance_provider_missing")
    if not provenance.get("acquired_at"):
        failures.append("source_provenance_acquired_at_missing")
    if not isinstance(provenance.get("files"), list):
        failures.append("source_provenance_files_missing")
    checksum_rows: dict[str, dict[str, str]] = {}
    if not checksums_path.is_file():
        failures.append("source_checksums_missing")
    else:
        try:
            with checksums_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames != ["file", "size", "sha256"]:
                    failures.append("source_checksums_header_failed")
                for row in reader:
                    file_name = row.get("file", "")
                    if file_name in checksum_rows:
                        failures.append(f"source_checksums_duplicate:{file_name}")
                    checksum_rows[file_name] = row
        except (OSError, csv.Error) as error:
            failures.append(f"source_checksums_invalid:{error}")
    if set(checksum_rows) != set(expected_files):
        failures.append("source_checksums_exact_file_set_failed")
    if raw.is_dir():
        for file_name in expected_files:
            path = raw / file_name
            row = checksum_rows.get(file_name)
            if not path.is_file() or row is None:
                continue
            try:
                if int(row.get("size", "-1")) != path.stat().st_size:
                    failures.append(f"size_mismatch:{file_name}")
            except ValueError:
                failures.append(f"invalid_size:{file_name}")
            if row.get("sha256") != sha256_file(path):
                failures.append(f"checksum_mismatch:{file_name}")
    provenance_files = {
        str(row.get("file")): row
        for row in provenance.get("files", [])
        if isinstance(row, dict)
    }
    if set(provenance_files) != set(expected_files):
        failures.append("source_provenance_exact_file_set_failed")
    return {
        "status": "READY" if not failures else "NOT_READY",
        "raw_dir": str(raw),
        "docs_dir": str(docs),
        "expected_file_count": len(expected_files),
        "failures": sorted(set(failures)),
        "marker": marker,
        "provenance": provenance,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a Drive source package before pipeline execution")
    parser.add_argument("--drive-root", type=Path, required=True)
    args = parser.parse_args()
    drive = require_drive_path(args.drive_root, args.drive_root, "--drive-root")
    raw = require_drive_path(drive / "01_raw_source", drive, "raw folder")
    docs = require_drive_path(drive / "06_source_docs", drive, "docs folder")
    result = verify_source_ready(raw, docs)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["status"] != "READY":
        raise SystemExit("Source readiness verification failed; inspect Drive evidence")


if __name__ == "__main__":
    main()
