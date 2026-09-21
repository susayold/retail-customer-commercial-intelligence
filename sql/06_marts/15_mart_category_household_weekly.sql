-- Grain: household x observation week x governed category.
-- This mart is the source for dynamic category penetration. Do not sum
-- weekly unique-household measures across weeks for a selected-period rate.
CREATE OR REPLACE TABLE mart_category_household_weekly AS
SELECT
    t.household_key,
    t.week_number,
    c.category_key,
    c.department,
    c.commodity,
    SUM(t.sales_value) AS panel_net_spend,
    COUNT(DISTINCT t.basket_id) AS category_baskets,
    SUM(t.quantity_raw) AS units,
    COUNT(DISTINCT t.product_id) AS distinct_products,
    SUM(t.retail_discount_value + t.coupon_discount_value + t.coupon_match_discount_value)
        AS discount_value
FROM fct_transaction_line t
LEFT JOIN dim_product p USING (product_id)
LEFT JOIN dim_category c
    ON c.department = COALESCE(NULLIF(TRIM(p.department), ''), 'Unknown')
   AND c.commodity = COALESCE(NULLIF(TRIM(p.commodity), ''), 'Unknown')
GROUP BY t.household_key, t.week_number, c.category_key, c.department, c.commodity;
