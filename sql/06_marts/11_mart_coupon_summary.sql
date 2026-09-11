CREATE OR REPLACE TABLE mart_coupon_summary AS
SELECT
    r.campaign_id,
    COUNT(*) AS redemption_events,
    COUNT(DISTINCT r.household_key) AS redeemer_households,
    COUNT(DISTINCT r.coupon_upc) AS redeemed_coupons,
    COUNT(DISTINCT b.product_id) AS linked_products
FROM fct_coupon_redemption r
LEFT JOIN bridge_coupon_product_campaign b
  ON b.coupon_upc = r.coupon_upc
 AND b.campaign_id = r.campaign_id
GROUP BY r.campaign_id;
