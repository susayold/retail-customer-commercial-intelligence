-- Grain: store x observation week.
CREATE OR REPLACE TABLE mart_store_weekly AS
SELECT
    store_id,
    week_number,
    SUM(sales_value) AS panel_net_spend,
    COUNT(DISTINCT basket_id) AS baskets,
    COUNT(DISTINCT household_key) AS active_households,
    COUNT(DISTINCT product_id) AS distinct_products,
    COUNT(*) AS transaction_lines,
    SUM(sales_value) / NULLIF(COUNT(DISTINCT basket_id), 0) AS spend_per_basket
FROM fct_transaction_line
GROUP BY store_id, week_number;
