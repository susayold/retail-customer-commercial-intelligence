-- Stability check for deterministic segmentation after removing the final window.
CREATE OR REPLACE TABLE analysis_segment_stability AS
WITH bounds AS (
    SELECT MIN(week_number) AS min_week, MAX(week_number) AS max_week
    FROM mart_household_weekly
),
trimmed_bounds AS (
    SELECT min_week, max_week - {{ SEGMENT_STABILITY_EXCLUSION_WEEKS }} AS trimmed_max_week
    FROM bounds
),
coupon_stats AS (
    SELECT
        household_key,
        COUNT(*) FILTER (WHERE has_coupon_discount AND week_number <= (SELECT trimmed_max_week FROM trimmed_bounds)) AS coupon_baskets,
        COUNT(*) FILTER (WHERE week_number <= (SELECT trimmed_max_week FROM trimmed_bounds)) AS total_baskets
    FROM fct_basket
    GROUP BY household_key
),
trimmed_summary AS (
    SELECT
        h.household_key,
        SUM(h.net_spend) AS observed_lifetime_spend,
        SUM(h.baskets) AS frequency_baskets,
        COUNT(DISTINCT h.week_number) AS active_weeks,
        SUM(h.discount_value) / NULLIF(SUM(h.net_spend + h.discount_value), 0) AS discount_share,
        COALESCE(cs.coupon_baskets / NULLIF(cs.total_baskets, 0), 0) AS coupon_basket_rate,
        SUM(h.private_label_spend) / NULLIF(SUM(h.net_spend), 0) AS private_label_share,
        AVG(CASE WHEN h.week_number <= b.min_week + {{ TRAJECTORY_WINDOW_WEEKS }} - 1 THEN h.net_spend END) AS early_avg_weekly_spend,
        AVG(CASE WHEN h.week_number > b.trimmed_max_week - {{ TRAJECTORY_WINDOW_WEEKS }} THEN h.net_spend END) AS late_avg_weekly_spend
    FROM mart_household_weekly h
    CROSS JOIN trimmed_bounds b
    LEFT JOIN coupon_stats cs USING (household_key)
    WHERE h.week_number <= b.trimmed_max_week
    GROUP BY h.household_key, cs.coupon_baskets, cs.total_baskets, b.min_week, b.trimmed_max_week
),
scored AS (
    SELECT
        t.*,
        NTILE(5) OVER (ORDER BY observed_lifetime_spend) AS monetary_quintile,
        NTILE(5) OVER (ORDER BY frequency_baskets) AS frequency_quintile
    FROM trimmed_summary t
),
trimmed_segment AS (
    SELECT
        household_key,
        CASE
            WHEN monetary_quintile >= 4 AND late_avg_weekly_spend <= early_avg_weekly_spend * {{ TRAJECTORY_DECLINING_FACTOR }} THEN 'High-Value Declining'
            WHEN monetary_quintile >= 4 AND late_avg_weekly_spend >= early_avg_weekly_spend * {{ TRAJECTORY_GROWING_FACTOR }} THEN 'High-Value Engaged'
            WHEN frequency_quintile >= 4 AND monetary_quintile < 4 THEN 'Frequent Core'
            WHEN coupon_basket_rate >= {{ SEGMENTATION_PROMOTION_COUPON_BASKET_RATE }} OR discount_share >= {{ SEGMENTATION_PROMOTION_DISCOUNT_SHARE }} THEN 'Promotion-Responsive'
            WHEN private_label_share >= {{ SEGMENTATION_PRIVATE_LABEL_SHARE }} THEN 'Private-Label Loyal'
            WHEN frequency_quintile <= {{ SEGMENTATION_OCCASIONAL_MAX_FREQUENCY_QUINTILE }} AND active_weeks <= {{ SEGMENTATION_OCCASIONAL_MAX_ACTIVE_WEEKS }} THEN 'Occasional'
            ELSE 'Low-Engagement'
        END AS trimmed_segment
    FROM scored
),
comparison AS (
    SELECT
        full_segment.household_key,
        full_segment.segment AS full_segment,
        trimmed_segment.trimmed_segment,
        CASE
            WHEN trimmed_segment.trimmed_segment IS NULL THEN 'Not observable in pre-trim window'
            WHEN full_segment.segment = trimmed_segment.trimmed_segment THEN 'Unchanged'
            ELSE 'Moved'
        END AS stability_class
    FROM mart_customer_segment full_segment
    LEFT JOIN trimmed_segment USING (household_key)
),
totals AS (
    SELECT COUNT(*) AS total_households FROM comparison
),
transitions AS (
    SELECT
        'full_vs_excluding_last_13_weeks' AS comparison_name,
        'transition' AS row_type,
        full_segment,
        COALESCE(trimmed_segment, 'Not observable in pre-trim window') AS trimmed_segment,
        COUNT(*) AS household_count,
        COUNT(*) / NULLIF(MAX(total_households), 0) AS pct_of_households,
        NULL::DOUBLE AS unchanged_pct,
        NULL::DOUBLE AS moved_pct,
        'Deterministic segment comparison; first observed history and late-window censoring apply.' AS interpretation_boundary
    FROM comparison
    CROSS JOIN totals
    GROUP BY full_segment, COALESCE(trimmed_segment, 'Not observable in pre-trim window')
),
overall AS (
    SELECT
        'full_vs_excluding_last_13_weeks' AS comparison_name,
        'overall' AS row_type,
        NULL::VARCHAR AS full_segment,
        NULL::VARCHAR AS trimmed_segment,
        COUNT(*) AS household_count,
        1.0 AS pct_of_households,
        COUNT(*) FILTER (WHERE stability_class = 'Unchanged') / NULLIF(COUNT(*), 0) AS unchanged_pct,
        COUNT(*) FILTER (WHERE stability_class <> 'Unchanged') / NULLIF(COUNT(*), 0) AS moved_pct,
        'Deterministic segment comparison; first observed history and late-window censoring apply.' AS interpretation_boundary
    FROM comparison
)
SELECT * FROM overall
UNION ALL
SELECT * FROM transitions;

