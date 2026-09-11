"""Validate raw source headers against the Drive-only schema contracts."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import yaml


def read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle), [])


def validate_headers(input_dir: Path, contract_path: Path) -> list[dict[str, object]]:
    contracts = yaml.safe_load(contract_path.read_text(encoding="utf-8"))["sources"]
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
                "observed_column_count": None,
            })
            continue
        observed = read_header(path)
        required = set(contract["required_columns"])
        missing = sorted(required - set(observed))
        rows.append({
            "source_name": source_name,
            "file_name": file_name,
            "status": "ok" if not missing else "missing_columns",
            "missing_columns": "|".join(missing),
            "observed_column_count": len(observed),
        })
    return rows


def write_report(rows: list[dict[str, object]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["source_name", "file_name", "status", "missing_columns", "observed_column_count"]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--contracts", type=Path, default=Path("config/source_contracts.yaml"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = validate_headers(args.input, args.contracts)
    write_report(rows, args.output)
    failures = [row for row in rows if row["status"] != "ok"]
    print({"sources": len(rows), "failures": len(failures), "output": str(args.output)})
    if failures:
        raise SystemExit("Schema validation failed; inspect the Drive QA report")


if __name__ == "__main__":
    main()