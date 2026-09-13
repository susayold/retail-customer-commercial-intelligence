# Executive decisions

This page converts verified findings into actions. All five rows below come from the corrected Drive-backed non-native rebuild and remain scoped to observed panel behavior.

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
| D01 | Trips per Active Household is the largest reconciled driver in the first-versus-last 13-week comparison; panel spend increased 208.58%. | `root_cause_cases.csv`, `da_no_native_20260913T213859Z_341c1744` | Accounting decomposition, not causal attribution. | CRM/commercial analytics — test a driver-aligned re-engagement or cadence intervention with holdout. | Panel Net Spend, active households, trips/household, spend/basket | Frequent-shopper panel only. |
| D02 | High-Value Declining contains 221 observed households and $1,277,884.99 lifetime panel spend. | `Mart_Customer_Segment.parquet`, `da_no_native_20260913T213859Z_341c1744` | Value and trajectory thresholds both pass. | CRM — prioritize a measurable re-engagement hypothesis. | Segment count, spend, repeat activity, reactivation rate | First observed purchase is not acquisition. |
| D03 | DRUG GM / LAWN AND GARDEN SHOP shows the largest observed erosion at -99.58% spend. | `Analysis_Category_Decomposition.parquet`, `da_no_native_20260913T213859Z_341c1744` | Supporting buyer and basket movement is visible. | Category/commercial — validate assortment, visibility, private-label and offer hypotheses. | Category spend, buyers, penetration, frequency, spend/basket | No market-share, margin or causal assortment claim. |
| D04 | display_and_mailer has the highest observed panel sales per product-store-week at $0.08 across 4,213,655 product-store-weeks. | `Analysis_Promotion_Association.parquet`, `da_no_native_20260913T213859Z_341c1744` | Association with promotional state. | Merchandising — design a holdout/control test before lift claims. | Sales per product-store-week, promo mix, zero-sale coverage | Promotion assignment is non-random. |
| D05 | Campaign 18 (TypeA) is strongest among campaigns with at least 50 recipients: 214/1,133 = 18.89%. | `Analysis_Campaign_Funnel.parquet`, `da_no_native_20260913T213859Z_341c1744` | Observed response with explicit denominator. | CRM/campaigns — refine targeting and validate with a pre-specified holdout. | Recipients, redeemers, redemption, repeat rate | Targeting bias, censoring and missing cost/margin. |

No row may be marked complete from synthetic fixtures alone. The final project requires at least five evidence-backed decisions and an explicit limitation on every row.

## Verified real-data run — 2026-09-13

The five evidence-backed decisions are recorded in `04_qa_reports/executive_decisions.csv` with pipeline run ID `da_no_native_20260913T213859Z_341c1744`. They are observational decisions with explicit actions, monitoring KPIs and limitations; no causal lift, ROI or market-share claim is made.

The curated-export SQL/BI parity file contains all eight required metrics and all rows pass at tolerance `0.01`. Native Power BI visual refresh and interaction UAT remain a separate human review step.
