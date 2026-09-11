# Data model

The warehouse is a small star schema designed for the dunnhumby frequent-shopper panel.

## Facts

| Table | Grain | Primary analytical use |
|---|---|---|
| fct_transaction_line | one transaction line | revenue, discount, product/category mix |
| fct_basket | one basket | trips, basket value, basket breadth |
| fct_promotion_product_store_week | one product x store x week | promotion association |
| fct_campaign_exposure | one household x campaign | exposure and observability |
| fct_coupon_redemption | one redemption event | redemption behavior |

## Dimensions

| Table | Grain | Primary key |
|---|---|---|
| dim_day | one observed day | day_key |
| dim_week | one observed week | week_number |
| dim_household | one observed household | household_key |
| dim_product | one product | product_id |
| dim_store | one observed store | store_id |
| dim_campaign | one campaign | campaign_id |
| dim_coupon | one coupon | coupon_upc |

## Bridge

bridge_coupon_product_campaign is one coupon x product x campaign row. It resolves the many-to-many path between coupon, product, and campaign without treating a coupon redemption as a product purchase.

## Join rules

- Basket metrics come from fct_basket. Never sum basket metrics after joining to fct_transaction_line.
- Product/category metrics come from fct_transaction_line joined to dim_product at line grain.
- Campaign windows join transactions by household_key and day_key; pre/during/post windows are aggregated before any redemption join.
- Redemptions join by household_key and campaign_id. They are not evidence of purchase unless the transaction data independently confirms the purchase.
- Post-period metrics are NULL when the observation window is not available; they are not interpreted as zero.

Raw CSVs, curated Parquet, DuckDB files, and BI exports remain on the private Google Drive artifact root.