CREATE OR REPLACE TABLE mart_category_household AS
SELECT
    t.household_key,
    c.category_key,
    p.department,
    p.commodity,
    MIN(t.day_key) AS first_observed_day,
    MAX(t.day_key) AS last_observed_day,
    MIN(t.week_number) AS first_observed_week,
    MAX(t.week_number) AS last_observed_week,
    COUNT(DISTINCT t.week_number) AS active_weeks,
    COUNT(DISTINCT t.day_key) AS active_days,
    SUM(t.sales_value) AS panel_net_spend,
    COUNT(DISTINCT t.basket_id) AS category_baskets,
    COUNT(DISTINCT t.product_id) AS distinct_products,
    SUM(
        t.retail_discount_value
        + t.coupon_discount_value
        + t.coupon_match_discount_value
    ) AS discount_value,
    SUM(t.coupon_discount_value + t.coupon_match_discount_value) AS coupon_discount,
    COUNT(DISTINCT CASE
        WHEN t.coupon_discount_value + t.coupon_match_discount_value > 0
        THEN t.basket_id
    END) AS coupon_baskets,
    SUM(CASE WHEN p.brand_type = 'PRIVATE' THEN t.sales_value ELSE 0 END)
        AS private_label_spend
FROM fct_transaction_line t
LEFT JOIN dim_product p USING (product_id)
LEFT JOIN dim_category c
    ON c.department = COALESCE(NULLIF(TRIM(p.department), ''), 'Unknown')
   AND c.commodity = COALESCE(NULLIF(TRIM(p.commodity), ''), 'Unknown')
GROUP BY t.household_key, c.category_key, p.department, p.commodity;
