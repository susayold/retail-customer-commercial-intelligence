"""Export curated marts from Drive-backed DuckDB for Power BI consumption."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.storage_paths import require_drive_path
from src.utils.duckdb_client import connect


POWERBI_TABLES = (
    "dim_day",
    "dim_week",
    "dim_household",
    "dim_product",
    "dim_store",
    "dim_campaign",
    "dim_category",
    "dim_segment",
    "mart_panel_weekly",
    "mart_household_summary",
    "mart_customer_segment",
    "mart_basket",
    "mart_category_weekly",
    "mart_category_household",
    "mart_category_household_weekly",
    "mart_store_weekly",
    "analysis_category_penetration",
    "analysis_category_decomposition",
    "mart_brand_category",
    "mart_promotion_category_week",
    "analysis_promotion_association",
    "analysis_promotion_dependency",
    "analysis_promotion_universe_audit",
    "analysis_root_cause_lmdi",
    "analysis_category_materiality",
    "analysis_category_lmdi",
    "analysis_segment_stability",
    "analysis_private_label_anomalies",
    "analysis_first_observed_cohort",
    "analysis_demographic_summary",
    "analysis_executive_decisions",
    "mart_campaign_household",
    "mart_campaign_summary",
    "analysis_campaign_funnel",
    "analysis_campaign_segment",
    "analysis_campaign_denominators",
    "mart_coupon_summary",
    "analysis_coupon_campaign",
    "analysis_coupon_segment",
    "analysis_coupon_category",
    "analysis_coupon_basket",
    "analysis_coupon_repeat_category",
    "mart_cross_category_pair",
    "mart_decision_alerts",
    "export_powerbi_metric_reconciliation",
    "export_powerbi_decision_alerts",
)

# Physical filenames intentionally match the semantic-model contract and DAX names.
POWERBI_OUTPUT_NAMES = {
    "dim_day": "Dim_Day",
    "dim_week": "Dim_Week",
    "dim_household": "Dim_Household",
    "dim_product": "Dim_Product",
    "dim_store": "Dim_Store",
    "dim_campaign": "Dim_Campaign",
    "dim_category": "Dim_Category",
    "dim_segment": "Dim_Segment",
    "mart_panel_weekly": "Mart_Panel_Weekly",
    "mart_household_summary": "Mart_Household_Summary",
    "mart_customer_segment": "Mart_Customer_Segment",
    "mart_basket": "Mart_Basket",
    "mart_category_weekly": "Mart_Category_Weekly",
    "mart_category_household": "Mart_Category_Household",
    "mart_category_household_weekly": "Mart_Category_Household_Weekly",
    "mart_store_weekly": "Mart_Store_Weekly",
    "analysis_category_penetration": "Analysis_Category_Penetration",
    "analysis_category_decomposition": "Analysis_Category_Decomposition",
    "mart_brand_category": "Mart_Brand_Category",
    "mart_promotion_category_week": "Mart_Promotion_Category_Week",
    "analysis_promotion_association": "Analysis_Promotion_Association",
    "analysis_promotion_dependency": "Analysis_Promotion_Dependency",
    "analysis_promotion_universe_audit": "Analysis_Promotion_Universe_Audit",
    "analysis_root_cause_lmdi": "Analysis_Root_Cause_LMDI",
    "analysis_category_materiality": "Analysis_Category_Materiality",
    "analysis_category_lmdi": "Analysis_Category_LMDI",
    "analysis_segment_stability": "Analysis_Segment_Stability",
    "analysis_private_label_anomalies": "Analysis_Private_Label_Anomalies",
    "analysis_first_observed_cohort": "Analysis_First_Observed_Cohort",
    "analysis_demographic_summary": "Analysis_Demographic_Summary",
    "analysis_executive_decisions": "Analysis_Executive_Decisions",
    "mart_campaign_household": "Mart_Campaign_Household",
    "mart_campaign_summary": "Mart_Campaign_Summary",
    "analysis_campaign_funnel": "Analysis_Campaign_Funnel",
    "analysis_campaign_segment": "Analysis_Campaign_Segment",
    "analysis_campaign_denominators": "Analysis_Campaign_Denominators",
    "mart_coupon_summary": "Mart_Coupon_Summary",
    "analysis_coupon_campaign": "Analysis_Coupon_Campaign",
    "analysis_coupon_segment": "Analysis_Coupon_Segment",
    "analysis_coupon_category": "Analysis_Coupon_Category",
    "analysis_coupon_basket": "Analysis_Coupon_Basket",
    "analysis_coupon_repeat_category": "Analysis_Coupon_Repeat_Category",
    "mart_cross_category_pair": "Mart_Cross_Category_Pair",
    "mart_decision_alerts": "Mart_Decision_Alerts",
    "export_powerbi_metric_reconciliation": "PowerBI_Metric_Reconciliation",
    "export_powerbi_decision_alerts": "PowerBI_Decision_Alerts",
}


def sql_string_literal(value: str) -> str:
    """Quote a controlled export metadata value for DuckDB SQL."""
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--database", type=Path, default=None)
    parser.add_argument("--sql-dir", type=Path, default=Path("sql"))
    parser.add_argument("--drive-root", type=Path, required=True)
    parser.add_argument("--format", choices=("parquet", "csv"), default="parquet")
    parser.add_argument("--run-id", default="manual_export")
    args = parser.parse_args()

    artifact_root = require_drive_path(args.artifact_root, args.drive_root, "--artifact-root")
    database = (
        require_drive_path(args.database, args.drive_root, "--database")
        if args.database is not None
        else artifact_root / "03_duckdb_and_marts" / "retail_intelligence.duckdb"
    )
    output_dir = artifact_root / "05_powerbi_exports"
    output_dir.mkdir(parents=True, exist_ok=True)

    connection = connect(database, threads=2)
    try:
        export_sql_dir = args.sql_dir / "09_exports"
        for sql_path in sorted(export_sql_dir.glob("*.sql")):
            connection.execute(sql_path.read_text(encoding="utf-8"))
        for table_name in POWERBI_TABLES:
            extension = "parquet" if args.format == "parquet" else "csv"
            output_path = output_dir / f"{POWERBI_OUTPUT_NAMES[table_name]}.{extension}"
            export_query = (
                f"SELECT *, {sql_string_literal(args.run_id)} AS pipeline_run_id "
                f"FROM {table_name}"
            )
            if args.format == "parquet":
                connection.execute(
                    f"COPY ({export_query}) TO ? (FORMAT PARQUET, COMPRESSION ZSTD)",
                    [output_path.as_posix()],
                )
            else:
                connection.execute(
                    f"COPY ({export_query}) TO ? (HEADER, DELIMITER ',')",
                    [output_path.as_posix()],
                )
            print(f"wrote {output_path}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
