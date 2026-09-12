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
    "mart_category_household",
    "analysis_category_penetration",
    "analysis_category_decomposition",
    "mart_brand_category",
    "mart_promotion_category_week",
    "analysis_promotion_association",
    "analysis_promotion_dependency",
    "mart_campaign_household",
    "mart_campaign_summary",
    "analysis_campaign_funnel",
    "analysis_campaign_segment",
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
    "dim_campaign": "Dim_Campaign",
    "mart_panel_weekly": "Mart_Panel_Weekly",
    "mart_household_summary": "Mart_Household_Summary",
    "mart_customer_segment": "Mart_Customer_Segment",
    "mart_basket": "Mart_Basket",
    "mart_category_weekly": "Mart_Category_Weekly",
    "mart_category_household": "Mart_Category_Household",
    "analysis_category_penetration": "Analysis_Category_Penetration",
    "analysis_category_decomposition": "Analysis_Category_Decomposition",
    "mart_brand_category": "Mart_Brand_Category",
    "mart_promotion_category_week": "Mart_Promotion_Category_Week",
    "analysis_promotion_association": "Analysis_Promotion_Association",
    "analysis_promotion_dependency": "Analysis_Promotion_Dependency",
    "mart_campaign_household": "Mart_Campaign_Household",
    "mart_campaign_summary": "Mart_Campaign_Summary",
    "analysis_campaign_funnel": "Analysis_Campaign_Funnel",
    "analysis_campaign_segment": "Analysis_Campaign_Segment",
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
            output_path = output_dir / f"{POWERBI_OUTPUT_NAMES[table_name]}.{extension}"
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
