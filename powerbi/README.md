# Power BI delivery

Power BI is the presentation layer, not the raw 36M-row transformation engine.

## Import these curated models

Dim_Day, Dim_Week, Dim_Household, Dim_Product, Dim_Campaign, Mart_Panel_Weekly, Mart_Household_Summary, Mart_Customer_Segment, Mart_Basket, Mart_Category_Weekly, Mart_Brand_Category, Mart_Promotion_Category_Week, Mart_Campaign_Household, Mart_Campaign_Summary, Mart_Cross_Category_Pair and Mart_Decision_Alerts.

## Six pages

1. Executive Customer & Commercial Health.
2. Customer Engagement & Segmentation.
3. Basket & Category Intelligence.
4. Category, Brand & Private Label.
5. Promotion & Merchandising.
6. Campaign & Coupon Intelligence.

## Core DAX measures

~~~DAX
Panel Net Spend = SUM(Mart_Basket[basket_net_spend])
Baskets = DISTINCTCOUNT(Mart_Basket[basket_id])
Active Households = DISTINCTCOUNT(Mart_Basket[household_key])
Spend per Basket = DIVIDE([Panel Net Spend], [Baskets])
Trips per Household = DIVIDE([Baskets], [Active Households])
Spend per Household = DIVIDE([Panel Net Spend], [Active Households])
Campaign Recipients = DISTINCTCOUNT(Mart_Campaign_Household[household_key])
Campaign Redeemers = CALCULATE([Campaign Recipients], Mart_Campaign_Household[redeemed_coupon_flag] = TRUE())
Campaign Redemption Rate = DIVIDE([Campaign Redeemers], [Campaign Recipients])
~~~

Store PBIX and PDF exports only in Drive 05_powerbi_exports. Reconcile SQL/DAX before sharing.
