CREATE OR REPLACE TABLE mart_category_weekly AS
WITH active_panel AS (
    SELECT
        week_number,
        COUNT(DISTINCT household_key) AS active_panel_households
    FROM fct_basket
    GROUP BY week_number
)
SELECT
    t.week_number,
    p.department,
    p.commodity,
    SUM(t.sales_value) AS panel_net_spend,
    COUNT(DISTINCT t.household_key) AS buying_households,
    a.active_panel_households,
    COUNT(DISTINCT t.household_key) / NULLIF(a.active_panel_households, 0) AS category_penetration,
    COUNT(DISTINCT t.basket_id) AS category_baskets,
    SUM(t.sales_value) / NULLIF(COUNT(DISTINCT t.household_key), 0) AS spend_per_buying_household,
    SUM(t.retail_discount_value + t.coupon_discount_value + t.coupon_match_discount_value)
        / NULLIF(SUM(t.gross_spend_before_recorded_discounts), 0) AS discount_rate,
    SUM(CASE WHEN p.brand_type = 'PRIVATE' THEN t.sales_value ELSE 0 END)
        / NULLIF(SUM(t.sales_value), 0) AS private_label_share
FROM fct_transaction_line t
LEFT JOIN dim_product p USING (product_id)
LEFT JOIN active_panel a USING (week_number)
GROUP BY t.week_number, p.department, p.commodity, a.active_panel_households;
