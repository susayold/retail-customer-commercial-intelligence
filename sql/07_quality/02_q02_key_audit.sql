CREATE OR REPLACE TABLE qa_key_audit AS
SELECT 'product' AS model, COUNT(*) - COUNT(DISTINCT product_id) AS duplicate_rows FROM dim_product
UNION ALL
SELECT 'household', COUNT(*) - COUNT(DISTINCT household_key) FROM dim_household
UNION ALL
SELECT 'promotion_product_store_week',
       COUNT(*) - COUNT(DISTINCT product_id || '-' || store_id || '-' || week_number)
FROM fct_promotion_product_store_week
UNION ALL
SELECT 'campaign_exposure',
       COUNT(*) - COUNT(DISTINCT household_key || '-' || campaign_id)
FROM fct_campaign_exposure
UNION ALL
SELECT 'coupon_bridge',
       COUNT(*) - COUNT(DISTINCT coupon_upc || '-' || product_id || '-' || campaign_id)
FROM bridge_coupon_product_campaign;
