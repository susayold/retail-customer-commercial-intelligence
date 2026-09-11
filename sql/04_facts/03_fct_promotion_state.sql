CREATE OR REPLACE TABLE fct_promotion_product_store_week AS
SELECT DISTINCT
    product_id,
    store_id,
    week_number,
    display_code,
    mailer_code,
    is_on_display,
    is_in_mailer,
    promo_state_group
FROM stg_promotion_state;
