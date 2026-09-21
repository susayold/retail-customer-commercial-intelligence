# Data dictionary

This dictionary distinguishes raw fields from curated fields. Raw source names are preserved alongside normalized names in staging.

| Field | Type | Nullable | Source | Meaning | Grain notes | Caveat |
|---|---|---|---|---|---|---|
| household_key | integer | No in transaction/exposure | transaction/demographic/campaign | panel household identifier | household; fact foreign key | panel only |
| BASKET_ID | string | No | transaction | shopping trip/basket identifier | one fct_basket row | count distinct baskets |
| DAY | integer | No | transaction/campaign | observation day index | day dimension key | not a calendar date |
| WEEK_NO | integer | No | transaction/promotion | observation week index | week dimension key | use for trends |
| PRODUCT_ID | integer | No | transaction/product/promotion | product identifier | product dimension key | no named brand inference |
| SALES_VALUE | numeric | No | transaction | net line value after recorded discounts | transaction-line measure | Panel Net Spend input |
| QUANTITY | numeric | No | transaction | source quantity | transaction-line measure | preserve/flag outliers |
| STORE_ID | integer | No | transaction/promotion | source store identifier | store dimension key | no geography invented |
| RETAIL_DISC | numeric | No | transaction | source retail discount | transaction-line measure | audit signs first |
| COUPON_DISC | numeric | No | transaction | source coupon discount | transaction-line measure | audit signs first |
| COUPON_MATCH_DISC | numeric | No | transaction | source coupon match discount | transaction-line measure | audit signs first |
| display | categorical | No | promotion | raw display code | product × store × week | categorical, not ordinal |
| mailer | categorical | No | promotion | raw mailer code | product × store × week | categorical, not ordinal |
| BRAND | categorical | No in source contract | product | private/national brand code | product | no margin inference |
| DEPARTMENT | string | No | product | department descriptor | department × commodity category | source-defined |
| COMMODITY_DESC | string | No | product | commodity descriptor | department × commodity category | affinity level |
| CAMPAIGN | integer | No | campaign/coupon | campaign identifier | campaign or household × campaign | recipient targeting bias |
| COUPON_UPC | integer | No | coupon/redemption | coupon identifier | coupon × product × campaign bridge | many-to-many bridge |
| classification_1..5 / HOMEOWNER_DESC / KID_CATEGORY_DESC | string | Yes | demographics | source-supplied demographic descriptors; classification_1..5 are anonymized fields mapped positionally to legacy roles | household snapshot | partial coverage |

## Curated fields

- retail_discount_value, coupon_discount_value, coupon_match_discount_value: absolute values after sign audit.
- gross_spend_before_recorded_discounts: descriptive reconstruction only.
- transaction_hour: parsed TRANS_TIME hour.
- quantity_outlier_flag: flag; raw quantity remains.
- synthetic_date: mechanics only; never real seasonality.
