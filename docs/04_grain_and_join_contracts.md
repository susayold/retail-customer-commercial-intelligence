# Grain and join contracts

| Model | Grain | Candidate key | Allowed duplicates | Fan-out risk |
|---|---|---|---|---|
| source transaction | one product line in basket | source row + derived line id | source duplicates audited | product/demographic joins |
| fct_basket | one basket | basket_id | none after validation | line-level counts mistaken as trips |
| dim_household | one observed household | household_key | none | demographic duplicates |
| dim_product | one product | product_id | none | product lookup multiplying lines |
| fct_promotion_product_store_week | product × store × week | three-column key | none | duplicate causal rows |
| fct_campaign_exposure | household × campaign | two-column key | none | coupon bridge multiplication |
| bridge_coupon_product_campaign | coupon UPC × product × campaign | three-column key | none at exact grain | flattening into customer exposure |
| fct_coupon_redemption | one redemption event | event fields | source duplicate audit | many-to-many coupon mapping |
| mart_household_weekly | household × week | two-column key | none | mixing with line grain |
| mart_category_weekly | department × commodity × week | three-column key | none | category filters changing denominator |

## Join rules

1. Build basket facts from line facts; use COUNT(DISTINCT basket_id).
2. Build all-household dimension from observed transactions, then left join demographics.
3. Join product attributes at product grain.
4. Keep coupon-product-campaign as a bridge; never aggregate customer reach after an uncontrolled bridge join.
5. Build promotion analysis from a product-store-week skeleton left-joined to aggregated sales so zero-sale promoted weeks remain visible.
6. Use anti-joins to identify unmatched products, households, campaigns and promotion keys.
7. Store expected cardinality and QA status beside each model.

## Mandatory fan-out demonstrations

### Unsafe campaign join

campaign_table (household × campaign) joined directly to coupon (coupon × product × campaign) creates multiple rows per recipient. Reach must be counted before the bridge, or after a distinct household-campaign projection.

### Unsafe basket metric

Counting transaction lines overstates trips. The correct basket metric is COUNT(DISTINCT basket_id) or a dedicated basket fact.

## Lifecycle note

The first observed transaction is not a true acquisition event. Use first_observed_purchase_day and engagement persistence rather than classic acquisition retention.
