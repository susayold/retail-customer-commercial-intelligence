CREATE OR REPLACE TABLE qa_key_audit AS
SELECT
    'product' AS model,
    COUNT(*) - COUNT(DISTINCT product_id) AS duplicate_rows
FROM dim_product
UNION ALL
SELECT
    'household',
    COUNT(*) - COUNT(DISTINCT household_key)
FROM dim_household
UNION ALL
SELECT
    'promotion_product_store_week',
    COUNT(*) - COUNT(DISTINCT CONCAT(
        COALESCE(CAST(product_id AS VARCHAR), '<NULL>'), '|',
        COALESCE(CAST(store_id AS VARCHAR), '<NULL>'), '|',
        COALESCE(CAST(week_number AS VARCHAR), '<NULL>')
    ))
FROM fct_promotion_product_store_week
UNION ALL
SELECT
    'campaign_exposure',
    COUNT(*) - COUNT(DISTINCT CONCAT(
        COALESCE(CAST(household_key AS VARCHAR), '<NULL>'), '|',
        COALESCE(CAST(campaign_id AS VARCHAR), '<NULL>')
    ))
FROM fct_campaign_exposure
UNION ALL
SELECT
    'coupon_bridge',
    COUNT(*) - COUNT(DISTINCT CONCAT(
        COALESCE(CAST(coupon_upc AS VARCHAR), '<NULL>'), '|',
        COALESCE(CAST(product_id AS VARCHAR), '<NULL>'), '|',
        COALESCE(CAST(campaign_id AS VARCHAR), '<NULL>')
    ))
FROM bridge_coupon_product_campaign;