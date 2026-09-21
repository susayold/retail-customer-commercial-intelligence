# Governed metric dictionary

Each metric has a defined population, grain, formula and limitation. All Power BI measures must reconcile to the SQL output.

| Metric | Business definition | Formula | Numerator | Denominator | Grain / filter behavior | Exclusions | Limitation |
|---|---|---|---|---|---|---|---|
| Panel Net Spend | Net observed spend in the panel | SUM sales_value | sales_value | — | transaction/basket rows in selected observation weeks | no synthetic revenue | not retailer revenue |
| Active Panel Households | Households with at least one observed basket | COUNT DISTINCT household_key | distinct active households | — | selected period; basket grain | no unobserved households | panel only |
| Baskets / Trips | Distinct observed baskets | COUNT DISTINCT basket_id | distinct baskets | — | selected period; basket grain | no line-count substitution | not store traffic |
| Spend per Basket | Net spend per observed basket | net spend / baskets | Panel Net Spend | Baskets | selected period; blank when denominator missing | no zero-fill | mix-sensitive |
| Trips per Active Household | Trips among active panel households | baskets / active households | Baskets | Active Panel Households | selected period; blank when denominator missing | no inactive panel denominator | panel denominator |
| Spend per Active Household | Net spend among active panel households | net spend / active households | Panel Net Spend | Active Panel Households | selected period; blank when denominator missing | no inactive panel denominator | panel denominator |
| Total Recorded Discount | Recorded retail + coupon + match discounts | sum absolute audited values | audited discount components | — | transaction line; source signs preserved separately | no margin inference | source discount semantics |
| Discount Rate | Recorded discount relative to descriptive gross reconstruction | discount / gross_spend_before_recorded_discounts | Total Recorded Discount | descriptive gross reconstruction | selected period; blank when denominator missing | no COGS/price elasticity | not margin |
| Category Penetration | Buying households divided by active panel households | buyers / active households | distinct category buyers | distinct active panel households | category × selected weeks; DISTINCTCOUNT, not sum of weekly buyers | no retailer-wide denominator | denominator is panel |
| Private Label Share | Observed private-label spend share | private label spend / panel net spend | private-label spend | panel net spend | category/period; anomaly flag if outside [0,1], never cap | no brand mapping invention | no margin claim |
| Campaign Redemption Rate | Recipient households with redemption | redeemers / recipients | redeemers | campaign-household exposures or unique exposed households, labelled separately | campaign; exposure and unique-HH estimands are never mixed | unobservable post-periods not zero-filled | not causal lift |
| Promotion Dependency | Share of observed activity during promoted states | promoted activity / all activity | observed promoted-state activity | observed product-store-week activity | category/period; only an observed coverage/association metric | no-promo uplift if `none` is absent | association only |

Power BI measure names must use these labels. A missing denominator returns blank, not zero. Numerators and denominators are shown for reach/redemption rates.
