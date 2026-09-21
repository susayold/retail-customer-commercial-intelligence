"""Build independent SQL and curated-export metric totals for reconciliation."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import duckdb

from src.storage_paths import require_drive_path


METRICS = (
    "Panel Net Spend",
    "Baskets",
    "Active Panel Households",
    "Spend per Basket",
    "Private Label Share",
    "Campaign Recipients",
    "Campaign Redeemers",
    "Redemption Rate",
)


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def write_values(path: Path, values: list[tuple[str, float]], pipeline_run_id: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value", "pipeline_run_id"])
        writer.writerows((metric, value, pipeline_run_id) for metric, value in values)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--drive-root", type=Path, required=True)
    parser.add_argument("--pipeline-run-id", default="manual_metric_totals")
    args = parser.parse_args()

    artifact_root = require_drive_path(args.artifact_root, args.drive_root, "--artifact-root")
    database = artifact_root / "03_duckdb_and_marts" / "retail_intelligence.duckdb"
    export_root = artifact_root / "05_powerbi_exports"
    output_root = artifact_root / "04_qa_reports"
    output_root.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(database), read_only=True)
    try:
        sql_values = connection.execute(
            "SELECT metric, sql_value FROM export_powerbi_metric_reconciliation ORDER BY metric"
        ).fetchall()

        basket_path = sql_literal((export_root / "Mart_Basket.parquet").as_posix())
        panel_path = sql_literal((export_root / "Mart_Panel_Weekly.parquet").as_posix())
        campaign_path = sql_literal((export_root / "Mart_Campaign_Household.parquet").as_posix())
        bi_values = connection.execute(
            f"""
            WITH metrics AS (
                SELECT 'Panel Net Spend' AS metric, SUM(basket_net_spend) AS value
                FROM read_parquet({basket_path})
                UNION ALL
                SELECT 'Baskets', COUNT(DISTINCT basket_id)
                FROM read_parquet({basket_path})
                UNION ALL
                SELECT 'Active Panel Households', COUNT(DISTINCT household_key)
                FROM read_parquet({basket_path})
                UNION ALL
                SELECT 'Spend per Basket', SUM(basket_net_spend) / NULLIF(COUNT(DISTINCT basket_id), 0)
                FROM read_parquet({basket_path})
                UNION ALL
                SELECT 'Private Label Share', SUM(private_label_spend) / NULLIF(SUM(panel_net_spend), 0)
                FROM read_parquet({panel_path})
                UNION ALL
                SELECT 'Campaign Recipients', COUNT(DISTINCT household_key)
                FROM read_parquet({campaign_path})
                UNION ALL
                SELECT 'Campaign Redeemers', COUNT(DISTINCT CASE WHEN redeemed_coupon_flag THEN household_key END)
                FROM read_parquet({campaign_path})
                UNION ALL
                SELECT 'Redemption Rate',
                    COUNT(DISTINCT CASE WHEN redeemed_coupon_flag THEN household_key END)
                    / NULLIF(COUNT(DISTINCT household_key), 0)
                FROM read_parquet({campaign_path})
            )
            SELECT metric, value FROM metrics ORDER BY metric
            """
        ).fetchall()
    finally:
        connection.close()

    sql_metrics = {str(metric): float(value) for metric, value in sql_values}
    bi_metrics = {str(metric): float(value) for metric, value in bi_values}
    if set(sql_metrics) != set(METRICS) or set(bi_metrics) != set(METRICS):
        raise SystemExit("Metric total output does not match the eight required metrics")

    write_values(output_root / "sql_metric_totals.csv", sorted(sql_metrics.items()), args.pipeline_run_id)
    write_values(output_root / "powerbi_metric_totals.csv", sorted(bi_metrics.items()), args.pipeline_run_id)
    print(
        {
            "sql_output": str(output_root / "sql_metric_totals.csv"),
            "powerbi_output": str(output_root / "powerbi_metric_totals.csv"),
            "metrics": len(METRICS),
        }
    )


if __name__ == "__main__":
    main()
