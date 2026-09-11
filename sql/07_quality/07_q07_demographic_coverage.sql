CREATE OR REPLACE TABLE qa_demographic_coverage AS
WITH behavior AS (
    SELECT
        h.has_demographics,
        COUNT(*) AS households,
        AVG(s.observed_lifetime_spend) AS avg_observed_lifetime_spend,
        AVG(s.frequency_baskets) AS avg_frequency_baskets
    FROM dim_household h
    LEFT JOIN mart_household_summary s
        ON s.household_key = h.household_key
    GROUP BY h.has_demographics
),
coverage AS (
    SELECT
        COUNT(*) AS observed_households,
        SUM(CASE WHEN has_demographics THEN 1 ELSE 0 END) AS households_with_demographics,
        SUM(CASE WHEN NOT has_demographics THEN 1 ELSE 0 END) AS households_without_demographics,
        SUM(CASE WHEN has_demographics THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS demographic_coverage_pct
    FROM dim_household
)
SELECT
    c.*,
    covered.avg_observed_lifetime_spend AS avg_spend_covered,
    uncovered.avg_observed_lifetime_spend AS avg_spend_uncovered,
    covered.avg_frequency_baskets AS avg_baskets_covered,
    uncovered.avg_frequency_baskets AS avg_baskets_uncovered
FROM coverage c
LEFT JOIN behavior covered ON covered.has_demographics
LEFT JOIN behavior uncovered ON NOT uncovered.has_demographics;
