"""Inventory source CSVs without loading the full dataset into memory."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable

EXPECTED_FILES = (
    "transaction_data.csv",
    "causal_data.csv",
    "coupon.csv",
    "coupon_redempt.csv",
    "campaign_table.csv",
    "campaign_desc.csv",
    "product.csv",
    "hh_demographic.csv",
)


def column_hash(columns: Iterable[str]) -> str:
    payload = "|".join(columns).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def inspect_csv(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        rows = sum(1 for _ in reader)
    return {
        "file_name": path.name,
        "file_size_bytes": path.stat().st_size,
        "row_count": rows,
        "column_count": len(header),
        "column_names_hash": column_hash(header),
        "load_status": "ok",
    }


def inventory(input_dir: Path) -> list[dict[str, object]]:
    rows = []
    for name in EXPECTED_FILES:
        path = input_dir / name
        if path.exists():
            rows.append(inspect_csv(path))
        else:
            rows.append({
                "file_name": name,
                "file_size_bytes": None,
                "row_count": None,
                "column_count": None,
                "column_names_hash": None,
                "load_status": "missing",
            })
    return rows


def write_inventory(rows: list[dict[str, object]], output: Path) -> None:
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
    args = parser.parse_args()
    rows = inventory(args.input)
    write_inventory(rows, args.output)
    missing = [row["file_name"] for row in rows if row["load_status"] != "ok"]
    print(json.dumps({"files": len(rows), "missing": missing, "output": str(args.output)}))
    if missing:
        raise SystemExit("Source inventory failed: missing expected files")


if __name__ == "__main__":
    main()
