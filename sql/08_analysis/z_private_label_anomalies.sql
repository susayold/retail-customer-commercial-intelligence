-- Do not cap or silently repair impossible private-label shares.
CREATE OR REPLACE TABLE analysis_private_label_anomalies AS
SELECT
    department,
    commodity,
    private_label_spend,
    category_spend,
    private_label_share,
    CASE
        WHEN private_label_share < 0 THEN 'share_below_zero'
        WHEN private_label_share > 1 THEN 'share_above_one'
        WHEN category_spend <= 0 THEN 'non_positive_denominator'
        ELSE 'review'
    END AS anomaly_type,
    'Review returns, negative net sales, brand mapping and denominator; no auto-cap applied.' AS limitation
FROM analysis_private_label
WHERE private_label_share < 0
   OR private_label_share > 1
   OR category_spend <= 0;

