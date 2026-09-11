CREATE OR REPLACE VIEW stg_coupon_redemption AS
SELECT
    CAST(household_key AS BIGINT) AS household_key,
    CAST(DAY AS INTEGER) AS day_key,
    CAST(COUPON_UPC AS BIGINT) AS coupon_upc,
    CAST(CAMPAIGN AS INTEGER) AS campaign_id
FROM raw_coupon_redempt;
