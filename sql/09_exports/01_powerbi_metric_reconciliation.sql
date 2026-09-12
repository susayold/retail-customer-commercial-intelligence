CREATE OR REPLACE TABLE export_powerbi_metric_reconciliation AS
WITH metrics AS (
    SELECT
        'Panel Net Spend' AS metric,
        SUM(basket_net_spend) AS sql_value
    FROM mart_basket
    UNION ALL
    SELECT 'Baskets', COUNT(DISTINCT basket_id)
    FROM mart_basket
    UNION ALL
    SELECT 'Active Panel Households', COUNT(DISTINCT household_key)
    FROM mart_basket
    UNION ALL
    SELECT 'Spend per Basket',
           SUM(basket_net_spend) / NULLIF(COUNT(DISTINCT basket_id), 0)
    FROM mart_basket
    UNION ALL
    SELECT 'Private Label Share',
           SUM(private_label_spend) / NULLIF(SUM(panel_net_spend), 0)
    FROM mart_panel_weekly
    UNION ALL
    SELECT 'Campaign Recipients', COUNT(DISTINCT household_key)
    FROM mart_campaign_household
    UNION ALL
    SELECT 'Campaign Redeemers',
           COUNT(DISTINCT CASE WHEN redeemed_coupon_flag THEN household_key END)
    FROM mart_campaign_household
)
SELECT metric, sql_value
FROM metrics
UNION ALL
SELECT
    'Redemption Rate',
    COUNT(DISTINCT CASE WHEN redeemed_coupon_flag THEN household_key END)
        / NULLIF(COUNT(DISTINCT household_key), 0)
FROM mart_campaign_household;
