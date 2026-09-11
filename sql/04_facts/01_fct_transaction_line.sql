CREATE OR REPLACE TABLE fct_transaction_line AS
SELECT
    ROW_NUMBER() OVER () AS transaction_line_id,
    t.*,
    t.sales_value
      + t.retail_discount_value
      + t.coupon_discount_value
      + t.coupon_match_discount_value AS gross_spend_before_recorded_discounts,
    CASE
        WHEN t.quantity_raw <= 0 THEN TRUE
        WHEN t.quantity_raw > PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY t.quantity_raw) OVER () THEN TRUE
        ELSE FALSE
    END AS quantity_outlier_flag
FROM stg_transaction t;
