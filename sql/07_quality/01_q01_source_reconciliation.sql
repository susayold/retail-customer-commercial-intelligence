CREATE OR REPLACE TABLE qa_source_reconciliation AS
SELECT 'transaction_data' AS source_name, COUNT(*) AS row_count, COUNT(DISTINCT household_key) AS households, COUNT(DISTINCT BASKET_ID) AS baskets FROM raw_transaction_data
UNION ALL
SELECT 'causal_data', COUNT(*), COUNT(DISTINCT NULL), COUNT(DISTINCT PRODUCT_ID || '-' || STORE_ID || '-' || WEEK_NO) FROM raw_causal_data
UNION ALL
SELECT 'coupon', COUNT(*), COUNT(DISTINCT NULL), COUNT(DISTINCT COUPON_UPC || '-' || PRODUCT_ID || '-' || CAMPAIGN) FROM raw_coupon
UNION ALL
SELECT 'coupon_redempt', COUNT(*), COUNT(DISTINCT household_key), COUNT(DISTINCT household_key || '-' || DAY || '-' || COUPON_UPC || '-' || CAMPAIGN) FROM raw_coupon_redempt
UNION ALL
SELECT 'campaign_table', COUNT(*), COUNT(DISTINCT household_key), COUNT(DISTINCT household_key || '-' || CAMPAIGN) FROM raw_campaign_table
UNION ALL
SELECT 'campaign_desc', COUNT(*), COUNT(DISTINCT CAMPAIGN), COUNT(DISTINCT CAMPAIGN) FROM raw_campaign_desc
UNION ALL
SELECT 'product', COUNT(*), COUNT(DISTINCT PRODUCT_ID), COUNT(DISTINCT PRODUCT_ID) FROM raw_product
UNION ALL
SELECT 'hh_demographic', COUNT(*), COUNT(DISTINCT household_key), COUNT(DISTINCT household_key) FROM raw_hh_demographic;
