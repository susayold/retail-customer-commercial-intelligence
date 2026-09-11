CREATE OR REPLACE TABLE mart_campaign_summary AS
SELECT
    campaign_id,
    MAX(campaign_type) AS campaign_type,
    COUNT(DISTINCT household_key) AS campaign_recipients,
    COUNT(DISTINCT CASE WHEN redeemed_coupon_flag THEN household_key END) AS campaign_redeemers,
    COUNT(DISTINCT CASE WHEN redeemed_coupon_flag THEN household_key END)
        / NULLIF(COUNT(DISTINCT household_key), 0) AS campaign_redemption_rate,
    AVG(pre_28d_spend) AS avg_pre_28d_spend,
    AVG(during_spend) AS avg_during_spend,
    AVG(post_28d_spend) FILTER (WHERE post_28d_observable) AS avg_post_28d_spend,
    COUNT(*) FILTER (WHERE post_28d_observable) AS post_28d_observable_rows
FROM mart_campaign_household
GROUP BY campaign_id;
