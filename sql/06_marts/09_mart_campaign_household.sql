CREATE OR REPLACE TABLE mart_campaign_household AS
WITH transaction_windows AS (
    SELECT
        e.household_key,
        e.campaign_id,
        SUM(CASE WHEN t.day_key BETWEEN e.start_day - 28 AND e.start_day - 1 THEN t.sales_value ELSE 0 END) AS pre_28d_spend,
        COUNT(DISTINCT CASE WHEN t.day_key BETWEEN e.start_day - 28 AND e.start_day - 1 THEN t.basket_id END) AS pre_28d_baskets,
        SUM(CASE WHEN t.day_key BETWEEN e.start_day AND e.end_day THEN t.sales_value ELSE 0 END) AS during_spend,
        COUNT(DISTINCT CASE WHEN t.day_key BETWEEN e.start_day AND e.end_day THEN t.basket_id END) AS during_baskets,
        SUM(CASE WHEN t.day_key BETWEEN e.end_day + 1 AND e.end_day + 28 THEN t.sales_value ELSE 0 END) AS post_28d_spend,
        COUNT(DISTINCT CASE WHEN t.day_key BETWEEN e.end_day + 1 AND e.end_day + 28 THEN t.basket_id END) AS post_28d_baskets
    FROM fct_campaign_exposure e
    LEFT JOIN fct_transaction_line t
        ON t.household_key = e.household_key
       AND t.day_key BETWEEN e.start_day - 28 AND e.end_day + 28
    GROUP BY e.household_key, e.campaign_id
),
redemptions AS (
    SELECT
        household_key,
        campaign_id,
        COUNT(*) AS redemption_count
    FROM fct_coupon_redemption
    GROUP BY household_key, campaign_id
)
SELECT
    e.household_key,
    e.campaign_id,
    e.campaign_type,
    e.start_day,
    e.end_day,
    e.post_14d_observable,
    e.post_28d_observable,
    COALESCE(t.pre_28d_spend, 0) AS pre_28d_spend,
    COALESCE(t.pre_28d_baskets, 0) AS pre_28d_baskets,
    COALESCE(t.during_spend, 0) AS during_spend,
    COALESCE(t.during_baskets, 0) AS during_baskets,
    CASE WHEN e.post_28d_observable THEN COALESCE(t.post_28d_spend, 0) END AS post_28d_spend,
    CASE WHEN e.post_28d_observable THEN COALESCE(t.post_28d_baskets, 0) END AS post_28d_baskets,
    (COALESCE(r.redemption_count, 0) > 0)::BOOLEAN AS redeemed_coupon_flag,
    COALESCE(r.redemption_count, 0) AS redemption_count,
    s.segment,
    h.has_demographics
FROM fct_campaign_exposure e
LEFT JOIN transaction_windows t
    ON t.household_key = e.household_key
   AND t.campaign_id = e.campaign_id
LEFT JOIN redemptions r
    ON r.household_key = e.household_key
   AND r.campaign_id = e.campaign_id
LEFT JOIN mart_customer_segment s USING (household_key)
LEFT JOIN dim_household h USING (household_key);