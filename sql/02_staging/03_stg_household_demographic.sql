CREATE OR REPLACE VIEW stg_household_demographic AS
SELECT
    CAST(household_key AS BIGINT) AS household_key,
    NULLIF(TRIM(CAST(classification_1 AS VARCHAR)), '') AS age_desc,
    NULLIF(TRIM(CAST(classification_2 AS VARCHAR)), '') AS marital_status_code,
    NULLIF(TRIM(CAST(classification_3 AS VARCHAR)), '') AS income_desc,
    NULLIF(TRIM(CAST(HOMEOWNER_DESC AS VARCHAR)), '') AS homeowner_desc,
    NULLIF(TRIM(CAST(classification_5 AS VARCHAR)), '') AS hh_comp_desc,
    NULLIF(TRIM(CAST(classification_4 AS VARCHAR)), '') AS household_size_desc,
    NULLIF(TRIM(CAST(KID_CATEGORY_DESC AS VARCHAR)), '') AS kid_category_desc
FROM raw_hh_demographic;
