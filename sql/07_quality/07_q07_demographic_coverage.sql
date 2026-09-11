CREATE OR REPLACE TABLE qa_demographic_coverage AS
SELECT
    COUNT(*) AS observed_households,
    SUM(CASE WHEN has_demographics THEN 1 ELSE 0 END) AS households_with_demographics,
    SUM(CASE WHEN NOT has_demographics THEN 1 ELSE 0 END) AS households_without_demographics,
    SUM(CASE WHEN has_demographics THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS demographic_coverage_pct
FROM dim_household;
