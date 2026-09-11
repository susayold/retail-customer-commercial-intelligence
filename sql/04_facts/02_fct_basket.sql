CREATE OR REPLACE TABLE fct_basket AS
SELECT
    basket_id,
    MAX(household_key) AS household_key,
    MAX(day_key) AS day_key,
    MAX(week_number) AS week_number,
    MAX(store_id) AS store_id,
    SUM(sales_value) AS basket_net_spend,
    SUM(gross_spend_before_recorded_discounts) AS basket_gross_spend,
    SUM(retail_discount_value + coupon_discount_value + coupon_match_discount_value) AS basket_discount_value,
    SUM(coupon_discount_value + coupon_match_discount_value) AS basket_coupon_discount,
    COUNT(*) AS basket_line_count,
    COUNT(DISTINCT product_id) AS basket_distinct_products,
    SUM(quantity_raw) AS basket_quantity_raw,
    COUNT(DISTINCT p.department) AS basket_distinct_departments,
    COUNT(DISTINCT p.commodity) AS basket_distinct_commodities,
    MAX(CASE WHEN coupon_discount_value + coupon_match_discount_value > 0 THEN 1 ELSE 0 END)::BOOLEAN AS has_coupon_discount,
    MAX(transaction_hour) AS transaction_hour
FROM fct_transaction_line t
LEFT JOIN dim_product p USING (product_id)
GROUP BY basket_id;
