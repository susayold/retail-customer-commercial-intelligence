CREATE OR REPLACE TABLE export_powerbi_metric_reconciliation AS
SELECT 'Panel Net Spend' AS metric, SUM(panel_net_spend) AS sql_value
FROM mart_panel_weekly
UNION ALL
SELECT 'Baskets', SUM(baskets)
FROM mart_panel_weekly
UNION ALL
SELECT 'Active Households', MAX(active_households)
FROM mart_panel_weekly
UNION ALL
SELECT 'Spend per Basket', SUM(panel_net_spend) / NULLIF(SUM(baskets), 0)
FROM mart_panel_weekly
UNION ALL
SELECT 'Private Label Share',
       SUM(private_label_spend) / NULLIF(SUM(panel_net_spend), 0)
FROM mart_panel_weekly
UNION ALL
SELECT 'Campaign Recipients', SUM(campaign_recipients)
FROM mart_campaign_summary
UNION ALL
SELECT 'Campaign Redeemers', SUM(campaign_redeemers)
FROM mart_campaign_summary
UNION ALL
SELECT 'Redemption Rate',
       SUM(campaign_redeemers) / NULLIF(SUM(campaign_recipients), 0)
FROM mart_campaign_summary;