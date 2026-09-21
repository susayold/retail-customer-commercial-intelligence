-- LMDI decomposition for the panel-spend identity:
-- Panel Spend = Active Households x Trips per Active Household x Spend per Basket.
-- The output is associative/accounting evidence, not a causal estimate.
CREATE OR REPLACE TABLE analysis_root_cause_lmdi AS
WITH bounds AS (
    SELECT MIN(week_number) AS min_week, MAX(week_number) AS max_week
    FROM mart_panel_weekly
),
periods AS (
    SELECT
        CASE
            WHEN week_number <= min_week + {{ TRAJECTORY_WINDOW_WEEKS }} - 1 THEN 'First {{ TRAJECTORY_WINDOW_WEEKS }} weeks'
            WHEN week_number > max_week - {{ TRAJECTORY_WINDOW_WEEKS }} THEN 'Last {{ TRAJECTORY_WINDOW_WEEKS }} weeks'
        END AS period,
        SUM(panel_net_spend) AS panel_net_spend,
        SUM(active_households) AS active_households,
        SUM(baskets) AS baskets
    FROM mart_panel_weekly
    CROSS JOIN bounds
    WHERE week_number <= min_week + {{ TRAJECTORY_WINDOW_WEEKS }} - 1
       OR week_number > max_week - {{ TRAJECTORY_WINDOW_WEEKS }}
    GROUP BY 1
),
pivoted AS (
    SELECT
        MAX(CASE WHEN period LIKE 'First%' THEN panel_net_spend END) AS early_spend,
        MAX(CASE WHEN period LIKE 'Last%' THEN panel_net_spend END) AS late_spend,
        MAX(CASE WHEN period LIKE 'First%' THEN active_households END) AS early_households,
        MAX(CASE WHEN period LIKE 'Last%' THEN active_households END) AS late_households,
        MAX(CASE WHEN period LIKE 'First%' THEN baskets END) AS early_baskets,
        MAX(CASE WHEN period LIKE 'Last%' THEN baskets END) AS late_baskets
    FROM periods
),
measures AS (
    SELECT
        *,
        early_baskets / NULLIF(early_households, 0) AS early_trips,
        late_baskets / NULLIF(late_households, 0) AS late_trips,
        early_spend / NULLIF(early_baskets, 0) AS early_basket_value,
        late_spend / NULLIF(late_baskets, 0) AS late_basket_value,
        CASE
            WHEN early_spend > 0 AND late_spend > 0 AND early_spend <> late_spend
                THEN (late_spend - early_spend) / LN(late_spend / early_spend)
            WHEN early_spend > 0 AND late_spend > 0 THEN late_spend
        END AS log_mean_spend
    FROM pivoted
),
drivers AS (
    SELECT 'active_households' AS driver, early_households AS early_value, late_households AS late_value,
           log_mean_spend * LN(late_households / NULLIF(early_households, 0)) AS contribution FROM measures
    UNION ALL
    SELECT 'trips_per_active_household', early_trips, late_trips,
           log_mean_spend * LN(late_trips / NULLIF(early_trips, 0)) FROM measures
    UNION ALL
    SELECT 'spend_per_basket', early_basket_value, late_basket_value,
           log_mean_spend * LN(late_basket_value / NULLIF(early_basket_value, 0)) FROM measures
),
reconciled AS (
    SELECT
        d.*,
        m.late_spend - m.early_spend AS total_spend_change,
        SUM(d.contribution) OVER () AS summed_driver_contribution
    FROM drivers d
    CROSS JOIN measures m
)
SELECT
    'D01' AS decision_id,
    'Panel Spend Movement' AS case_name,
    driver,
    early_value,
    late_value,
    late_value / NULLIF(early_value, 0) - 1 AS relative_change,
    contribution,
    total_spend_change,
    summed_driver_contribution,
    summed_driver_contribution - total_spend_change AS reconciliation_delta,
    CASE WHEN ABS(summed_driver_contribution - total_spend_change) <= 0.01 THEN 'PASS' ELSE 'REVIEW' END AS reconciliation_status,
    'First and last observation windows; associative accounting decomposition only' AS limitation
FROM reconciled;
