# Power BI delivery

Power BI is the presentation layer, not the raw 36M-row transformation engine.

## Curated inputs

Import only these Drive-backed exports from 05_powerbi_exports:

- Dim_Day, Dim_Week, Dim_Household, Dim_Product, Dim_Campaign
- Mart_Panel_Weekly, Mart_Household_Summary, Mart_Customer_Segment
- Mart_Basket, Mart_Category_Weekly, Mart_Brand_Category
- Mart_Promotion_Category_Week, Mart_Campaign_Household
- Mart_Campaign_Summary, Mart_Cross_Category_Pair, Mart_Decision_Alerts

Run the exporter after the DuckDB build:

~~~powershell
python -m src.export_powerbi --artifact-root $env:RETAIL_ARTIFACT_ROOT --format parquet
~~~

The current Drive-native Excel companion is [Retail DA - Excel Companion](https://docs.google.com/spreadsheets/d/16Iz47jiHM2nl5gGuhP5Py_xbNjLVLO5FaFpiL-_dR4k/edit).

## Semantic model

Use single-direction relationships wherever possible:

- Dim_Week[week_number] → weekly marts[week_number].
- Dim_Day[day_key] → Mart_Basket[day_key].
- Dim_Household[household_key] → Mart_Basket, Mart_Household_Summary, Mart_Customer_Segment and Mart_Campaign_Household.
- Dim_Campaign[campaign_id] → Mart_Campaign_Household and Mart_Campaign_Summary.
- Keep Mart_Basket and weekly aggregate marts as separate fact-like tables; do not relate them directly.
- Do not hide a many-to-many coupon relationship inside a KPI. Use Mart_Coupon_Summary or the documented bridge.

## Core DAX measures

~~~DAX
Panel Net Spend = SUM(Mart_Basket[basket_net_spend])
Panel Gross Spend = SUM(Mart_Basket[basket_gross_spend])
Recorded Discount = SUM(Mart_Basket[basket_discount_value])
Discount Rate = DIVIDE([Recorded Discount], [Panel Gross Spend])

Baskets = DISTINCTCOUNT(Mart_Basket[basket_id])
Active Households = DISTINCTCOUNT(Mart_Basket[household_key])
Spend per Basket = DIVIDE([Panel Net Spend], [Baskets])
Trips per Household = DIVIDE([Baskets], [Active Households])
Spend per Household = DIVIDE([Panel Net Spend], [Active Households])

Private Label Spend = SUM(Mart_Panel_Weekly[private_label_spend])
Private Label Share = DIVIDE([Private Label Spend], SUM(Mart_Panel_Weekly[panel_net_spend]))
Coupon Baskets = CALCULATE([Baskets], Mart_Basket[has_coupon_discount] = TRUE())
Coupon Basket Rate = DIVIDE([Coupon Baskets], [Baskets])

Campaign Recipients = DISTINCTCOUNT(Mart_Campaign_Household[household_key])
Campaign Redeemers = CALCULATE([Campaign Recipients], Mart_Campaign_Household[redeemed_coupon_flag] = TRUE())
Campaign Redemption Rate = DIVIDE([Campaign Redeemers], [Campaign Recipients])
~~~

## Six pages

### 1. Executive Customer & Commercial Health

Cards: Panel Net Spend, Active Households, Baskets, Spend per Basket, Trips per Household, Discount Rate and Private Label Share.

Visuals: weekly spend, active-household trend, trips and basket value, department contribution, segment contribution and the decision-alert table.

Question: what is changing, and which accounting driver explains it?

### 2. Customer Engagement & Segmentation

Show segment distribution, segment spend, segment frequency, trajectory, discount affinity and private-label affinity.

Signature use case: identify High-Value Declining observed households for a CRM hypothesis. Do not expose individual household identifiers in a public export.

### 3. Basket & Category Intelligence

Show basket value, basket line count, category penetration, category frequency, department contribution and the cross-category affinity matrix sourced from Mart_Cross_Category_Pair.

Guardrail: basket-level metrics come from Mart_Basket; line-level category metrics come from category marts.

### 4. Category, Brand & Private Label

Show category spend, household penetration, frequency, private-label share, discount rate and category decomposition. Use slicers for department, commodity and brand type.

Question: which categories are broad, deep, growing or deteriorating?

### 5. Promotion & Merchandising

Show promotion-state comparison, display exposure, mailer exposure, category response and private-vs-national response. Always display product-store-week sample sizes.

Visible disclaimer: Association, not causal lift.

### 6. Campaign & Coupon Intelligence

Show campaign reach, redemption, pre/during/post engagement, redemption by segment, coupon category and observed repurchase. Keep post-period values blank when the campaign window is not observable.

Question: which observed customer groups and campaigns show the strongest response?

## Refresh and UAT

1. Place the eight raw source CSVs in Drive 01_raw_source.
2. Run schema, inventory, profiling, Parquet, warehouse and QA commands.
3. Export marts to Drive 05_powerbi_exports.
4. Refresh the model using curated exports only.
5. Run SQL-to-DAX reconciliation using the metrics in docs/14_powerbi_uat.md.
6. Complete filter, tooltip, drill-through, blank handling, sample-size and disclaimer checks.

Store PBIX/PDF exports only in Drive 05_powerbi_exports. Until the real-data run exists, PBIX/PDF and numeric findings are intentionally not fabricated.