-- Governed category key at department x commodity grain.
-- The key is deterministic and does not depend on row order.
CREATE OR REPLACE TABLE dim_category AS
SELECT
    COALESCE(NULLIF(TRIM(department), ''), 'Unknown') || '|' ||
        COALESCE(NULLIF(TRIM(commodity), ''), 'Unknown') AS category_key,
    COALESCE(NULLIF(TRIM(department), ''), 'Unknown') AS department,
    COALESCE(NULLIF(TRIM(commodity), ''), 'Unknown') AS commodity,
    COALESCE(NULLIF(TRIM(department), ''), 'Unknown') || ' / ' ||
        COALESCE(NULLIF(TRIM(commodity), ''), 'Unknown') AS category_label,
    'category_v1_department_commodity' AS rule_version
FROM dim_product
GROUP BY 1, 2, 3, 4, 5;
