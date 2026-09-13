# Executive decisions

This page converts verified findings into actions. The rows below are decision slots, not findings. Populate them only after the linked Drive output has passed QA and reconciliation.

## Decision-writing standard

Every completed row must state:

- the observed panel scope and observation window;
- the metric, numerator, denominator and grain;
- the evidence artifact and run ID;
- the operational action or test;
- the monitoring KPI and review cadence;
- the limitation that prevents overclaiming.

## Decision slots

| ID | Decision question | Evidence required | Decision rule | Action template | Monitoring KPI | Limitation |
|---|---|---|---|---|---|---|
| D01 | Which driver explains Panel Net Spend movement? | `mart_panel_weekly` + `mart_decision_alerts` + source/basket reconciliation | Select the largest reconciled accounting driver | Test re-engagement, cadence or basket-building intervention | Panel Net Spend, Active Panel Households, Trips/Household, Spend/Basket | Panel spend is frequent-shopper panel spend, not retailer revenue |
| D02 | Which high-value observed households are declining? | `mart_customer_segment` + trajectory QA | Prioritize a segment only when value and decline thresholds both pass | Create a measurable CRM re-engagement hypothesis | High-Value Declining count, spend and repeat activity | First observed purchase is not acquisition; left censoring applies |
| D03 | Which category is eroding and why? | `mart_category_household` + penetration/decomposition + basket/category QA | Require spend movement plus a supporting penetration, frequency or basket branch | Validate assortment, visibility, private-label or offer hypothesis | Category spend, buying households, penetration, frequency, spend/category basket | No market share, margin or causal assortment claim |
| D04 | Which promotion state is associated with activity? | `analysis_promotion_association` + dependency metrics + sample sizes | Use only sufficiently observed states; label association | Design a holdout/control test before claiming lift | Panel sales per product-store-week, promo-state mix, zero-sale coverage | Promotion assignment is non-random; no causal uplift claim |
| D05 | Which campaign/coupon response is strongest? | `analysis_campaign_segment` + five coupon aggregates + observability/fan-out QA | Compare rates with denominators and eligible post-period coverage | Refine targeting and coupon test design | Recipients, redeemers, redemption rate, observed repeat | Targeting bias, censoring, no campaign cost/margin/ROI |

## Completion table

| ID | Verified finding | Evidence link / run ID | Interpretation | Action owner / test | Status |
|---|---|---|---|---|---|
| D01 | pending | pending | pending | pending | waiting for real source |
| D02 | pending | pending | pending | pending | waiting for real source |
| D03 | pending | pending | pending | pending | waiting for real source |
| D04 | pending | pending | pending | pending | waiting for real source |
| D05 | pending | pending | pending | pending | waiting for real source |

No row may be marked complete from synthetic fixtures alone. The final project requires at least five evidence-backed decisions and an explicit limitation on every row.

## Verified real-data run — 2026-09-13

The five evidence-backed decisions are recorded in `04_qa_reports/executive_decisions.csv` with source run ID `run_20260913T001329Z_69411005`. They are observational decisions with explicit actions, monitoring KPIs and limitations; no causal lift, ROI or market-share claim is made.

The curated-export SQL/BI parity file contains all eight required metrics and all rows pass at tolerance `0.01`. Native Power BI visual refresh and interaction UAT remain a separate human review step.
