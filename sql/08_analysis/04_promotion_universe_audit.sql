-- Audit whether the source contains a valid unpromoted product-store-week state.
CREATE OR REPLACE TABLE analysis_promotion_universe_audit AS
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE promo_state_group = 'none') AS none_rows,
    COUNT(*) FILTER (WHERE promo_state_group = 'display_only') AS display_only_rows,
    COUNT(*) FILTER (WHERE promo_state_group = 'mailer_only') AS mailer_only_rows,
    COUNT(*) FILTER (WHERE promo_state_group = 'display_and_mailer') AS display_and_mailer_rows,
    COUNT(DISTINCT product_id) AS products,
    COUNT(DISTINCT store_id) AS stores,
    COUNT(DISTINCT week_number) AS weeks,
    CASE WHEN COUNT(*) FILTER (WHERE promo_state_group = 'none') > 0 THEN 'RECOVERED' ELSE 'NOT_OBSERVED' END AS none_state_status,
    CASE WHEN COUNT(*) FILTER (WHERE promo_state_group = 'none') > 0
        THEN 'Observed states include none; comparative tests may use it as a reference with sample sizes visible'
        ELSE 'Promotion analysis is restricted to observed modeled promotion states; no no-promo uplift claim is allowed'
    END AS interpretation_boundary
FROM fct_promotion_product_store_week;
