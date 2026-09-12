CREATE OR REPLACE TABLE qa_layer_reconciliation AS
WITH checks AS (
    SELECT
        'transaction_raw_vs_staging' AS audit_name,
        'equal_rows_population_and_sales' AS reconciliation_rule,
        (SELECT COUNT(*) FROM raw_transaction_data)::BIGINT AS upstream_rows,
        (SELECT COUNT(*) FROM stg_transaction)::BIGINT AS downstream_rows,
        (SELECT COUNT(DISTINCT household_key) FROM raw_transaction_data)::BIGINT AS upstream_households,
        (SELECT COUNT(DISTINCT household_key) FROM stg_transaction)::BIGINT AS downstream_households,
        (SELECT COUNT(DISTINCT BASKET_ID) FROM raw_transaction_data)::BIGINT AS upstream_baskets,
        (SELECT COUNT(DISTINCT basket_id) FROM stg_transaction)::BIGINT AS downstream_baskets,
        (SELECT SUM(CAST(SALES_VALUE AS DOUBLE)) FROM raw_transaction_data)::DOUBLE AS upstream_sales,
        (SELECT SUM(sales_value) FROM stg_transaction)::DOUBLE AS downstream_sales
    UNION ALL
    SELECT
        'transaction_staging_vs_fact',
        'equal_rows_population_and_sales',
        (SELECT COUNT(*) FROM stg_transaction),
        (SELECT COUNT(*) FROM fct_transaction_line),
        (SELECT COUNT(DISTINCT household_key) FROM stg_transaction),
        (SELECT COUNT(DISTINCT household_key) FROM fct_transaction_line),
        (SELECT COUNT(DISTINCT basket_id) FROM stg_transaction),
        (SELECT COUNT(DISTINCT basket_id) FROM fct_transaction_line),
        (SELECT SUM(sales_value) FROM stg_transaction),
        (SELECT SUM(sales_value) FROM fct_transaction_line)
    UNION ALL
    SELECT
        'transaction_fact_vs_basket',
        'equal_population_and_sales_aggregation',
        (SELECT COUNT(*) FROM fct_transaction_line),
        (SELECT COUNT(*) FROM fct_basket),
        (SELECT COUNT(DISTINCT household_key) FROM fct_transaction_line),
        (SELECT COUNT(DISTINCT household_key) FROM fct_basket),
        (SELECT COUNT(DISTINCT basket_id) FROM fct_transaction_line),
        (SELECT COUNT(DISTINCT basket_id) FROM fct_basket),
        (SELECT SUM(sales_value) FROM fct_transaction_line),
        (SELECT SUM(basket_net_spend) FROM fct_basket)
    UNION ALL
    SELECT
        'causal_raw_vs_promotion_fact',
        'equal_rows',
        (SELECT COUNT(*) FROM raw_causal_data),
        (SELECT COUNT(*) FROM fct_promotion_product_store_week),
        NULL, NULL, NULL, NULL, NULL, NULL
    UNION ALL
    SELECT
        'redemption_raw_vs_fact',
        'equal_rows',
        (SELECT COUNT(*) FROM raw_coupon_redempt),
        (SELECT COUNT(*) FROM fct_coupon_redemption),
        (SELECT COUNT(DISTINCT household_key) FROM raw_coupon_redempt),
        (SELECT COUNT(DISTINCT household_key) FROM fct_coupon_redemption),
        NULL, NULL, NULL, NULL
    UNION ALL
    SELECT
        'campaign_exposure_raw_vs_fact',
        'equal_rows_and_population',
        (SELECT COUNT(*) FROM raw_campaign_table),
        (SELECT COUNT(*) FROM fct_campaign_exposure),
        (SELECT COUNT(DISTINCT household_key) FROM raw_campaign_table),
        (SELECT COUNT(DISTINCT household_key) FROM fct_campaign_exposure),
        NULL, NULL, NULL, NULL
    UNION ALL
    SELECT
        'campaign_desc_raw_vs_dimension',
        'equal_rows',
        (SELECT COUNT(*) FROM raw_campaign_desc),
        (SELECT COUNT(*) FROM dim_campaign),
        NULL, NULL, NULL, NULL, NULL, NULL
    UNION ALL
    SELECT
        'product_raw_vs_dimension',
        'deduplication_expected',
        (SELECT COUNT(*) FROM raw_product),
        (SELECT COUNT(*) FROM dim_product),
        NULL, NULL, NULL, NULL, NULL, NULL
    UNION ALL
    SELECT
        'coupon_raw_vs_bridge',
        'deduplication_expected',
        (SELECT COUNT(*) FROM raw_coupon),
        (SELECT COUNT(*) FROM bridge_coupon_product_campaign),
        NULL, NULL, NULL, NULL, NULL, NULL
)
SELECT
    audit_name,
    reconciliation_rule,
    upstream_rows,
    downstream_rows,
    downstream_rows - upstream_rows AS row_difference,
    upstream_households,
    downstream_households,
    downstream_households - upstream_households AS household_difference,
    upstream_baskets,
    downstream_baskets,
    downstream_baskets - upstream_baskets AS basket_difference,
    upstream_sales,
    downstream_sales,
    downstream_sales - upstream_sales AS sales_difference,
    CASE
        WHEN reconciliation_rule = 'equal_rows_population_and_sales'
             AND upstream_rows = downstream_rows
             AND upstream_households = downstream_households
             AND upstream_baskets = downstream_baskets
             AND ABS(COALESCE(downstream_sales, 0) - COALESCE(upstream_sales, 0)) <= 0.000001
            THEN 'pass'
        WHEN reconciliation_rule = 'equal_population_and_sales_aggregation'
             AND upstream_households = downstream_households
             AND upstream_baskets = downstream_baskets
             AND ABS(COALESCE(downstream_sales, 0) - COALESCE(upstream_sales, 0)) <= 0.000001
            THEN 'pass'
        WHEN reconciliation_rule = 'equal_rows'
             AND upstream_rows = downstream_rows
            THEN 'pass'
        WHEN reconciliation_rule = 'equal_rows_and_population'
             AND upstream_rows = downstream_rows
             AND upstream_households = downstream_households
            THEN 'pass'
        WHEN reconciliation_rule = 'deduplication_expected'
             AND downstream_rows <= upstream_rows
            THEN 'pass'
        ELSE 'review'
    END AS status
FROM checks;
