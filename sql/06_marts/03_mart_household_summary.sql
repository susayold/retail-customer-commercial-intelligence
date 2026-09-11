CREATE OR REPLACE TABLE mart_household_summary AS
WITH bounds AS (
    SELECT MIN(week_number) AS min_week, MAX(week_number) AS max_week
    FROM mart_household_weekly
),
base AS (
    SELECT
        h.household_key,
        MIN(h.week_number) AS first_observed_week,
        MAX(h.week_number) AS last_observed_week,
        COUNT(DISTINCT h.week_number) AS active_weeks,
        SUM(h.net_spend) AS observed_lifetime_spend,
        SUM(h.baskets) AS lifetime_baskets,
        AVG(h.net_spend / NULLIF(h.baskets, 0)) AS avg_basket_value,
        AVG(h.net_spend) AS avg_weekly_spend,
        MEDIAN(h.net_spend) AS median_weekly_spend,
        SUM(h.discount_value) / NULLIF(SUM(h.net_spend + h.discount_value), 0) AS discount_share,
        SUM(h.coupon_discount) / NULLIF(SUM(h.net_spend + h.discount_value), 0) AS coupon_basket_rate,
        SUM(h.private_label_spend) / NULLIF(SUM(h.net_spend), 0) AS private_label_share,
        MAX(h.distinct_departments) AS distinct_departments,
        MAX(h.distinct_commodities) AS distinct_commodities,
        MAX(h.baskets) AS frequency_baskets,
        AVG(CASE WHEN h.week_number <= b.min_week + 12 THEN h.net_spend END) AS early_avg_weekly_spend,
        AVG(CASE WHEN h.week_number > b.max_week - 13 THEN h.net_spend END) AS late_avg_weekly_spend
    FROM mart_household_weekly h
    CROSS JOIN bounds b
    GROUP BY h.household_key
)
SELECT
    base.*,
    late_avg_weekly_spend - early_avg_weekly_spend AS absolute_change,
    CASE
        WHEN early_avg_weekly_spend IS NULL OR late_avg_weekly_spend IS NULL THEN 'Insufficient History'
        WHEN late_avg_weekly_spend >= early_avg_weekly_spend * 1.10 THEN 'Growing'
        WHEN late_avg_weekly_spend <= early_avg_weekly_spend * 0.90 THEN 'Declining'
        ELSE 'Stable'
    END AS trajectory,
    d.has_demographics
FROM base
LEFT JOIN dim_household d USING (household_key);
