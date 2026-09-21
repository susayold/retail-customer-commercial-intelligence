"""Inventory the exact Drive-backed raw CSV contract without local staging."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from src.source_manifest import EXPECTED_ROW_COUNTS, EXPECTED_SOURCE_FILES
from src.storage_paths import require_drive_path

# Backward-compatible aliases for downstream imports. The manifest is canonical.
EXPECTED_FILES = EXPECTED_SOURCE_FILES


def column_hash(columns: Iterable[str]) -> str:
    payload = "|".join(columns).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_csv(path: Path, expected_row_count: int | None = None) -> dict[str, object]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        rows = sum(1 for _ in reader)
    row_count_delta = rows - expected_row_count if expected_row_count is not None else None
    planning_expectation_status = (
        "match"
        if expected_row_count is not None and row_count_delta == 0
        else "review"
        if expected_row_count is not None
        else "not_configured"
    )
    return {
        "file_name": path.name,
        "file_size_bytes": path.stat().st_size,
        "modified_time": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        "row_count": rows,
        "expected_row_count": expected_row_count,
        "row_count_delta": row_count_delta,
        "planning_expectation_status": planning_expectation_status,
        "column_count": len(header),
        "column_names_hash": column_hash(header),
        "content_sha256": content_hash(path),
        "expected_schema_version": "v1",
        "load_status": "ok",
        "ingestion_status": "ok",
    }


def inventory(input_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name in EXPECTED_SOURCE_FILES:
        path = input_dir / name
        if path.exists():
            rows.append(inspect_csv(path, EXPECTED_ROW_COUNTS.get(name)))
        else:
            rows.append({
                "file_name": name,
                "file_size_bytes": None,
                "modified_time": None,
                "row_count": None,
                "expected_row_count": EXPECTED_ROW_COUNTS.get(name),
                "row_count_delta": None,
                "planning_expectation_status": "missing",
                "column_count": None,
                "column_names_hash": None,
                "content_sha256": None,
                "expected_schema_version": "v1",
                "load_status": "missing",
                "ingestion_status": "missing",
            })
    return rows


def write_inventory(rows: list[dict[str, object]], output: Path) -> None:
    if not rows:
        raise ValueError("Inventory cannot be written without source rows")
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--drive-root", type=Path, required=True)
    args = parser.parse_args()
    input_root = require_drive_path(args.input, args.drive_root, "--input")
    output_path = require_drive_path(args.output, args.drive_root, "--output")
    rows = inventory(input_root)
    write_inventory(rows, output_path)
    missing = [row["file_name"] for row in rows if row["load_status"] != "ok"]
    print(json.dumps({"files": len(rows), "missing": missing, "output": str(output_path)}))
    if missing:
        raise SystemExit("Source inventory failed: missing expected files")


if __name__ == "__main__":
    main()
