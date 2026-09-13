"""Run semantic checks that are independent of derived private-label marts."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import duckdb
import yaml

from src.storage_paths import require_drive_path
from src.utils.duckdb_client import register_raw_views


EXPECTED_SEGMENTS = {
    "High-Value Declining",
    "High-Value Engaged",
    "Frequent Core",
    "Promotion-Responsive",
    "Private-Label Loyal",
    "Occasional",
    "Low-Engagement",
}
SEMANTIC_TOLERANCE = 1e-9


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def normalize_brand(value: object) -> str | None:
    """Mirror the governed UPPER(TRIM()) staging rule for unit tests."""
    if value is None:
        return None
    normalized = str(value).strip().upper()
    return normalized or None


def private_label_status(
    raw_semantic_value: float,
    warehouse_value: float,
    export_value: float,
    tolerance: float = SEMANTIC_TOLERANCE,
) -> str:
    values = (raw_semantic_value, warehouse_value, export_value)
    if not all(math.isfinite(value) and value > 0 for value in values):
        return "fail"
    return "pass" if abs(raw_semantic_value - warehouse_value) <= tolerance and abs(raw_semantic_value - export_value) <= tolerance else "fail"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _threshold(path: Path) -> float:
    config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return float(config.get("segmentation", {}).get("private_label_share", 0.60))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run independent semantic QA for the corrected retail DA build.")
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--thresholds", type=Path, default=Path("config/analysis_thresholds.yaml"))
    parser.add_argument("--pipeline-run-id", required=True)
    parser.add_argument("--drive-root", type=Path, required=True)
    args = parser.parse_args()

    data_root = require_drive_path(args.data_root, args.drive_root, "--data-root")
    artifact_root = require_drive_path(args.artifact_root, args.drive_root, "--artifact-root")
    database = artifact_root / "03_duckdb_and_marts" / "retail_intelligence.duckdb"
    export_root = artifact_root / "05_powerbi_exports"
    qa_root = artifact_root / "04_qa_reports"
    panel_export = export_root / "Mart_Panel_Weekly.parquet"

    if not database.is_file() or not panel_export.is_file():
        raise SystemExit("Semantic QA requires the rebuilt DuckDB and Mart_Panel_Weekly export")

    connection = duckdb.connect(":memory:")
    try:
        database_literal = sql_literal(database.as_posix())
        connection.execute(f"ATTACH {database_literal} AS warehouse (READ_ONLY)")
        register_raw_views(connection, data_root)

        raw_private_spend, raw_panel_spend, raw_buying_households = connection.execute(
            """
            SELECT
                SUM(CASE WHEN UPPER(TRIM(CAST(p.BRAND AS VARCHAR))) = 'PRIVATE'
                         THEN CAST(t.SALES_VALUE AS DOUBLE) ELSE 0 END),
                SUM(CAST(t.SALES_VALUE AS DOUBLE)),
                COUNT(DISTINCT CASE WHEN UPPER(TRIM(CAST(p.BRAND AS VARCHAR))) = 'PRIVATE'
                                    THEN t.household_key END)
            FROM raw_transaction_data t
            INNER JOIN raw_product p
                ON CAST(t.PRODUCT_ID AS BIGINT) = CAST(p.PRODUCT_ID AS BIGINT)
            """
        ).fetchone()
        warehouse_private_spend, warehouse_panel_spend = connection.execute(
            """
            SELECT SUM(private_label_spend), SUM(panel_net_spend)
            FROM warehouse.mart_panel_weekly
            """
        ).fetchone()
        export_path = sql_literal(panel_export.as_posix())
        export_private_spend, export_panel_spend = connection.execute(
            f"SELECT SUM(private_label_spend), SUM(panel_net_spend) FROM read_parquet({export_path})"
        ).fetchone()

        raw_private_spend = float(raw_private_spend or 0)
        raw_panel_spend = float(raw_panel_spend or 0)
        warehouse_private_spend = float(warehouse_private_spend or 0)
        warehouse_panel_spend = float(warehouse_panel_spend or 0)
        export_private_spend = float(export_private_spend or 0)
        export_panel_spend = float(export_panel_spend or 0)
        raw_share = raw_private_spend / raw_panel_spend if raw_panel_spend else 0.0
        warehouse_share = warehouse_private_spend / warehouse_panel_spend if warehouse_panel_spend else 0.0
        export_share = export_private_spend / export_panel_spend if export_panel_spend else 0.0
        status = private_label_status(raw_share, warehouse_share, export_share)
        write_csv(
            qa_root / "qa_private_label_reconciliation.csv",
            [
                "metric", "raw_semantic_value", "warehouse_value", "export_value",
                "warehouse_delta", "export_delta", "tolerance", "status",
                "raw_private_label_spend", "warehouse_private_label_spend", "export_private_label_spend",
                "raw_panel_net_spend", "warehouse_panel_net_spend", "export_panel_net_spend",
                "raw_private_label_buying_households", "source_semantic_rule", "pipeline_run_id",
            ],
            [{
                "metric": "Private Label Share",
                "raw_semantic_value": raw_share,
                "warehouse_value": warehouse_share,
                "export_value": export_share,
                "warehouse_delta": abs(raw_share - warehouse_share),
                "export_delta": abs(raw_share - export_share),
                "tolerance": SEMANTIC_TOLERANCE,
                "status": status,
                "raw_private_label_spend": raw_private_spend,
                "warehouse_private_label_spend": warehouse_private_spend,
                "export_private_label_spend": export_private_spend,
                "raw_panel_net_spend": raw_panel_spend,
                "warehouse_panel_net_spend": warehouse_panel_spend,
                "export_panel_net_spend": export_panel_spend,
                "raw_private_label_buying_households": int(raw_buying_households or 0),
                "source_semantic_rule": "UPPER(TRIM(raw_product.BRAND)) = 'PRIVATE'",
                "pipeline_run_id": args.pipeline_run_id,
            }],
        )

        expected_households = 2500
        threshold = _threshold(args.thresholds.expanduser().resolve())
        segment_metrics = connection.execute(
            """
            WITH duplicate_households AS (
                SELECT household_key
                FROM warehouse.mart_customer_segment
                GROUP BY household_key
                HAVING COUNT(*) > 1
            )
            SELECT
                COUNT(*) AS row_count,
                COUNT(DISTINCT household_key) AS distinct_households,
                COUNT(*) FILTER (WHERE segment IS NULL OR TRIM(segment) = '') AS null_segments,
                (SELECT COUNT(*) FROM duplicate_households) AS duplicate_households,
                COUNT(*) FILTER (WHERE segment NOT IN (
                    'High-Value Declining', 'High-Value Engaged', 'Frequent Core',
                    'Promotion-Responsive', 'Private-Label Loyal', 'Occasional', 'Low-Engagement'
                )) AS invalid_segments
            FROM warehouse.mart_customer_segment
            """
        ).fetchone()
        check_rows = [
            ("segment_rows", expected_households, int(segment_metrics[0] or 0), int(segment_metrics[0] or 0) == expected_households),
            ("distinct_households", expected_households, int(segment_metrics[1] or 0), int(segment_metrics[1] or 0) == expected_households),
            ("null_segments", 0, int(segment_metrics[2] or 0), int(segment_metrics[2] or 0) == 0),
            ("duplicate_household_assignment", 0, int(segment_metrics[3] or 0), int(segment_metrics[3] or 0) == 0),
            ("invalid_segment_labels", 0, int(segment_metrics[4] or 0), int(segment_metrics[4] or 0) == 0),
        ]
        write_csv(
            qa_root / "qa_segment_integrity.csv",
            ["check_name", "expected_value", "actual_value", "status", "pipeline_run_id"],
            [
                {"check_name": name, "expected_value": expected, "actual_value": actual, "status": "pass" if passed else "fail", "pipeline_run_id": args.pipeline_run_id}
                for name, expected, actual, passed in check_rows
            ],
        )

        distribution = connection.execute(
            """
            SELECT
                segment,
                COUNT(*) AS households,
                COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0) AS share_of_households,
                SUM(observed_lifetime_spend) AS observed_spend,
                SUM(observed_lifetime_spend) / NULLIF(SUM(SUM(observed_lifetime_spend)) OVER (), 0) AS share_of_observed_spend,
                SUM(frequency_baskets) AS baskets,
                SUM(observed_lifetime_spend) / NULLIF(SUM(frequency_baskets), 0) AS avg_basket
            FROM warehouse.mart_customer_segment
            GROUP BY segment
            ORDER BY observed_spend DESC
            """
        ).fetchall()
        write_csv(
            qa_root / "qa_segment_distribution.csv",
            ["segment", "households", "share_of_households", "observed_spend", "share_of_observed_spend", "baskets", "avg_basket", "pipeline_run_id"],
            [dict(zip(["segment", "households", "share_of_households", "observed_spend", "share_of_observed_spend", "baskets", "avg_basket"], row), pipeline_run_id=args.pipeline_run_id) for row in distribution],
        )

        candidate_households, final_loyal_households = connection.execute(
            f"""
            SELECT
                COUNT(*) FILTER (WHERE private_label_share >= {threshold}),
                COUNT(*) FILTER (WHERE private_label_share >= {threshold} AND segment = 'Private-Label Loyal')
            FROM warehouse.mart_customer_segment
            """
        ).fetchone()
        top_categories = connection.execute(
            """
            SELECT department, commodity, private_label_spend
            FROM warehouse.analysis_private_label
            WHERE private_label_spend > 0
            ORDER BY private_label_spend DESC, department, commodity
            LIMIT 10
            """
        ).fetchall()
        top_category_text = "; ".join(
            f"{department} / {commodity} ({float(spend):.2f})"
            for department, commodity, spend in top_categories
        )
        write_csv(
            qa_root / "qa_private_label_summary.csv",
            [
                "pipeline_run_id", "panel_private_label_spend", "panel_private_label_share",
                "private_label_buying_households", "private_label_candidate_households",
                "final_private_label_loyal_households", "candidate_definition", "segment_precedence_note",
                "top_private_label_categories",
            ],
            [{
                "pipeline_run_id": args.pipeline_run_id,
                "panel_private_label_spend": warehouse_private_spend,
                "panel_private_label_share": warehouse_share,
                "private_label_buying_households": int(raw_buying_households or 0),
                "private_label_candidate_households": int(candidate_households or 0),
                "final_private_label_loyal_households": int(final_loyal_households or 0),
                "candidate_definition": f"mart_customer_segment.private_label_share >= {threshold:.2f}",
                "segment_precedence_note": "Private-Label Loyal is evaluated after higher-priority segments; candidate count may exceed final assignment count.",
                "top_private_label_categories": top_category_text,
            }],
        )
    finally:
        connection.close()

    print({
        "private_label_status": status,
        "raw_private_label_share": raw_share,
        "warehouse_private_label_share": warehouse_share,
        "export_private_label_share": export_share,
        "segment_integrity": all(item[3] for item in check_rows),
        "pipeline_run_id": args.pipeline_run_id,
    })
    if status != "pass" or not all(item[3] for item in check_rows):
        raise SystemExit("Semantic QA failed; inspect 04_qa_reports/qa_private_label_reconciliation.csv and qa_segment_integrity.csv")


if __name__ == "__main__":
    main()
