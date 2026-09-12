CREATE OR REPLACE TABLE mart_decision_alerts AS
WITH weekly AS (
    SELECT
        week_number,
        panel_net_spend,
        active_households,
        trips_per_household,
        spend_per_basket,
        LAG(panel_net_spend) OVER (ORDER BY week_number) AS prior_spend,
        LAG(active_households) OVER (ORDER BY week_number) AS prior_households,
        LAG(trips_per_household) OVER (ORDER BY week_number) AS prior_trips,
        LAG(spend_per_basket) OVER (ORDER BY week_number) AS prior_basket_value
    FROM mart_panel_weekly
)
SELECT
    'panel_net_spend_decline' AS metric,
    prior_spend AS baseline,
    panel_net_spend AS current,
    panel_net_spend - prior_spend AS absolute_variance,
    panel_net_spend / NULLIF(prior_spend, 0) - 1 AS relative_variance,
    -0.10 AS threshold,
    CASE
        WHEN panel_net_spend / NULLIF(prior_spend, 0) - 1 < -0.10 THEN 'high'
        ELSE 'normal'
    END AS severity,
    'observation_week=' || CAST(week_number AS VARCHAR) AS scope
FROM weekly
WHERE prior_spend IS NOT NULL
UNION ALL
SELECT
    'active_households_decline',
    prior_households,
    active_households,
    active_households - prior_households,
    active_households / NULLIF(prior_households, 0) - 1,
    -0.10,
    CASE
        WHEN active_households / NULLIF(prior_households, 0) - 1 < -0.10 THEN 'high'
        ELSE 'normal'
    END,
    'observation_week=' || CAST(week_number AS VARCHAR)
FROM weekly
WHERE prior_households IS NOT NULL
UNION ALL
SELECT
    'trip_frequency_decline',
    prior_trips,
    trips_per_household,
    trips_per_household - prior_trips,
    trips_per_household / NULLIF(prior_trips, 0) - 1,
    -0.10,
    CASE
        WHEN trips_per_household / NULLIF(prior_trips, 0) - 1 < -0.10 THEN 'medium'
        ELSE 'normal'
    END,
    'observation_week=' || CAST(week_number AS VARCHAR)
FROM weekly
WHERE prior_trips IS NOT NULL;
