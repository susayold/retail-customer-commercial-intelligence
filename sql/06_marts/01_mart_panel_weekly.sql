CREATE OR REPLACE TABLE mart_panel_weekly AS
SELECT
    week_number,
    SUM(basket_net_spend) AS panel_net_spend,
    SUM(basket_gross_spend) AS panel_gross_spend,
    COUNT(*) AS baskets,
    COUNT(DISTINCT household_key) AS active_households,
    SUM(basket_net_spend) / NULLIF(COUNT(*), 0) AS spend_per_basket,
    COUNT(*) / NULLIF(COUNT(DISTINCT household_key), 0) AS trips_per_household,
    SUM(basket_net_spend) / NULLIF(COUNT(DISTINCT household_key), 0) AS spend_per_household,
    SUM(basket_discount_value) AS discount_value,
    SUM(basket_discount_value) / NULLIF(SUM(basket_gross_spend), 0) AS discount_rate,
    AVG(CASE WHEN has_coupon_discount THEN 1.0 ELSE 0.0 END) AS coupon_basket_rate,
    AVG(CASE WHEN p.brand_type = 'PRIVATE' THEN 1.0 ELSE 0.0 END) AS private_label_share
FROM fct_basket b
LEFT JOIN fct_transaction_line l USING (basket_id)
LEFT JOIN dim_product p USING (product_id)
GROUP BY week_number;
