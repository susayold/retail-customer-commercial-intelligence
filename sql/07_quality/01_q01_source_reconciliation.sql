CREATE OR REPLACE TABLE qa_source_reconciliation AS
SELECT
    'transaction_data' AS source_name,
    COUNT(*) AS row_count,
    COUNT(DISTINCT household_key) AS households,
    COUNT(DISTINCT BASKET_ID) AS baskets
FROM raw_transaction_data
UNION ALL
SELECT
    'causal_data',
    COUNT(*),
    0,
    COUNT(DISTINCT CONCAT(
        COALESCE(CAST(PRODUCT_ID AS VARCHAR), '<NULL>'), '|',
        COALESCE(CAST(STORE_ID AS VARCHAR), '<NULL>'), '|',
        COALESCE(CAST(WEEK_NO AS VARCHAR), '<NULL>')
    ))
FROM raw_causal_data
UNION ALL
SELECT
    'coupon',
    COUNT(*),
    0,
    COUNT(DISTINCT CONCAT(
        COALESCE(CAST(COUPON_UPC AS VARCHAR), '<NULL>'), '|',
        COALESCE(CAST(PRODUCT_ID AS VARCHAR), '<NULL>'), '|',
        COALESCE(CAST(CAMPAIGN AS VARCHAR), '<NULL>')
    ))
FROM raw_coupon
UNION ALL
SELECT
    'coupon_redempt',
    COUNT(*),
    COUNT(DISTINCT household_key),
    COUNT(DISTINCT CONCAT(
        COALESCE(CAST(household_key AS VARCHAR), '<NULL>'), '|',
        COALESCE(CAST(DAY AS VARCHAR), '<NULL>'), '|',
        COALESCE(CAST(COUPON_UPC AS VARCHAR), '<NULL>'), '|',
        COALESCE(CAST(CAMPAIGN AS VARCHAR), '<NULL>')
    ))
FROM raw_coupon_redempt
UNION ALL
SELECT
    'campaign_table',
    COUNT(*),
    COUNT(DISTINCT household_key),
    COUNT(DISTINCT CONCAT(
        COALESCE(CAST(household_key AS VARCHAR), '<NULL>'), '|',
        COALESCE(CAST(CAMPAIGN AS VARCHAR), '<NULL>')
    ))
FROM raw_campaign_table
UNION ALL
SELECT
    'campaign_desc',
    COUNT(*),
    COUNT(DISTINCT CAMPAIGN),
    COUNT(DISTINCT CAMPAIGN)
FROM raw_campaign_desc
UNION ALL
SELECT
    'product',
    COUNT(*),
    COUNT(DISTINCT PRODUCT_ID),
    COUNT(DISTINCT PRODUCT_ID)
FROM raw_product
UNION ALL
SELECT
    'hh_demographic',
    COUNT(*),
    COUNT(DISTINCT household_key),
    COUNT(DISTINCT household_key)
FROM raw_hh_demographic;