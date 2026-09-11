CREATE OR REPLACE TABLE mart_brand_category AS
SELECT
    p.department,
    p.commodity,
    p.brand_type,
    SUM(t.sales_value) AS panel_net_spend,
    COUNT(DISTINCT t.household_key) AS buying_households,
    COUNT(DISTINCT t.basket_id) AS baskets,
    SUM(t.sales_value) / NULLIF(COUNT(DISTINCT t.household_key), 0) AS spend_per_buying_household,
    SUM(t.retail_discount_value + t.coupon_discount_value + t.coupon_match_discount_value)
        / NULLIF(SUM(t.gross_spend_before_recorded_discounts), 0) AS discount_rate
FROM fct_transaction_line t
LEFT JOIN dim_product p USING (product_id)
GROUP BY p.department, p.commodity, p.brand_type;
