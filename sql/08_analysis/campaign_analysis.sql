CREATE OR REPLACE TABLE analysis_campaign_funnel AS
SELECT
    c.campaign_id,
    c.campaign_type,
    c.campaign_recipients,
    c.campaign_redeemers,
    c.campaign_redemption_rate,
    c.avg_pre_28d_spend,
    c.avg_during_spend,
    c.avg_post_28d_spend,
    c.post_28d_observable_rows,
    c.avg_during_spend - c.avg_pre_28d_spend AS avg_spend_change_during,
    c.avg_post_28d_spend - c.avg_pre_28d_spend AS avg_spend_change_post
FROM mart_campaign_summary c;