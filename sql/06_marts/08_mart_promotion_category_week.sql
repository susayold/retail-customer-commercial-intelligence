CREATE OR REPLACE TABLE mart_promotion_category_week AS
WITH sales AS (
    SELECT
        product_id,
        store_id,
        week_number,
        SUM(sales_value) AS panel_sales,
        SUM(quantity_raw) AS panel_units,
        COUNT(DISTINCT household_key) AS panel_buying_households,
        COUNT(DISTINCT basket_id) AS panel_baskets
    FROM fct_transaction_line
    GROUP BY product_id, store_id, week_number
),
working_panel AS (
    SELECT
        ps.product_id,
        ps.store_id,
        ps.week_number,
        COALESCE(s.panel_sales, 0) AS panel_sales,
        COALESCE(s.panel_units, 0) AS panel_units,
        COALESCE(s.panel_buying_households, 0) AS panel_buying_households,
        COALESCE(s.panel_baskets, 0) AS panel_baskets,
        ps.promo_state_group,
        p.department,
        p.commodity,
        p.brand_type
    FROM fct_promotion_product_store_week ps
    LEFT JOIN sales s USING (product_id, store_id, week_number)
    LEFT JOIN dim_product p USING (product_id)
)
SELECT
    commodity,
    department,
    week_number,
    promo_state_group,
    COUNT(*) AS product_store_weeks,
    SUM(panel_sales) AS panel_sales,
    SUM(panel_units) AS panel_units,
    SUM(panel_buying_households) AS panel_buying_households,
    SUM(panel_baskets) AS panel_baskets
FROM working_panel
GROUP BY commodity, department, week_number, promo_state_group;
