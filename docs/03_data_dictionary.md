# Data dictionary

This dictionary distinguishes raw fields from curated fields. Raw source names are preserved alongside normalized names in staging.

| Field | Source | Meaning | Caveat |
|---|---|---|---|
| household_key | transaction/demographic/campaign | panel household identifier | panel only |
| BASKET_ID | transaction | shopping trip/basket identifier | count distinct baskets |
| DAY | transaction/campaign | observation day index | not a calendar date |
| WEEK_NO | transaction/promotion | observation week index | use for trends |
| PRODUCT_ID | transaction/product/promotion | product identifier | no named brand inference |
| SALES_VALUE | transaction | net line value after recorded discounts | Panel Net Spend input |
| QUANTITY | transaction | source quantity | preserve/flag outliers |
| STORE_ID | transaction/promotion | source store identifier | no geography invented |
| RETAIL_DISC | transaction | source retail discount | audit signs first |
| COUPON_DISC | transaction | source coupon discount | audit signs first |
| COUPON_MATCH_DISC | transaction | source coupon match discount | audit signs first |
| display | promotion | raw display code | categorical, not ordinal |
| mailer | promotion | raw mailer code | categorical, not ordinal |
| BRAND | product | raw private/national brand code | raw value preserved; normalize with `UPPER(TRIM(BRAND))` before semantic comparisons |
| DEPARTMENT | product | department descriptor | source-defined |
| COMMODITY_DESC | product | commodity descriptor | affinity level |
| CAMPAIGN | campaign | campaign identifier | recipient targeting bias |
| COUPON_UPC | coupon/redemption | coupon identifier | many-to-many bridge |
| classification_1..5 / HOMEOWNER_DESC / KID_CATEGORY_DESC | demographics | source-supplied demographic descriptors; classification_1..5 are anonymized fields mapped positionally to the legacy age, marital, income, household-composition and household-size roles | partial coverage |

## Curated fields

- `brand_type_raw` preserves the production source value exactly; `brand_type` is the governed `UPPER(TRIM(BRAND))` value used by downstream metrics.
- retail_discount_value, coupon_discount_value, coupon_match_discount_value: absolute values after sign audit.
- gross_spend_before_recorded_discounts: descriptive reconstruction only.
- transaction_hour: parsed TRANS_TIME hour.
- quantity_outlier_flag: flag; raw quantity remains.
- synthetic_date: mechanics only; never real seasonality.
