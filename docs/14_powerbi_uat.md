# Power BI UAT

## Model checks

- curated marts only; never load raw causal_data by default;
- single-direction relationships wherever possible;
- dimension keys are unique;
- no many-to-many relationship is hidden inside a KPI;
- all measures reconcile to SQL output.

## Filter tests

- Observation Week filter;
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

Unobservable periods must be NULL in the household mart and excluded from averages.

## Reconciliation file

Store 04_qa_reports/powerbi_reconciliation.csv with:
metric, sql_value, powerbi_value, difference, tolerance, status.

Required metrics: Panel Net Spend, Baskets, Active Households, Spend per Basket, Private Label Share, Campaign Recipients, Campaign Redeemers and Redemption Rate.
