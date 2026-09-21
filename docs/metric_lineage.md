# Metric lineage

| Metric | Source path | Grain | Formula / denominator | Boundary |
|---|---|---|---|---|
| Panel Net Spend | transaction → basket → `mart_panel_weekly` | week | `SUM(basket_net_spend)` | Observed panel spend, not retailer-wide revenue |
| Baskets | transaction → `fct_basket` | basket | `COUNT(DISTINCT basket_id)` | One source basket key |
| Active Panel Households | basket → `mart_panel_weekly` | week | `COUNT(DISTINCT household_key)` | Observed active panel households |
| Private Label Share | product → brand/category mart | category/window | `private_label_spend / panel_net_spend` | Anomalies are flagged, never capped |
| Exposure Redemption Rate | campaign household mart | campaign | redeeming exposures / exposures | Exposure-level estimand |
| Unique-HH Redemption Rate | campaign household mart | campaign | unique redeemers / unique exposed HH | Distinct-HH estimand; do not combine with exposure rate |
| Category Penetration | category-household-week mart | selected weeks | distinct buying HH / distinct active HH | Never sum weekly unique households |
| Panel LMDI contribution | panel mart | first vs last window | log-mean contribution by household, trips or basket value | Associative accounting decomposition, not causal lift |

Missing denominators remain blank. Observation week is an index rather than a
calendar date. Campaign/promotion results are observational associations.
