CREATE OR REPLACE TABLE qa_campaign_observability AS
SELECT
    campaign_id,
    COUNT(*) AS recipient_rows,
    SUM(CASE WHEN post_14d_observable THEN 1 ELSE 0 END) AS post_14d_observable_rows,
    SUM(CASE WHEN post_28d_observable THEN 1 ELSE 0 END) AS post_28d_observable_rows,
    MIN(start_day) AS start_day,
    MAX(end_day) AS end_day
FROM fct_campaign_exposure
GROUP BY campaign_id;
