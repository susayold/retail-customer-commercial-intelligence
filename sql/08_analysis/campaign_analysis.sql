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

 
CREATE OR REPLACE TABLE analysis_campaign_segment AS
SELECT
    campaign_id,
    COALESCE(campaign_type, 'Unknown') AS campaign_type,
    COALESCE(segment, 'Unknown') AS customer_segment,
    COUNT(DISTINCT household_key) AS recipient_households,
    COUNT(DISTINCT CASE WHEN redeemed_coupon_flag THEN household_key END) AS redeemer_households,
    COUNT(DISTINCT CASE WHEN redeemed_coupon_flag THEN household_key END)
        / NULLIF(COUNT(DISTINCT household_key), 0) AS redemption_rate,
    AVG(pre_28d_spend) FILTER (WHERE pre_28d_observable) AS avg_pre_28d_spend,
    AVG(during_spend) FILTER (WHERE during_observable) AS avg_during_spend,
    AVG(post_28d_spend) FILTER (WHERE post_28d_observable) AS avg_post_28d_spend,
    COUNT(*) FILTER (WHERE pre_28d_observable) AS pre_28d_observable_rows,
    COUNT(*) FILTER (WHERE during_observable) AS during_observable_rows,
    COUNT(*) FILTER (WHERE post_14d_observable) AS post_14d_observable_rows,
    COUNT(*) FILTER (WHERE post_28d_observable) AS post_28d_observable_rows,
    COUNT(DISTINCT CASE WHEN has_demographics THEN household_key END)
        AS demographic_households,
    'Observed response; recipient targeting and observability limits apply' AS interpretation_boundary
FROM mart_campaign_household
GROUP BY campaign_id, COALESCE(campaign_type, 'Unknown'), COALESCE(segment, 'Unknown');
