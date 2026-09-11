CREATE OR REPLACE TABLE dim_day AS
WITH bounds AS (
    SELECT
        COALESCE(MIN(day_key), 1) AS min_day,
        COALESCE(MAX(day_key), 711) AS max_day
    FROM stg_transaction
)
SELECT
    day_key,
    'Observation Day ' || CAST(day_key AS VARCHAR) AS observation_day,
    DATE '2020-01-01' + (day_key - 1) * INTERVAL '1 day' AS synthetic_date
FROM bounds, range(min_day, max_day + 1) AS r(day_key);
