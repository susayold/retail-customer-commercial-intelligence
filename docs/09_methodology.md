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
