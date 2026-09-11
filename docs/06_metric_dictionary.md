# Governed metric dictionary

Each metric has a defined population, grain, formula and limitation. All Power BI measures must reconcile to the SQL output.

| Metric | Business definition | Formula | Grain | Limitation |
|---|---|---|---|---|
| Panel Net Spend | Net observed spend in the panel | SUM sales_value | selected period | not retailer revenue |
| Active Panel Households | Households with at least one observed basket | COUNT DISTINCT household_key | selected period | panel only |
| Baskets / Trips | Distinct observed baskets | COUNT DISTINCT basket_id | selected period | not store traffic |
| Spend per Basket | Net spend per observed basket | net spend / baskets | selected period | mix-sensitive |
| Trips per Active Household | Trips among active panel households | baskets / active households | selected period | panel denominator |
| Spend per Active Household | Net spend among active panel households | net spend / active households | selected period | panel denominator |
| Total Recorded Discount | Recorded retail + coupon + match discounts | sum absolute audited values | selected period | source discount semantics |
| Discount Rate | Recorded discount relative to descriptive gross reconstruction | discount / gross_spend_before_recorded_discounts | selected period | not margin |
| Category Penetration | Buying households divided by active panel households | buyers / active households | category/period | denominator is panel |
| Private Label Share | Observed private-label spend share | private label spend / panel net spend | category/period | no margin claim |
| Campaign Redemption Rate | Recipient households with redemption | redeemers / recipients | campaign | not causal lift |
| Promotion Dependency | Share of observed activity during promoted states | promoted activity / all activity | category/period | association only |

Power BI measure names must use these labels. A missing denominator returns blank, not zero. Numerators and denominators are shown for reach/redemption rates.
