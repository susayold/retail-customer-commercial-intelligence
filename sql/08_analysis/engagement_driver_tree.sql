CREATE OR REPLACE TABLE analysis_panel_driver_tree AS
WITH weekly AS (
    SELECT
        week_number,
        panel_net_spend,
        active_households,
        trips_per_household,
        spend_per_basket,
        AVG(panel_net_spend) OVER (
            ORDER BY week_number
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ) AS rolling_4w_panel_spend,
        SUM(panel_net_spend) OVER (
            ORDER BY week_number
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_panel_spend,
        LAG(panel_net_spend) OVER (ORDER BY week_number) AS prior_panel_net_spend,
        LAG(active_households) OVER (ORDER BY week_number) AS prior_active_households,
        LAG(trips_per_household) OVER (ORDER BY week_number) AS prior_trips_per_household,
        LAG(spend_per_basket) OVER (ORDER BY week_number) AS prior_spend_per_basket
    FROM mart_panel_weekly
)
SELECT
    *,
    active_households * trips_per_household * spend_per_basket AS reconstructed_panel_net_spend,
    panel_net_spend
        - active_households * trips_per_household * spend_per_basket AS driver_identity_delta,
    panel_net_spend / NULLIF(prior_panel_net_spend, 0) - 1 AS panel_spend_change_pct,
    active_households / NULLIF(prior_active_households, 0) - 1 AS active_household_change_pct,
    trips_per_household / NULLIF(prior_trips_per_household, 0) - 1 AS trip_frequency_change_pct,
    spend_per_basket / NULLIF(prior_spend_per_basket, 0) - 1 AS basket_value_change_pct
FROM weekly;