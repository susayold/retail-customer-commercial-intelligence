CREATE OR REPLACE TABLE analysis_private_label AS
SELECT
    department,
    commodity,
    SUM(CASE WHEN brand_type = 'PRIVATE' THEN panel_net_spend ELSE 0 END) AS private_label_spend,
    SUM(panel_net_spend) AS category_spend,
    SUM(CASE WHEN brand_type = 'PRIVATE' THEN panel_net_spend ELSE 0 END)
        / NULLIF(SUM(panel_net_spend), 0) AS private_label_share,
    SUM(CASE WHEN brand_type = 'PRIVATE' THEN buying_households ELSE 0 END) AS private_label_buying_households
FROM mart_brand_category
GROUP BY department, commodity;