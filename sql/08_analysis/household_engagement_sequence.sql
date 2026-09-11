CREATE OR REPLACE TABLE analysis_household_engagement_sequence AS
WITH sequence AS (
    SELECT
        household_key,
        week_number,
        net_spend,
        baskets,
        LAG(net_spend) OVER (PARTITION BY household_key ORDER BY week_number) AS prior_week_spend,
        LEAD(net_spend) OVER (PARTITION BY household_key ORDER BY week_number) AS next_week_spend,
        SUM(net_spend) OVER (
            PARTITION BY household_key
            ORDER BY week_number
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_household_spend
    FROM mart_household_weekly
),
ranked AS (
    SELECT
        *,
        RANK() OVER (PARTITION BY week_number ORDER BY net_spend DESC) AS weekly_spend_rank,
        DENSE_RANK() OVER (PARTITION BY week_number ORDER BY baskets DESC) AS weekly_frequency_rank
    FROM sequence
)
SELECT *
FROM ranked;