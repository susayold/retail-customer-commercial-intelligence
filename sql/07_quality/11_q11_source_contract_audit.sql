-- Source-level null, domain, range and key checks.
-- These checks are descriptive and fail closed for structural contract breaks;
-- transaction anomalies that are intentionally retained are handled separately.
CREATE OR REPLACE TABLE qa_source_contract_audit AS
WITH checks AS (
    SELECT 'transaction_data' AS source_name, 'required_household_key' AS check_name,
           COUNT(*) FILTER (WHERE TRY_CAST(household_key AS BIGINT) IS NULL) AS violating_rows,
           'block' AS severity, 'household_key must be non-null' AS rule
    FROM raw_transaction_data
    UNION ALL
    SELECT 'transaction_data', 'required_basket_id', COUNT(*) FILTER (WHERE BASKET_ID IS NULL OR TRIM(CAST(BASKET_ID AS VARCHAR)) = ''), 'block', 'BASKET_ID must be non-null and non-blank'
    FROM raw_transaction_data
    UNION ALL
    SELECT 'transaction_data', 'required_product_id', COUNT(*) FILTER (WHERE TRY_CAST(PRODUCT_ID AS BIGINT) IS NULL), 'block', 'PRODUCT_ID must be non-null and numeric'
    FROM raw_transaction_data
    UNION ALL
    SELECT 'transaction_data', 'required_store_id', COUNT(*) FILTER (WHERE TRY_CAST(STORE_ID AS BIGINT) IS NULL), 'block', 'STORE_ID must be non-null and numeric'
    FROM raw_transaction_data
    UNION ALL
    SELECT 'transaction_data', 'required_sales_value', COUNT(*) FILTER (WHERE TRY_CAST(SALES_VALUE AS DOUBLE) IS NULL), 'block', 'SALES_VALUE must be non-null and numeric'
    FROM raw_transaction_data
    UNION ALL
    SELECT 'transaction_data', 'required_observation_index', COUNT(*) FILTER (WHERE TRY_CAST(DAY AS BIGINT) IS NULL OR TRY_CAST(WEEK_NO AS BIGINT) IS NULL OR TRY_CAST(DAY AS BIGINT) < 1 OR TRY_CAST(WEEK_NO AS BIGINT) < 1), 'block', 'DAY and WEEK_NO must be positive observation indexes'
    FROM raw_transaction_data
    UNION ALL
    SELECT 'transaction_data', 'duplicate_raw_rows',
           COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM raw_transaction_data) AS distinct_rows),
           'warning', 'Exact duplicate raw lines are retained and reported for review'
    FROM raw_transaction_data
    UNION ALL
    SELECT 'product', 'duplicate_product_id', COUNT(*) - COUNT(DISTINCT TRY_CAST(PRODUCT_ID AS BIGINT)), 'block', 'PRODUCT_ID must be unique in the product dimension source'
    FROM raw_product
    UNION ALL
    SELECT 'product', 'required_category_attributes', COUNT(*) FILTER (WHERE DEPARTMENT IS NULL OR TRIM(CAST(DEPARTMENT AS VARCHAR)) = '' OR COMMODITY_DESC IS NULL OR TRIM(CAST(COMMODITY_DESC AS VARCHAR)) = ''), 'warning', 'Missing DEPARTMENT/COMMODITY_DESC is retained as Unknown in the governed category dimension'
    FROM raw_product
    UNION ALL
    SELECT 'product', 'required_brand_flag', COUNT(*) FILTER (WHERE BRAND IS NULL OR TRIM(CAST(BRAND AS VARCHAR)) = ''), 'warning', 'BRAND is preserved as Unknown when source coverage is missing'
    FROM raw_product
    UNION ALL
    SELECT 'product', 'invalid_brand_domain', COUNT(*) FILTER (WHERE BRAND IS NOT NULL AND LOWER(TRIM(CAST(BRAND AS VARCHAR))) NOT IN ('private', 'national')), 'block', 'BRAND must use the source domains Private or National; staging normalizes them to PRIVATE/NATIONAL'
    FROM raw_product
    UNION ALL
    SELECT 'campaign_desc', 'duplicate_campaign_id', COUNT(*) - COUNT(DISTINCT TRY_CAST(CAMPAIGN AS BIGINT)), 'block', 'CAMPAIGN must be unique in campaign description source'
    FROM raw_campaign_desc
    UNION ALL
    SELECT 'campaign_desc', 'invalid_campaign_window', COUNT(*) FILTER (WHERE TRY_CAST(START_DAY AS BIGINT) IS NULL OR TRY_CAST(END_DAY AS BIGINT) IS NULL OR TRY_CAST(START_DAY AS BIGINT) < 1 OR TRY_CAST(END_DAY AS BIGINT) < TRY_CAST(START_DAY AS BIGINT)), 'block', 'Campaign end must be on or after start within the observation index'
    FROM raw_campaign_desc
    UNION ALL
    SELECT 'campaign_table', 'duplicate_campaign_exposure', COUNT(*) - COUNT(DISTINCT CONCAT(CAST(household_key AS VARCHAR), '|', CAST(CAMPAIGN AS VARCHAR))), 'block', 'household x campaign exposure must be unique'
    FROM raw_campaign_table
    UNION ALL
    SELECT 'campaign_table', 'recipient_without_campaign', COUNT(*) FILTER (WHERE DESCRIPTION IS NULL OR NOT EXISTS (SELECT 1 FROM raw_campaign_desc d WHERE d.DESCRIPTION = raw_campaign_table.DESCRIPTION)), 'block', 'Every recipient row must map to a campaign description'
    FROM raw_campaign_table
    UNION ALL
    SELECT 'coupon', 'coupon_without_product', COUNT(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM raw_product p WHERE p.PRODUCT_ID = raw_coupon.PRODUCT_ID)), 'block', 'Every coupon product mapping must map to a product'
    FROM raw_coupon
    UNION ALL
    SELECT 'coupon', 'coupon_without_campaign', COUNT(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM raw_campaign_desc d WHERE d.CAMPAIGN = raw_coupon.CAMPAIGN)), 'block', 'Every coupon mapping must map to a campaign'
    FROM raw_coupon
    UNION ALL
    SELECT 'coupon', 'duplicate_coupon_product_campaign', COUNT(*) - COUNT(DISTINCT CONCAT(CAST(COUPON_UPC AS VARCHAR), '|', CAST(PRODUCT_ID AS VARCHAR), '|', CAST(CAMPAIGN AS VARCHAR))), 'warning', 'Raw coupon relationship repeats are collapsed to a distinct coupon x product x campaign bridge'
    FROM raw_coupon
    UNION ALL
    SELECT 'coupon_redempt', 'duplicate_redemption_event', COUNT(*) - COUNT(DISTINCT CONCAT(CAST(household_key AS VARCHAR), '|', CAST(DAY AS VARCHAR), '|', CAST(COUPON_UPC AS VARCHAR), '|', CAST(CAMPAIGN AS VARCHAR))), 'warning', 'Exact redemption-event duplicates are retained and reported for review'
    FROM raw_coupon_redempt
    UNION ALL
    SELECT 'coupon_redempt', 'redemption_without_coupon_mapping', COUNT(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM raw_coupon c WHERE c.COUPON_UPC = raw_coupon_redempt.COUPON_UPC AND c.CAMPAIGN = raw_coupon_redempt.CAMPAIGN)), 'block', 'Every redemption must map to a coupon x campaign record'
    FROM raw_coupon_redempt
    UNION ALL
    SELECT 'causal_data', 'duplicate_product_store_week', COUNT(*) - COUNT(DISTINCT CONCAT(CAST(PRODUCT_ID AS VARCHAR), '|', CAST(STORE_ID AS VARCHAR), '|', CAST(WEEK_NO AS VARCHAR))), 'warning', 'Raw promotion rows may contain multiple codes at product x store x week; the modeled fact aggregates them at that grain'
    FROM raw_causal_data
    UNION ALL
    SELECT 'causal_data', 'unsupported_promotion_codes', COUNT(*) FILTER (WHERE CAST(display AS VARCHAR) NOT IN ('0', '1', '2', '3', '4', '5', '6', '7', '9', 'A') OR CAST(mailer AS VARCHAR) NOT IN ('0', 'A', 'C', 'D', 'F', 'H', 'J', 'L', 'P', 'X', 'Z')), 'block', 'display and mailer must use the official source code domains; any non-zero code means the activity is on'
    FROM raw_causal_data
)
SELECT
    source_name,
    check_name,
    CAST(violating_rows AS BIGINT) AS violating_rows,
    severity,
    CASE WHEN violating_rows = 0 THEN 'PASS' ELSE 'REVIEW' END AS status,
    rule
FROM checks;
