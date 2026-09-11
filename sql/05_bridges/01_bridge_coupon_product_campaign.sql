CREATE OR REPLACE TABLE bridge_coupon_product_campaign AS
SELECT
    coupon_upc,
    product_id,
    campaign_id
FROM stg_coupon_product
GROUP BY coupon_upc, product_id, campaign_id;
