CREATE OR REPLACE TABLE fct_campaign_exposure AS
WITH max_observation AS (
    SELECT COALESCE(MAX(day_key), 711) AS max_day FROM fct_transaction_line
)
SELECT DISTINCT
    e.household_key,
    e.campaign_id,
    c.campaign_type,
    c.start_day,
    c.end_day,
    c.end_day + 14 <= m.max_day AS post_14d_observable,
    c.end_day + 28 <= m.max_day AS post_28d_observable
FROM stg_campaign_exposure e
LEFT JOIN dim_campaign c USING (campaign_id)
CROSS JOIN max_observation m;
