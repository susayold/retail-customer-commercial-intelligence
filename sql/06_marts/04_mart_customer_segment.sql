CREATE OR REPLACE TABLE mart_customer_segment AS
WITH scored AS (
    SELECT
        s.*,
        NTILE(5) OVER (ORDER BY monetary_spend) AS monetary_quintile,
        NTILE(5) OVER (ORDER BY frequency_baskets) AS frequency_quintile
    FROM (
        SELECT
            h.*,
            h.observed_lifetime_spend AS monetary_spend
        FROM mart_household_summary h
    ) s
)
SELECT
    *,
    CASE
        WHEN monetary_quintile >= 4 AND trajectory = 'Declining' THEN 'High-Value Declining'
        WHEN monetary_quintile >= 4 AND trajectory IN ('Growing', 'Stable') THEN 'High-Value Engaged'
        WHEN frequency_quintile >= 4 AND monetary_quintile < 4 THEN 'Frequent Core'
        WHEN coupon_basket_rate >= 0.30 OR discount_share >= 0.20 THEN 'Promotion-Responsive'
        WHEN private_label_share >= 0.60 THEN 'Private-Label Loyal'
        WHEN frequency_quintile <= 2 AND active_weeks <= 8 THEN 'Occasional'
        ELSE 'Low-Engagement'
    END AS segment
FROM scored;
