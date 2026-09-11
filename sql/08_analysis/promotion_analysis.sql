CREATE OR REPLACE TABLE analysis_promotion_association AS
SELECT
    department,
    commodity,
    promo_state_group,
    SUM(product_store_weeks) AS product_store_weeks,
    SUM(panel_sales) AS panel_sales,
    SUM(panel_units) AS panel_units,
    SUM(panel_buying_households) AS panel_buying_households,
    SUM(panel_baskets) AS panel_baskets,
    SUM(panel_sales) / NULLIF(SUM(product_store_weeks), 0) AS avg_panel_sales_per_product_store_week,
    SUM(panel_baskets) / NULLIF(SUM(product_store_weeks), 0) AS avg_panel_baskets_per_product_store_week
FROM mart_promotion_category_week
GROUP BY department, commodity, promo_state_group;