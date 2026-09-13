CREATE OR REPLACE TABLE qa_brand_domain AS
WITH expected AS (
    SELECT * FROM (VALUES ('PRIVATE'), ('NATIONAL')) AS values_table(brand_type)
),
observed AS (
    SELECT
        brand_type,
        COUNT(*) AS product_count
    FROM dim_product
    GROUP BY brand_type
),
transaction_rollup AS (
    SELECT
        p.brand_type,
        COUNT(t.product_id) AS transaction_rows,
        SUM(t.sales_value) AS panel_net_spend
    FROM fct_transaction_line t
    LEFT JOIN dim_product p USING (product_id)
    GROUP BY p.brand_type
),
domains AS (
    SELECT brand_type FROM expected
    UNION
    SELECT brand_type FROM observed
)
SELECT
    d.brand_type,
    COALESCE(o.product_count, 0)::BIGINT AS product_count,
    COALESCE(r.transaction_rows, 0)::BIGINT AS transaction_rows,
    COALESCE(r.panel_net_spend, 0)::DOUBLE AS panel_net_spend,
    d.brand_type IN (SELECT brand_type FROM expected) AS is_expected_domain,
    CASE
        WHEN d.brand_type IN (SELECT brand_type FROM expected)
             AND COALESCE(o.product_count, 0) > 0
        THEN 'pass'
        ELSE 'fail'
    END AS status
FROM domains d
LEFT JOIN observed o USING (brand_type)
LEFT JOIN transaction_rollup r USING (brand_type)
ORDER BY d.brand_type;
