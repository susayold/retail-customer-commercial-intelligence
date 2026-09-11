CREATE OR REPLACE TABLE dim_household AS
WITH observed AS (
    SELECT DISTINCT household_key FROM stg_transaction WHERE household_key IS NOT NULL
),
demographic_one_row AS (
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (PARTITION BY household_key ORDER BY household_key) AS rn
        FROM stg_household_demographic d
    )
    WHERE rn = 1
)
SELECT
    o.household_key,
    d.age_desc,
    d.marital_status_code,
    d.income_desc,
    d.homeowner_desc,
    d.hh_comp_desc,
    d.household_size_desc,
    d.kid_category_desc,
    CASE WHEN d.household_key IS NOT NULL THEN TRUE ELSE FALSE END AS has_demographics
FROM observed o
LEFT JOIN demographic_one_row d USING (household_key);
