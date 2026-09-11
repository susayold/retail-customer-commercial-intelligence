CREATE OR REPLACE TABLE qa_grain_audit AS
SELECT 'basket_household_consistency' AS audit_name,
       COUNT(*) AS violating_baskets
FROM (
    SELECT basket_id
    FROM fct_transaction_line
    GROUP BY basket_id
    HAVING COUNT(DISTINCT household_key) > 1
) x
UNION ALL
SELECT 'basket_day_consistency', COUNT(*)
FROM (
    SELECT basket_id
    FROM fct_transaction_line
    GROUP BY basket_id
    HAVING COUNT(DISTINCT day_key) > 1
) x
UNION ALL
SELECT 'basket_store_consistency', COUNT(*)
FROM (
    SELECT basket_id
    FROM fct_transaction_line
    GROUP BY basket_id
    HAVING COUNT(DISTINCT store_id) > 1
) x;
