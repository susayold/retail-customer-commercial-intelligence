-- Available demographic coverage only. Unknown is preserved, not imputed.
CREATE OR REPLACE TABLE analysis_demographic_summary AS
WITH base AS (
    SELECT
        h.household_key,
        s.observed_lifetime_spend,
        h.age_desc,
        h.marital_status_code,
        h.income_desc,
        h.homeowner_desc,
        h.hh_comp_desc,
        h.household_size_desc,
        h.kid_category_desc
    FROM dim_household h
    LEFT JOIN mart_household_summary s USING (household_key)
),
long_values AS (
    SELECT 'age_desc' AS attribute_name, COALESCE(age_desc, 'Unknown') AS attribute_value, household_key, observed_lifetime_spend FROM base
    UNION ALL SELECT 'marital_status_code', COALESCE(marital_status_code, 'Unknown'), household_key, observed_lifetime_spend FROM base
    UNION ALL SELECT 'income_desc', COALESCE(income_desc, 'Unknown'), household_key, observed_lifetime_spend FROM base
    UNION ALL SELECT 'homeowner_desc', COALESCE(homeowner_desc, 'Unknown'), household_key, observed_lifetime_spend FROM base
    UNION ALL SELECT 'hh_comp_desc', COALESCE(hh_comp_desc, 'Unknown'), household_key, observed_lifetime_spend FROM base
    UNION ALL SELECT 'household_size_desc', COALESCE(household_size_desc, 'Unknown'), household_key, observed_lifetime_spend FROM base
    UNION ALL SELECT 'kid_category_desc', COALESCE(kid_category_desc, 'Unknown'), household_key, observed_lifetime_spend FROM base
)
SELECT
    attribute_name,
    attribute_value,
    COUNT(DISTINCT household_key) AS households,
    SUM(observed_lifetime_spend) AS observed_lifetime_spend,
    COUNT(DISTINCT household_key) / NULLIF((SELECT COUNT(DISTINCT household_key) FROM base), 0) AS household_coverage,
    'Descriptive demographic coverage only; no imputation or causal interpretation.' AS interpretation_boundary
FROM long_values
GROUP BY attribute_name, attribute_value;

