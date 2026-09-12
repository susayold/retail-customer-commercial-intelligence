CREATE OR REPLACE TABLE fct_campaign_exposure AS
WITH observation_bounds AS (
    SELECT
        COALESCE(MIN(day_key), 1) AS min_day,
        COALESCE(MAX(day_key), 711) AS max_day
    FROM fct_transaction_line
)
SELECT DISTINCT
    e.household_key,
    e.campaign_id,
    c.campaign_type,
    c.start_day,
    c.end_day,
    c.start_day - 28 >= o.min_day AS pre_28d_observable,
    c.start_day >= o.min_day AND c.end_day <= o.max_day AS during_observable,
    c.end_day + 14 <= o.max_day AS post_14d_observable,
    c.end_day + 28 <= o.max_day AS post_28d_observable
FROM stg_campaign_exposure e
LEFT JOIN dim_campaign c USING (campaign_id)
CROSS JOIN observation_bounds o;
