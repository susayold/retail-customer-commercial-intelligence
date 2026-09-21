# Metric lineage

| Metric | Source path | Formula | Grain | Boundary |
|---|---|---|---|---|
| Panel Net Spend | `SALES_VALUE → fct_transaction_line → fct_basket → mart_panel_weekly` | `SUM(sales_value)` | selected observation week/period | observed panel spend, not retailer revenue |
| Baskets | `BASKET_ID → fct_basket` | `COUNT(DISTINCT basket_id)` | selected period | basket grain is audited for household/day/store consistency |
| Active Panel Households | `household_key → fct_basket → mart_panel_weekly` | distinct households with at least one basket | selected period | frequent-shopper panel only |
| Trips per Active Household | panel weekly | `baskets / active_panel_households` | selected period | denominator is selected-period active households |
| Spend per Basket | panel weekly | `panel_net_spend / baskets` | selected period | basket value is a proxy based on recorded sales |
| Category Household Penetration | `mart_category_household_weekly` | distinct buying households in selected weeks / distinct active households in selected weeks | category + selected period | never sum weekly unique-household counts |
| Private Label Share | `fct_transaction_line + dim_product` | private-label spend / panel net spend | selected period/category | mapping and negative-value anomalies remain visible |
| Exposure Redemption Rate | `mart_campaign_household` | redeeming campaign-household exposures / campaign-household exposures | campaign | not the unique-household rate |
| Unique-HH Redemption Rate | `mart_campaign_household` | unique redeeming households / unique exposed households | campaign | targeting and censoring apply |
| Panel Spend Driver Contribution | `mart_panel_weekly → analysis_root_cause_lmdi` | LMDI contribution of households, trips or basket value | first vs last observation window | accounting decomposition, not causal lift |

Each metric must answer: source, grain, formula, denominator, filter behavior and limitation. Power BI consumes the governed Parquet exports rather than rebuilding these definitions in visuals.
