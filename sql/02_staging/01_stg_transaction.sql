CREATE OR REPLACE VIEW stg_transaction AS
SELECT
    CAST(household_key AS BIGINT) AS household_key,
    CAST(BASKET_ID AS BIGINT) AS basket_id,
    CAST(DAY AS INTEGER) AS day_key,
    CAST(PRODUCT_ID AS BIGINT) AS product_id,
    CAST(QUANTITY AS DOUBLE) AS quantity_raw,
    CAST(SALES_VALUE AS DOUBLE) AS sales_value,
    CAST(STORE_ID AS BIGINT) AS store_id,
    CAST(RETAIL_DISC AS DOUBLE) AS retail_disc_raw,
    CAST(COUPON_DISC AS DOUBLE) AS coupon_disc_raw,
    CAST(COUPON_MATCH_DISC AS DOUBLE) AS coupon_match_disc_raw,
    ABS(CAST(RETAIL_DISC AS DOUBLE)) AS retail_discount_value,
    ABS(CAST(COUPON_DISC AS DOUBLE)) AS coupon_discount_value,
    ABS(CAST(COUPON_MATCH_DISC AS DOUBLE)) AS coupon_match_discount_value,
    CAST(TRANS_TIME AS INTEGER) AS trans_time,
    FLOOR(CAST(TRANS_TIME AS INTEGER) / 100) AS transaction_hour,
    CAST(WEEK_NO AS INTEGER) AS week_number
FROM raw_transaction_data;
