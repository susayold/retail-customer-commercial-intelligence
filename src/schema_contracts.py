"""Validate raw source headers against the Drive-only schema contracts."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

import yaml

from src.storage_paths import require_drive_path


def read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle), [])


def validate_contract_definitions(contracts: dict[str, object]) -> None:
    """Fail closed when a source contract omits governance metadata."""
    sources = contracts.get("sources")
    if not isinstance(sources, dict) or not sources:
        raise ValueError("source contract must contain a non-empty sources mapping")
    for source_name, contract in sources.items():
        if not isinstance(contract, dict):
            raise ValueError(f"source contract {source_name} must be a mapping")
        for field in ("file", "grain", "required_columns", "primary_key", "business_key", "columns"):
            if field not in contract:
                raise ValueError(f"source contract {source_name} is missing {field}")
        required = set(contract["required_columns"])
        columns = contract["columns"]
        if not isinstance(columns, dict) or not required.issubset(columns):
            missing = sorted(required - set(columns if isinstance(columns, dict) else {}))
            raise ValueError(f"source contract {source_name} is missing column metadata: {missing}")
        for column_name in required:
            metadata = columns[column_name]
            if not isinstance(metadata, dict) or not metadata.get("type") or "nullable" not in metadata:
                raise ValueError(f"source contract {source_name}.{column_name} needs type and nullable metadata")
        for key_name in ("primary_key", "business_key"):
            if not all(isinstance(column, str) and column in columns for column in contract[key_name]):
                raise ValueError(f"source contract {source_name}.{key_name} references an unknown column")


def validate_headers(input_dir: Path, contract_path: Path) -> list[dict[str, object]]:
    contracts = yaml.safe_load(contract_path.read_text(encoding="utf-8"))["sources"]
    validate_contract_definitions({"sources": contracts})
    rows: list[dict[str, object]] = []
    for source_name, contract in contracts.items():
        file_name = contract["file"]
        path = input_dir / file_name
        if not path.exists():
            rows.append({
                "source_name": source_name,
                "file_name": file_name,
                "status": "missing_file",
                "missing_columns": "",
                "unexpected_columns": "",
                "duplicate_columns": "",
                "observed_column_count": None,
            })
            continue

        observed = read_header(path)
        required = set(contract["required_columns"])
        missing = sorted(required - set(observed))
        unexpected = sorted(set(observed) - required)
        duplicate = sorted(
            name for name, count in Counter(observed).items() if count > 1
        )
        if duplicate:
            status = "duplicate_columns"
        elif missing:
            status = "missing_columns"
        elif unexpected:
            status = "unexpected_columns"
        else:
            status = "ok"
        rows.append({
            "source_name": source_name,
            "file_name": file_name,
            "status": status,
            "missing_columns": "|".join(missing),
            "unexpected_columns": "|".join(unexpected),
            "duplicate_columns": "|".join(duplicate),
            "observed_column_count": len(observed),
        })
    return rows


def write_report(rows: list[dict[str, object]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_name",
        "file_name",
        "status",
        "missing_columns",
        "unexpected_columns",
        "duplicate_columns",
        "observed_column_count",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--contracts", type=Path, default=Path("config/source_contracts.yaml"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--drive-root", type=Path, required=True)
    args = parser.parse_args()

    input_root = require_drive_path(args.input, args.drive_root, "--input")
    output_path = require_drive_path(args.output, args.drive_root, "--output")
    rows = validate_headers(input_root, args.contracts)
    write_report(rows, output_path)
    failures = [row for row in rows if row["status"] != "ok"]
    print({"sources": len(rows), "failures": len(failures), "output": str(output_path)})
    if failures:
        raise SystemExit("Schema validation failed; inspect the Drive QA report")


if __name__ == "__main__":
    main()
