CREATE OR REPLACE TABLE analysis_customer_engagement AS
SELECT
    s.household_key,
    s.segment,
    s.trajectory,
    s.observed_lifetime_spend,
    s.frequency_baskets,
    s.avg_basket_value,
    s.early_avg_weekly_spend,
    s.late_avg_weekly_spend,
    s.absolute_change,
    s.discount_share,
    s.coupon_basket_rate,
    s.private_label_share
FROM mart_customer_segment s
WHERE s.trajectory IN ('Growing', 'Stable', 'Declining');
