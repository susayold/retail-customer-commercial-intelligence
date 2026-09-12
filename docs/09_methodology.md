# Methodology

## Analytical sequence

1. Inventory and schema validation.
2. Profile nulls, cardinality, ranges, duplicate keys and unexpected values.
3. Register raw views and convert CSV to Parquet in Drive.
4. Build staging with explicit casts and derived fields.
5. Build dimensions, facts and the coupon bridge at declared grains.
6. Reconcile raw/staging/fact rows and key populations.
7. Build governed metrics and marts.
8. Diagnose spend using the accounting identity:
   Panel Spend = Active Households × Trips per Active Household × Spend per Basket.
9. Segment observed households with deterministic, explainable rules.
10. Analyze baskets, categories, brands and private label.
11. Build a product-store-week promotion skeleton so zero-sale weeks remain visible.
12. Analyze campaign recipients, redemption and observable pre/during/post behavior.
13. Validate selected differences with confidence intervals/effect sizes where useful.
14. Write root-cause cases and decision recommendations.
15. Export curated BI marts, reconcile SQL/DAX and complete UAT.

## Statistical guardrails

Use bootstrap or proportion confidence intervals, Mann–Whitney/Kruskal–Wallis, chi-square or matched observational comparisons only when they answer a business question. Report sample size, magnitude, uncertainty and limitation together. Never use a p-value as the business result.

## Causal language

The data is observational. Promotion and campaign recipients may be selected. Use associated with, observed response, descriptive difference and matched observational comparison. Do not write causal lift or ROI without verified experimental/cost data.

## Category household and penetration

`mart_category_household` is one row per observed household × department × commodity. It supports distinct buying households, household penetration against all observed panel households, category baskets, purchase frequency, spend per buying household, coupon-basket rate and private-label share without summing household-week records as if they were unique buyers.

`analysis_category_decomposition` compares early and late observation windows using distinct buyers and category baskets. The decomposition separates changes in buyers, baskets per buying household and spend per category basket. Early/late labels use observation weeks, not real calendar seasonality.

## Promotion dependency

Promotion dependency is reported by department and commodity as two descriptive shares:

- observed panel sales occurring in display/mailer-supported states divided by total observed panel sales;
- product-store-weeks in display/mailer-supported states divided by all product-store-weeks.

The promotion mart is built from the product-store-week skeleton, so zero-sale weeks remain in the denominator. These measures describe association and support commercial monitoring; they do not imply causal lift, profitability or ROI.

## Campaign response by segment

`analysis_campaign_segment` preserves the campaign funnel at campaign × campaign type × observed customer segment. It reports recipient and redeemer household denominators, redemption rate, pre/during/post observable row counts, and demographic coverage. Unobservable windows remain excluded from averages, and the output is interpreted as observed response rather than causal campaign lift.

## Coupon analytics

Coupon analysis keeps separate grains for campaign funnel, customer segment, coupon-category mapping, observed basket behavior and repeat-category behavior:

- `analysis_coupon_campaign` reports campaign reach, redemption, linked coupon count and linked product count.
- `analysis_coupon_segment` reports recipient and redeemer denominators by observed customer segment.
- `analysis_coupon_category` attributes redemption events to linked departments/commodities with distinct event counts; because the bridge is many-to-many, category event counts are intentionally non-additive across categories.
- `analysis_coupon_basket` compares coupon-discounted and non-coupon-discounted observed baskets without claiming exact redemption-to-basket attribution.
- `analysis_coupon_repeat_category` starts from the first observed coupon-discounted category purchase and checks for a later observed purchase in that category. It is not true acquisition, true first-ever purchase or causal repeat.
