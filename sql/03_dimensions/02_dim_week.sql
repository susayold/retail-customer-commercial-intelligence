CREATE OR REPLACE TABLE dim_week AS
WITH bounds AS (
    SELECT
        COALESCE(MIN(week_number), 1) AS min_week,
        COALESCE(MAX(week_number), 102) AS max_week
    FROM stg_transaction
)
SELECT
    week_number,
    'Observation Week ' || CAST(week_number AS VARCHAR) AS observation_week,
    DATE '2020-01-01' + (week_number - 1) * INTERVAL '7 days' AS synthetic_week_start
FROM bounds, range(min_week, max_week + 1) AS r(week_number);
