CREATE OR REPLACE TABLE mart_panel_weekly AS
WITH basket_weekly AS (
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
        AVG(CASE WHEN has_coupon_discount THEN 1.0 ELSE 0.0 END) AS coupon_basket_rate
    FROM fct_basket
    GROUP BY week_number
),
private_label_weekly AS (
    SELECT
        t.week_number,
        SUM(CASE WHEN p.brand_type = 'PRIVATE' THEN t.sales_value ELSE 0 END) AS private_label_spend
    FROM fct_transaction_line t
    LEFT JOIN dim_product p USING (product_id)
    GROUP BY t.week_number
)
SELECT
    b.*,
    p.private_label_spend,
    p.private_label_spend / NULLIF(b.panel_net_spend, 0) AS private_label_share
FROM basket_weekly b
LEFT JOIN private_label_weekly p USING (week_number);