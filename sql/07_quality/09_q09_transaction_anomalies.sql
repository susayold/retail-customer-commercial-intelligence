CREATE OR REPLACE TABLE qa_transaction_anomalies AS
SELECT
    'day_range' AS audit_name,
    CAST(MIN(day_key) AS VARCHAR) AS observed_min,
    CAST(MAX(day_key) AS VARCHAR) AS observed_max,
    SUM(CASE WHEN day_key IS NULL OR day_key < 1 OR day_key > 711 THEN 1 ELSE 0 END) AS violating_rows,
    'DAY must be a positive observation index; 1–711 is the planning range; retain and review deviations' AS rule
FROM fct_transaction_line
UNION ALL
SELECT
    'week_range',
    CAST(MIN(week_number) AS VARCHAR),
    CAST(MAX(week_number) AS VARCHAR),
    SUM(CASE WHEN week_number IS NULL OR week_number < 1 OR week_number > 102 THEN 1 ELSE 0 END),
    'WEEK_NO must be a positive observation index; 1–102 is the planning range; retain and review deviations'
FROM fct_transaction_line
UNION ALL
SELECT
    'sales_negative',
    CAST(MIN(sales_value) AS VARCHAR),
    CAST(MAX(sales_value) AS VARCHAR),
    SUM(CASE WHEN sales_value < 0 THEN 1 ELSE 0 END),
    'Investigate negative SALES_VALUE; never delete before review'
FROM fct_transaction_line
UNION ALL
SELECT
    'sales_zero',
    CAST(MIN(sales_value) AS VARCHAR),
    CAST(MAX(sales_value) AS VARCHAR),
    SUM(CASE WHEN sales_value = 0 THEN 1 ELSE 0 END),
    'Retain zero SALES_VALUE rows and explain their context'
FROM fct_transaction_line
UNION ALL
SELECT
    'quantity_non_positive',
    CAST(MIN(quantity_raw) AS VARCHAR),
    CAST(MAX(quantity_raw) AS VARCHAR),
    SUM(CASE WHEN quantity_raw IS NULL OR quantity_raw <= 0 THEN 1 ELSE 0 END),
    'Preserve raw quantity and flag non-positive values'
FROM fct_transaction_line
UNION ALL
SELECT
    'quantity_outlier',
    CAST(MIN(quantity_raw) AS VARCHAR),
    CAST(MAX(quantity_raw) AS VARCHAR),
    SUM(CASE WHEN quantity_outlier_flag THEN 1 ELSE 0 END),
    'Use percentile flag; never silently cap source quantity'
FROM fct_transaction_line
UNION ALL
SELECT
    'trans_time_invalid',
    CAST(MIN(trans_time) AS VARCHAR),
    CAST(MAX(trans_time) AS VARCHAR),
    SUM(
        CASE
            WHEN trans_time IS NULL
              OR trans_time < 0
              OR trans_time > 2359
              OR trans_time % 100 > 59
            THEN 1
            ELSE 0
        END
    ),
    'TRANS_TIME must be a valid HHMM observation'
FROM fct_transaction_line
UNION ALL
SELECT
    'missing_product',
    CAST(NULL AS VARCHAR),
    CAST(NULL AS VARCHAR),
    SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END),
    'PRODUCT_ID is required for line-level product analysis'
FROM fct_transaction_line
UNION ALL
SELECT
    'missing_household',
    CAST(NULL AS VARCHAR),
    CAST(NULL AS VARCHAR),
    SUM(CASE WHEN household_key IS NULL THEN 1 ELSE 0 END),
    'household_key is required for panel and customer analysis'
FROM fct_transaction_line
UNION ALL
SELECT
    'missing_basket',
    CAST(NULL AS VARCHAR),
    CAST(NULL AS VARCHAR),
    SUM(CASE WHEN basket_id IS NULL THEN 1 ELSE 0 END),
    'basket_id is required for trip and basket analysis'
FROM fct_transaction_line;
