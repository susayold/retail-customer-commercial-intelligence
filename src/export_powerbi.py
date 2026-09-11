"""Export curated marts from Drive-backed DuckDB for Power BI consumption."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.utils.duckdb_client import connect


POWERBI_TABLES = (
    "dim_day",
    "dim_week",
    "dim_household",
    "dim_product",
    "dim_campaign",
    "mart_panel_weekly",
    "mart_household_summary",
    "mart_customer_segment",
    "mart_basket",
    "mart_category_weekly",
    "mart_brand_category",
    "mart_promotion_category_week",
    "mart_campaign_household",
    "mart_campaign_summary",
    "mart_coupon_summary",
    "mart_cross_category_pair",
    "mart_decision_alerts",
    "export_powerbi_metric_reconciliation",
    "export_powerbi_decision_alerts",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--database", type=Path, default=None)
    parser.add_argument("--sql-dir", type=Path, default=Path("sql"))
    parser.add_argument("--format", choices=("parquet", "csv"), default="parquet")
    args = parser.parse_args()

    output_dir = args.artifact_root / "05_powerbi_exports"
    output_dir.mkdir(parents=True, exist_ok=True)
    database = args.database or args.artifact_root / "03_duckdb_and_marts" / "retail_intelligence.duckdb"

    connection = connect(database, threads=2)
    try:
        export_sql_dir = args.sql_dir / "09_exports"
        for sql_path in sorted(export_sql_dir.glob("*.sql")):
            connection.execute(sql_path.read_text(encoding="utf-8"))
        for table_name in POWERBI_TABLES:
            extension = "parquet" if args.format == "parquet" else "csv"
            output_path = output_dir / f"{table_name}.{extension}"
            if args.format == "parquet":
                connection.execute(
                    f"COPY (SELECT * FROM {table_name}) TO ? (FORMAT PARQUET, COMPRESSION ZSTD)",
                    [output_path.as_posix()],
                )
            else:
                connection.execute(
                    f"COPY (SELECT * FROM {table_name}) TO ? (HEADER, DELIMITER ',')",
                    [output_path.as_posix()],
                )
            print(f"wrote {output_path}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
