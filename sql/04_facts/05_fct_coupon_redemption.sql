CREATE OR REPLACE TABLE fct_coupon_redemption AS
SELECT
    household_key,
    day_key,
    coupon_upc,
    campaign_id,
    ROW_NUMBER() OVER () AS redemption_event_id
FROM stg_coupon_redemption;
