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

# Planning expectations from the supplied blueprint; differences require review,
# not automatic rejection, because permitted source versions may vary.
EXPECTED_ROW_COUNTS = {
    "transaction_data.csv": 2_595_732,
    "causal_data.csv": 36_786_524,
    "coupon.csv": 124_548,
    "coupon_redempt.csv": 2_318,
    "campaign_table.csv": 7_208,
    "campaign_desc.csv": 30,
    "product.csv": 92_353,
    "hh_demographic.csv": 801,
}


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
    row_count_delta = (
        rows - expected_row_count
        if expected_row_count is not None
        else None
    )
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
        "row_count": rows,
        "expected_row_count": expected_row_count,
        "row_count_delta": row_count_delta,
        "planning_expectation_status": planning_expectation_status,
        "column_count": len(header),
        "column_names_hash": column_hash(header),
        "content_sha256": content_hash(path),
        "load_status": "ok",
    }


def inventory(input_dir: Path) -> list[dict[str, object]]:
    rows = []
    for name in EXPECTED_FILES:
        path = input_dir / name
        if path.exists():
            rows.append(inspect_csv(path, EXPECTED_ROW_COUNTS.get(name)))
        else:
            rows.append({
                "file_name": name,
                "file_size_bytes": None,
                "row_count": None,
                "expected_row_count": EXPECTED_ROW_COUNTS.get(name),
                "row_count_delta": None,
                "planning_expectation_status": "missing",
                "column_count": None,
                "column_names_hash": None,
                "content_sha256": None,
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
