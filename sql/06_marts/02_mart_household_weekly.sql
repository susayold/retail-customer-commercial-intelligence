CREATE OR REPLACE TABLE mart_household_weekly AS
SELECT
    household_key,
    week_number,
    SUM(sales_value) AS net_spend,
    COUNT(DISTINCT basket_id) AS baskets,
    COUNT(DISTINCT product_id) AS distinct_products,
    COUNT(DISTINCT p.department) AS distinct_departments,
    COUNT(DISTINCT p.commodity) AS distinct_commodities,
    SUM(retail_discount_value + coupon_discount_value + coupon_match_discount_value) AS discount_value,
    SUM(coupon_discount_value + coupon_match_discount_value) AS coupon_discount,
    SUM(CASE WHEN p.brand_type = 'PRIVATE' THEN sales_value ELSE 0 END) AS private_label_spend
FROM fct_transaction_line t
LEFT JOIN dim_product p USING (product_id)
GROUP BY household_key, week_number;
