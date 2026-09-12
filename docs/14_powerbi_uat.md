# Power BI UAT

## Stable UAT result contract

Populate `04_qa_reports/uat_results.csv` with exactly one pass row for each stable check ID below. The release audit rejects missing, unexpected or duplicate IDs.

| ID | Area | Test | Pass evidence |
|---|---|---|---|
| UAT-01 | Data model | Dimension keys unique | `qa_key_audit.csv` |
| UAT-02 | Grain | Basket metrics are not multiplied by line joins | `qa_grain_audit.csv` |
| UAT-03 | Filters | Observation Week propagates to category/promotion weekly pages | Power BI filter evidence + semantic model |
| UAT-04 | Filters | Customer segment filter preserves curated totals | Power BI filter evidence |
| UAT-05 | Filters | Department/commodity filter preserves declared category grain | Power BI filter evidence |
| UAT-06 | Filters | Brand type filter preserves brand/private-label metrics | Power BI filter evidence |
| UAT-07 | Filters | Campaign filter preserves recipient/redeemer denominators | Power BI filter evidence + coupon exports |
| UAT-08 | Reconciliation | SQL vs Power BI core metrics are within tolerance | `powerbi_reconciliation.csv` |
| UAT-09 | Interaction | Tooltips show numerator and denominator for rates | Power BI tooltip evidence |
| UAT-10 | Interaction | Drill-through keeps declared grain | Power BI drill-through evidence + grain QA |
| UAT-11 | Censoring | Unobservable pre/during/post windows remain blank | `qa_campaign_observability.csv` |
| UAT-12 | Guardrails | Promotion/coupon states, sample sizes and disclaimers are visible | QA exports + Power BI page review |

## Model checks

- curated marts only; never load raw causal_data by default;
- single-direction relationships wherever possible;
- dimension keys are unique;
- no many-to-many relationship is hidden inside a KPI;
- all measures reconcile to SQL output.

## Filter tests

- Observation Week filter (must propagate to Mart_Category_Weekly and Mart_Promotion_Category_Week);
- customer segment filter;
- department and commodity filter;
- brand type filter;
- campaign filter;
- cross-page totals.

## Interaction tests

- tooltips show numerator/denominator where relevant;
- drill-through keeps the declared grain;
- blank pre/during/post campaign windows stay blank when unobservable;
- promotion state shows sample sizes;
- association disclaimer is visible;
- no synthetic month/seasonality claim.

## Campaign observability

Verify the four fields for every campaign:

- pre_28d_observable;
- during_observable;
- post_14d_observable;
- post_28d_observable.

A during period is observable only when the full campaign interval is covered; unobservable periods must be NULL in the household mart and excluded from averages.

## Reconciliation file

Store 04_qa_reports/powerbi_reconciliation.csv with:
metric, sql_value, powerbi_value, difference, tolerance, status.

Required metrics: Panel Net Spend, Baskets, Active Panel Households, Spend per Basket, Private Label Share, Campaign Recipients, Campaign Redeemers and Redemption Rate.
