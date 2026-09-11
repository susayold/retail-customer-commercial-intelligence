CREATE OR REPLACE TABLE qa_reference_coverage AS
SELECT
    'transaction_product_unmatched' AS audit_name,
    COUNT(*) AS violating_rows
FROM fct_transaction_line t
WHERE NOT EXISTS (
    SELECT 1
    FROM dim_product p
    WHERE p.product_id = t.product_id
)
UNION ALL
SELECT
    'promotion_product_unmatched',
    COUNT(*)
FROM fct_promotion_product_store_week ps
WHERE NOT EXISTS (
    SELECT 1
    FROM dim_product p
    WHERE p.product_id = ps.product_id
)
UNION ALL
SELECT
    'campaign_exposure_unmatched',
    COUNT(*)
FROM fct_campaign_exposure e
WHERE NOT EXISTS (
    SELECT 1
    FROM dim_campaign c
    WHERE c.campaign_id = e.campaign_id
)
UNION ALL
SELECT
    'coupon_redemption_unmatched',
    COUNT(*)
FROM fct_coupon_redemption r
WHERE NOT EXISTS (
    SELECT 1
    FROM dim_coupon c
    WHERE c.coupon_upc = r.coupon_upc
);