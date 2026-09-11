CREATE OR REPLACE TABLE mart_campaign_household AS
SELECT
    e.household_key,
    e.campaign_id,
    e.campaign_type,
    e.start_day,
    e.end_day,
    e.post_14d_observable,
    e.post_28d_observable,
    SUM(CASE WHEN t.day_key BETWEEN e.start_day - 28 AND e.start_day - 1 THEN t.sales_value ELSE 0 END) AS pre_28d_spend,
    COUNT(DISTINCT CASE WHEN t.day_key BETWEEN e.start_day - 28 AND e.start_day - 1 THEN t.basket_id END) AS pre_28d_baskets,
    SUM(CASE WHEN t.day_key BETWEEN e.start_day AND e.end_day THEN t.sales_value ELSE 0 END) AS during_spend,
    COUNT(DISTINCT CASE WHEN t.day_key BETWEEN e.start_day AND e.end_day THEN t.basket_id END) AS during_baskets,
    CASE WHEN e.post_28d_observable THEN SUM(CASE WHEN t.day_key BETWEEN e.end_day + 1 AND e.end_day + 28 THEN t.sales_value ELSE 0 END) END AS post_28d_spend,
    CASE WHEN e.post_28d_observable THEN COUNT(DISTINCT CASE WHEN t.day_key BETWEEN e.end_day + 1 AND e.end_day + 28 THEN t.basket_id END) END AS post_28d_baskets,
    MAX(CASE WHEN r.household_key IS NOT NULL THEN 1 ELSE 0 END)::BOOLEAN AS redeemed_coupon_flag,
    COUNT(DISTINCT r.redemption_event_id) AS redemption_count,
    s.segment,
    h.has_demographics
FROM fct_campaign_exposure e
LEFT JOIN fct_transaction_line t
    ON t.household_key = e.household_key
LEFT JOIN fct_coupon_redemption r
    ON r.household_key = e.household_key
   AND r.campaign_id = e.campaign_id
LEFT JOIN mart_customer_segment s USING (household_key)
LEFT JOIN dim_household h USING (household_key)
GROUP BY ALL;
