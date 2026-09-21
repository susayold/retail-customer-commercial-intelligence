-- First-observed cohort analysis. This is not acquisition or retention.
CREATE OR REPLACE TABLE analysis_first_observed_cohort AS
WITH bounds AS (
    SELECT MAX(week_number) AS max_week FROM mart_household_weekly
),
household_repeat AS (
    SELECT
        s.household_key,
        s.first_observed_week,
        s.observed_lifetime_spend,
        s.lifetime_baskets,
        CASE WHEN s.first_observed_week + {{ TRAJECTORY_WINDOW_WEEKS }} <= b.max_week THEN TRUE ELSE FALSE END AS follow_up_13_weeks_observable,
        CASE WHEN COUNT(*) FILTER (
            WHERE h.week_number > s.first_observed_week
              AND h.week_number <= s.first_observed_week + {{ TRAJECTORY_WINDOW_WEEKS }}
        ) > 0 THEN TRUE ELSE FALSE END AS repeat_within_13_weeks
    FROM mart_household_summary s
    CROSS JOIN bounds b
    LEFT JOIN mart_household_weekly h USING (household_key)
    GROUP BY s.household_key, s.first_observed_week, s.observed_lifetime_spend, s.lifetime_baskets, b.max_week
)
SELECT
    first_observed_week,
    COUNT(*) AS first_observed_households,
    COUNT(*) FILTER (WHERE follow_up_13_weeks_observable) AS households_with_observable_follow_up,
    COUNT(*) FILTER (WHERE follow_up_13_weeks_observable AND repeat_within_13_weeks) AS repeat_households_within_13_weeks,
    COUNT(*) FILTER (WHERE follow_up_13_weeks_observable AND repeat_within_13_weeks)
        / NULLIF(COUNT(*) FILTER (WHERE follow_up_13_weeks_observable), 0) AS observed_repeat_rate_within_13_weeks,
    AVG(observed_lifetime_spend) AS avg_observed_lifetime_spend,
    AVG(lifetime_baskets) AS avg_observed_lifetime_baskets,
    'First observed activity is not acquisition; cohorts after the 13-week cutoff are censored.' AS interpretation_boundary
FROM household_repeat
GROUP BY first_observed_week;

