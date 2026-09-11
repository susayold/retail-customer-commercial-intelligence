CREATE OR REPLACE TABLE analysis_basket_category AS
SELECT
    commodity,
    SUM(panel_net_spend) AS panel_net_spend,
    SUM(buying_households) AS buying_household_week_records,
    SUM(category_baskets) AS category_baskets,
    AVG(private_label_share) AS avg_private_label_share,
    AVG(discount_rate) AS avg_discount_rate
FROM mart_category_weekly
GROUP BY commodity;
