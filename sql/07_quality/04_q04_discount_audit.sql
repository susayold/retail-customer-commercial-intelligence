CREATE OR REPLACE TABLE qa_discount_audit AS
SELECT
    COUNT(*) AS transaction_lines,
    SUM(CASE WHEN retail_disc_raw > 0 THEN 1 ELSE 0 END) AS positive_retail_disc_rows,
    SUM(CASE WHEN coupon_disc_raw > 0 THEN 1 ELSE 0 END) AS positive_coupon_disc_rows,
    SUM(CASE WHEN coupon_match_disc_raw > 0 THEN 1 ELSE 0 END) AS positive_coupon_match_disc_rows,
    SUM(retail_discount_value) AS retail_discount_value,
    SUM(coupon_discount_value) AS coupon_discount_value,
    SUM(coupon_match_discount_value) AS coupon_match_discount_value
FROM stg_transaction;
