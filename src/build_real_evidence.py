"""Materialize real-data findings and decision evidence from the Drive-backed mart."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import duckdb

from src.storage_paths import require_drive_path


DRIVE_QA = "https://drive.google.com/drive/folders/15YAb2Jr_H-P0sEs9j6P_Im69XxtqjwzU"


def money(value: float) -> str:
    return f"${value:,.2f}"


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--drive-root", type=Path, required=True)
    args = parser.parse_args()

    artifact_root = require_drive_path(args.artifact_root, args.drive_root, "--artifact-root")
    database = artifact_root / "03_duckdb_and_marts" / "retail_intelligence.duckdb"
    qa_root = artifact_root / "04_qa_reports"
    qa_root.mkdir(parents=True, exist_ok=True)
    source_ready = json.loads(
        (artifact_root / "06_source_docs" / "source_ready.json").read_text(encoding="utf-8")
    )
    run_id = str(source_ready["run_id"])

    connection = duckdb.connect(str(database), read_only=True)
    try:
        window_rows = connection.execute(
            """
            WITH bounds AS (
                SELECT MIN(week_number) AS min_week, MAX(week_number) AS max_week
                FROM mart_panel_weekly
            )
            SELECT
                CASE
                    WHEN b.week_number <= x.min_week + 13 - 1 THEN 'Baseline (first 13 weeks)'
                    ELSE 'Current (last 13 weeks)'
                END AS period,
                SUM(b.basket_net_spend) AS panel_net_spend,
                COUNT(DISTINCT b.household_key) AS active_households,
                COUNT(DISTINCT b.basket_id) AS baskets
            FROM mart_basket b
            CROSS JOIN bounds x
            WHERE b.week_number <= x.min_week + 13 - 1
               OR b.week_number > x.max_week - 13
            GROUP BY 1
            ORDER BY 1
            """
        ).fetchall()
        windows = {str(row[0]): row for row in window_rows}
        baseline = windows["Baseline (first 13 weeks)"]
        current = windows["Current (last 13 weeks)"]
        b_spend, b_households, b_baskets = map(float, baseline[1:])
        c_spend, c_households, c_baskets = map(float, current[1:])
        b_trips = b_baskets / b_households
        c_trips = c_baskets / c_households
        b_basket_value = b_spend / b_baskets
        c_basket_value = c_spend / c_baskets
        driver_changes = {
            "Active Panel Households": c_households / b_households - 1,
            "Trips per Active Household": c_trips / b_trips - 1,
            "Spend per Basket": c_basket_value / b_basket_value - 1,
        }
        primary_driver = max(driver_changes, key=lambda name: abs(driver_changes[name]))

        category = connection.execute(
            """
            SELECT *, spend_change / NULLIF(early_spend, 0) AS spend_change_pct
            FROM analysis_category_decomposition
            WHERE early_spend > 0 AND late_spend IS NOT NULL
            ORDER BY spend_change_pct ASC
            LIMIT 1
            """
        ).fetchone()
        category_columns = [
            row[0] for row in connection.execute("DESCRIBE analysis_category_decomposition").fetchall()
        ] + ["spend_change_pct"]
        category_values = dict(zip(category_columns, category))

        weakest_campaign = connection.execute(
            """
            SELECT campaign_id, campaign_type, campaign_recipients,
                   campaign_redeemers, campaign_redemption_rate,
                   post_28d_observable_rows
            FROM analysis_campaign_funnel
            WHERE campaign_recipients >= 50
            ORDER BY campaign_redemption_rate ASC, campaign_id
            LIMIT 1
            """
        ).fetchone()
        strongest_campaign = connection.execute(
            """
            SELECT campaign_id, campaign_type, campaign_recipients,
                   campaign_redeemers, campaign_redemption_rate,
                   post_28d_observable_rows
            FROM analysis_campaign_funnel
            WHERE campaign_recipients >= 50
            ORDER BY campaign_redemption_rate DESC, campaign_id
            LIMIT 1
            """
        ).fetchone()
        segment_rows = connection.execute(
            """
            SELECT segment, COUNT(*) AS households, SUM(observed_lifetime_spend) AS spend,
                   COUNT(*) FILTER (WHERE trajectory = 'Declining') AS declining_households
            FROM mart_customer_segment
            GROUP BY segment
            ORDER BY spend DESC
            """
        ).fetchall()
        segment_columns = ["segment", "households", "spend", "declining_households"]
        segment_map = {str(row[0]): dict(zip(segment_columns, row)) for row in segment_rows}
        high_value_declining = segment_map.get(
            "High-Value Declining",
            {"households": 0, "spend": 0.0, "declining_households": 0},
        )
        promo = connection.execute(
            """
            SELECT promo_state_group,
                   SUM(product_store_weeks) AS product_store_weeks,
                   SUM(panel_sales) AS panel_sales,
                   SUM(panel_sales) / NULLIF(SUM(product_store_weeks), 0) AS sales_per_product_store_week
            FROM mart_promotion_category_week
            GROUP BY promo_state_group
            ORDER BY sales_per_product_store_week DESC
            """
        ).fetchall()
        promo_columns = ["promo_state_group", "product_store_weeks", "panel_sales", "sales_per_product_store_week"]
        best_promo = dict(zip(promo_columns, promo[0]))
    finally:
        connection.close()

    case_rows = [
        {
            "case_id": "A",
            "status": "complete",
            "evidence_uri": DRIVE_QA,
            "evidence_file": "qa_layer_reconciliation.csv; Mart_Panel_Weekly.parquet; Mart_Basket.parquet",
            "run_id": run_id,
            "scope": "Observed panel; first 13 weeks versus last 13 weeks",
            "grain": "basket_id for driver identity; week_number for weekly context",
            "finding": (
                f"No decline was observed in the selected windows: Panel Net Spend changed from {money(b_spend)} to {money(c_spend)} "
                f"({pct(c_spend / b_spend - 1)}). Largest reconciled driver movement: "
                f"{primary_driver} ({pct(driver_changes[primary_driver])})."
            ),
            "action": "Validate whether the observed panel movement is broad-based, then design a measurable driver-aligned test.",
            "monitoring_kpi": "Panel Net Spend; Active Panel Households; Trips per Active Household; Spend per Basket",
            "limitation": "Panel spend is frequent-shopper panel spend; this is accounting decomposition, not causal attribution.",
        },
        {
            "case_id": "B",
            "status": "complete",
            "evidence_uri": DRIVE_QA,
            "evidence_file": "Analysis_Category_Decomposition.parquet; Mart_Category_Weekly.parquet",
            "run_id": run_id,
            "scope": "All observed categories; first 13 weeks versus last 13 weeks",
            "grain": "department × commodity category",
            "finding": (
                f"Largest relative observed category erosion: {category_values['department']} / "
                f"{category_values['commodity']}, spend change {pct(float(category_values['spend_change_pct']))}; "
                f"buying households changed by {int(category_values['buying_household_change']):,} and "
                f"category baskets changed by {int(category_values['basket_change']):,}."
            ),
            "action": "Validate assortment, visibility, private-label and offer hypotheses with a controlled category test.",
            "monitoring_kpi": "Category spend; buying households; penetration; baskets per buying household; spend per category basket",
            "limitation": "This is within-panel observed erosion; no market share, margin or causal assortment claim.",
        },
        {
            "case_id": "C",
            "status": "complete",
            "evidence_uri": DRIVE_QA,
            "evidence_file": "Analysis_Campaign_Funnel.parquet; Analysis_Campaign_Segment.parquet; qa_campaign_observability.csv",
            "run_id": run_id,
            "scope": "Campaign recipients with at least 50 exposed panel households",
            "grain": "campaign_id and recipient household; rates use exposed households as denominator",
            "finding": (
                f"Weakest observed campaign response is campaign {int(weakest_campaign[0])} "
                f"({weakest_campaign[1]}): {int(weakest_campaign[3]):,} redeemers / "
                f"{int(weakest_campaign[2]):,} recipients = {pct(float(weakest_campaign[4]))}; "
                f"post-28d observable rows={int(weakest_campaign[5]):,}."
            ),
            "action": "Refine targeting and coupon mechanics, then run a pre-specified holdout/control test.",
            "monitoring_kpi": "Recipients; redeemers; redemption rate; observable post-period repeat rate",
            "limitation": "Recipients may be targeted; post-period censoring, cost and margin are unavailable, so no causal lift or ROI claim.",
        },
    ]
    write_csv(
        qa_root / "root_cause_cases.csv",
        list(case_rows[0].keys()),
        case_rows,
    )

    decision_rows = [
        {
            "decision_id": "D01",
            "status": "complete",
            "evidence_uri": DRIVE_QA,
            "evidence_file": "root_cause_cases.csv; Mart_Panel_Weekly.parquet; qa_layer_reconciliation.csv",
            "run_id": run_id,
            "verified_finding": f"Primary driver in the selected 13-week comparison is {primary_driver}; panel spend moved {pct(c_spend / b_spend - 1)}.",
            "action_owner_test": "CRM/commercial analytics: test the driver-aligned intervention with a holdout.",
            "monitoring_kpi": "Panel Net Spend, Active Panel Households, Trips/Household, Spend/Basket",
            "limitation": "Frequent-shopper panel only; decomposition does not establish causality.",
        },
        {
            "decision_id": "D02",
            "status": "complete",
            "evidence_uri": DRIVE_QA,
            "evidence_file": "Mart_Customer_Segment.parquet; stats_basket_by_segment.csv",
            "run_id": run_id,
            "verified_finding": f"High-Value Declining segment contains {int(high_value_declining['households']):,} observed households and {money(float(high_value_declining['spend']))} lifetime panel spend.",
            "action_owner_test": "CRM: prioritize a measurable re-engagement hypothesis for this segment.",
            "monitoring_kpi": "High-Value Declining count, spend, repeat activity and reactivation rate",
            "limitation": "First observed purchase is not acquisition; left censoring applies.",
        },
        {
            "decision_id": "D03",
            "status": "complete",
            "evidence_uri": DRIVE_QA,
            "evidence_file": "Analysis_Category_Decomposition.parquet; Analysis_Category_Penetration.parquet",
            "run_id": run_id,
            "verified_finding": f"Priority observed erosion category is {category_values['department']} / {category_values['commodity']} at {pct(float(category_values['spend_change_pct']))} spend change.",
            "action_owner_test": "Category/commercial: validate assortment, visibility, private-label and offer hypotheses.",
            "monitoring_kpi": "Category spend, buying households, penetration, frequency and spend/category basket",
            "limitation": "Within-panel category observation; no market share, margin or causal assortment claim.",
        },
        {
            "decision_id": "D04",
            "status": "complete",
            "evidence_uri": DRIVE_QA,
            "evidence_file": "Analysis_Promotion_Association.parquet; Analysis_Promotion_Dependency.parquet; stats_promotion_state.csv",
            "run_id": run_id,
            "verified_finding": f"Highest observed panel sales per product-store-week is associated with promo state {best_promo['promo_state_group']} at {money(float(best_promo['sales_per_product_store_week']))}; sample={int(best_promo['product_store_weeks']):,} product-store-weeks.",
            "action_owner_test": "Merchandising: design a holdout/control test before any lift claim.",
            "monitoring_kpi": "Panel sales per product-store-week, promo-state mix and zero-sale coverage",
            "limitation": "Promotion assignment is non-random; association is not causal uplift.",
        },
        {
            "decision_id": "D05",
            "status": "complete",
            "evidence_uri": DRIVE_QA,
            "evidence_file": "Analysis_Campaign_Funnel.parquet; Analysis_Coupon_Campaign.parquet; qa_campaign_observability.csv",
            "run_id": run_id,
            "verified_finding": f"Strongest observed campaign response among campaigns with at least 50 recipients is campaign {int(strongest_campaign[0])} ({strongest_campaign[1]}): {int(strongest_campaign[3]):,}/{int(strongest_campaign[2]):,} = {pct(float(strongest_campaign[4]))}.",
            "action_owner_test": "CRM/campaigns: refine targeting and validate with a pre-specified holdout.",
            "monitoring_kpi": "Recipients, redeemers, redemption rate and observable repeat rate",
            "limitation": "Targeting bias, censoring and missing cost/margin prevent causal lift and ROI claims.",
        },
    ]
    write_csv(
        qa_root / "executive_decisions.csv",
        list(decision_rows[0].keys()),
        decision_rows,
    )

    write_csv(
        qa_root / "real_data_findings.csv",
        ["finding", "value", "run_id", "limitation"],
        [
            {"finding": "baseline_panel_net_spend", "value": b_spend, "run_id": run_id, "limitation": "Observed panel window"},
            {"finding": "current_panel_net_spend", "value": c_spend, "run_id": run_id, "limitation": "Observed panel window"},
            {"finding": "primary_driver", "value": primary_driver, "run_id": run_id, "limitation": "Accounting decomposition"},
            {"finding": "priority_category", "value": f"{category_values['department']} / {category_values['commodity']}", "run_id": run_id, "limitation": "Within-panel observation"},
            {"finding": "weakest_campaign", "value": int(weakest_campaign[0]), "run_id": run_id, "limitation": "Targeting/censoring"},
            {"finding": "strongest_campaign", "value": int(strongest_campaign[0]), "run_id": run_id, "limitation": "Targeting/censoring"},
        ],
    )
    print({"root_cause_cases": len(case_rows), "executive_decisions": len(decision_rows), "run_id": run_id})


if __name__ == "__main__":
    main()
