CREATE OR REPLACE TABLE fct_promotion_product_store_week AS
WITH aggregated AS (
    SELECT
        product_id,
        store_id,
        week_number,
        MAX(CASE WHEN is_on_display THEN 1 ELSE 0 END) = 1 AS is_on_display,
        MAX(CASE WHEN is_in_mailer THEN 1 ELSE 0 END) = 1 AS is_in_mailer,
        MAX(CASE WHEN is_on_display THEN display_code ELSE '0' END) AS display_code,
        MAX(CASE WHEN is_in_mailer THEN mailer_code ELSE '0' END) AS mailer_code
    FROM stg_promotion_state
    GROUP BY product_id, store_id, week_number
)
SELECT
    product_id,
    store_id,
    week_number,
    display_code,
    mailer_code,
    is_on_display,
    is_in_mailer,
    CASE
        WHEN NOT is_on_display AND NOT is_in_mailer THEN 'none'
        WHEN is_on_display AND NOT is_in_mailer THEN 'display_only'
        WHEN NOT is_on_display AND is_in_mailer THEN 'mailer_only'
        ELSE 'display_and_mailer'
    END AS promo_state_group
FROM aggregated;
