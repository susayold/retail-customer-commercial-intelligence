"""Audit whether the raw promotion universe supports a valid no-promotion state."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from src.storage_paths import require_drive_path
from src.utils.duckdb_client import connect


def _write_csv(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def audit(database: Path, data_root: Path, artifact_root: Path, run_id: str) -> dict[str, object]:
    causal_path = data_root / "causal_data.csv"
    connection = connect(database, read_only=True)
    try:
        modeled = connection.execute(
            """
            SELECT
                COUNT(*) AS total_rows,
                COUNT(*) FILTER (WHERE promo_state_group = 'display_only') AS display_only_rows,
                COUNT(*) FILTER (WHERE promo_state_group = 'mailer_only') AS mailer_only_rows,
                COUNT(*) FILTER (WHERE promo_state_group = 'display_and_mailer') AS display_and_mailer_rows,
                COUNT(*) FILTER (WHERE promo_state_group = 'none') AS none_rows,
                COUNT(DISTINCT product_id) AS products,
                COUNT(DISTINCT store_id) AS stores,
                COUNT(DISTINCT week_number) AS weeks
            FROM fct_promotion_product_store_week
            """
        ).fetchone()
    finally:
        connection.close()

    raw = duckdb.connect(":memory:")
    try:
        raw_row = raw.execute(
            """
            SELECT
                COUNT(*) AS raw_total_rows,
                COUNT(*) FILTER (WHERE CAST(display AS VARCHAR) = '0' AND CAST(mailer AS VARCHAR) = '0') AS raw_zero_zero_rows,
                COUNT(DISTINCT CASE WHEN CAST(display AS VARCHAR) = '0' AND CAST(mailer AS VARCHAR) = '0'
                    THEN CONCAT(CAST(PRODUCT_ID AS VARCHAR), '|', CAST(STORE_ID AS VARCHAR), '|', CAST(WEEK_NO AS VARCHAR)) END) AS raw_zero_zero_keys
            FROM read_csv_auto(?, header=true, union_by_name=true)
            """,
            [causal_path.as_posix()],
        ).fetchone()
    finally:
        raw.close()

    raw_total, raw_zero_zero, raw_zero_zero_keys = int(raw_row[0]), int(raw_row[1]), int(raw_row[2])
    total_rows, display_only, mailer_only, display_and_mailer, none_rows, products, stores, weeks = map(int, modeled)
    if none_rows > 0:
        recovery_case = "RECOVERED_MODELED_NONE"
        valid_none_for_uplift = True
    elif raw_zero_zero == 0:
        recovery_case = "CASE_A_RAW_PROMOTED_ROWS_ONLY"
        valid_none_for_uplift = False
    else:
        recovery_case = "CASE_B_RAW_ZERO_ZERO_NOT_RETAINED"
        valid_none_for_uplift = False
    row = {
        "run_id": run_id,
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "raw_total_rows": raw_total,
        "raw_zero_zero_rows": raw_zero_zero,
        "raw_zero_zero_keys": raw_zero_zero_keys,
        "total_rows": total_rows,
        "display_only_rows": display_only,
        "mailer_only_rows": mailer_only,
        "display_and_mailer_rows": display_and_mailer,
        "none_rows": none_rows,
        "products": products,
        "stores": stores,
        "weeks": weeks,
        "none_state_status": "RECOVERED" if none_rows > 0 else "NOT_OBSERVED",
        "recovery_case": recovery_case,
        "valid_none_for_uplift": valid_none_for_uplift,
        "interpretation_boundary": "Promotion comparisons are observational; raw 0/0 rows are a valid none candidate only when retained at product-store-week grain; no valid none state means no uplift/dependency-vs-no-promo claim.",
    }
    qa_root = artifact_root / "04_qa_reports"
    _write_csv(qa_root / "qa_promotion_universe.csv", row)
    (qa_root / "qa_promotion_universe.json").write_text(
        json.dumps(row, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--drive-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    database = require_drive_path(args.database, args.drive_root, "--database")
    data_root = require_drive_path(args.data_root, args.drive_root, "--data-root")
    artifact_root = require_drive_path(args.artifact_root, args.drive_root, "--artifact-root")
    result = audit(database, data_root, artifact_root, args.run_id)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
