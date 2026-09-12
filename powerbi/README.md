# Power BI delivery

The data-free semantic contract is versioned in [`semantic_model.yaml`](semantic_model.yaml), and the governed measure definitions are versioned in [`measures.dax`](measures.dax). These files are reviewable before a real-data refresh; PBIX/PDF remain Drive-only outputs after the source run.

Power BI is the presentation layer, not the raw 36M-row transformation engine.

## Curated inputs

Import only these Drive-backed exports from 05_powerbi_exports:

- Dim_Day, Dim_Week, Dim_Household, Dim_Product, Dim_Campaign
- Mart_Panel_Weekly, Mart_Household_Summary, Mart_Customer_Segment
- Mart_Basket, Mart_Category_Weekly, Mart_Category_Household
- Analysis_Category_Penetration, Analysis_Category_Decomposition
- Mart_Brand_Category, Mart_Promotion_Category_Week
- Analysis_Promotion_Association, Analysis_Promotion_Dependency
- Mart_Campaign_Household, Mart_Campaign_Summary
- Analysis_Campaign_Funnel, Analysis_Campaign_Segment, Mart_Coupon_Summary
- Analysis_Coupon_Campaign, Analysis_Coupon_Segment, Analysis_Coupon_Category
- Analysis_Coupon_Basket, Analysis_Coupon_Repeat_Category
- Mart_Cross_Category_Pair, Mart_Decision_Alerts

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
- Dim_Campaign[campaign_id] → Mart_Campaign_Household, Mart_Campaign_Summary, Analysis_Campaign_Funnel, Analysis_Campaign_Segment, Mart_Coupon_Summary and coupon analysis aggregates.
- Category penetration/decomposition and promotion association/dependency are pre-aggregated analysis tables; keep their declared category/promo-state grain and do not relate them directly to transaction-line facts.
- Keep Mart_Basket and weekly aggregate marts as separate fact-like tables; do not relate them directly.
- Coupon category analysis is linked through campaign and keeps the many-to-many bridge logic in SQL; do not flatten the bridge into household exposure.
- Do not hide a many-to-many coupon relationship inside a KPI.

## Core DAX measures

~~~DAX
Panel Net Spend = SUM(Mart_Basket[basket_net_spend])
Panel Gross Spend = SUM(Mart_Basket[basket_gross_spend])
Total Recorded Discount = SUM(Mart_Basket[basket_discount_value])
Discount Rate = DIVIDE([Total Recorded Discount], [Panel Gross Spend])

Baskets = DISTINCTCOUNT(Mart_Basket[basket_id])
Active Panel Households = DISTINCTCOUNT(Mart_Basket[household_key])
Spend per Basket = DIVIDE([Panel Net Spend], [Baskets])
Trips per Active Household = DIVIDE([Baskets], [Active Panel Households])
Spend per Active Household = DIVIDE([Panel Net Spend], [Active Panel Households])

Private Label Spend = SUM(Mart_Panel_Weekly[private_label_spend])
Private Label Share = DIVIDE([Private Label Spend], SUM(Mart_Panel_Weekly[panel_net_spend]))
Coupon Baskets = CALCULATE([Baskets], Mart_Basket[has_coupon_discount] = TRUE())
Coupon Basket Rate = DIVIDE([Coupon Baskets], [Baskets])

Campaign Recipients = DISTINCTCOUNT(Mart_Campaign_Household[household_key])
Campaign Redeemers = CALCULATE([Campaign Recipients], Mart_Campaign_Household[redeemed_coupon_flag] = TRUE())
Campaign Redemption Rate = DIVIDE([Campaign Redeemers], [Campaign Recipients])
Coupon Linked Products = SUM(Analysis_Coupon_Campaign[linked_products])
