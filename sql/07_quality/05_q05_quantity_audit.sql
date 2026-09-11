CREATE OR REPLACE TABLE qa_quantity_audit AS
SELECT
    COUNT(*) AS transaction_lines,
    SUM(CASE WHEN quantity_raw <= 0 THEN 1 ELSE 0 END) AS non_positive_quantity_rows,
    MIN(quantity_raw) AS min_quantity,
    MAX(quantity_raw) AS max_quantity,
    QUANTILE_CONT(quantity_raw, 0.50) AS p50_quantity,
    QUANTILE_CONT(quantity_raw, 0.95) AS p95_quantity,
    QUANTILE_CONT(quantity_raw, 0.99) AS p99_quantity,
    SUM(CASE WHEN quantity_outlier_flag THEN 1 ELSE 0 END) AS flagged_outlier_rows
FROM fct_transaction_line;
