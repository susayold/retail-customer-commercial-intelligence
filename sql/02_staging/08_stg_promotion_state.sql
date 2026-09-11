CREATE OR REPLACE VIEW stg_promotion_state AS
SELECT
    CAST(PRODUCT_ID AS BIGINT) AS product_id,
    CAST(STORE_ID AS BIGINT) AS store_id,
    CAST(WEEK_NO AS INTEGER) AS week_number,
    CAST(display AS VARCHAR) AS display_code,
    CAST(mailer AS VARCHAR) AS mailer_code,
    CASE WHEN CAST(display AS VARCHAR) <> '0' THEN TRUE ELSE FALSE END AS is_on_display,
    CASE WHEN CAST(mailer AS VARCHAR) <> '0' THEN TRUE ELSE FALSE END AS is_in_mailer,
    CASE
        WHEN CAST(display AS VARCHAR) = '0' AND CAST(mailer AS VARCHAR) = '0' THEN 'none'
        WHEN CAST(display AS VARCHAR) <> '0' AND CAST(mailer AS VARCHAR) = '0' THEN 'display_only'
        WHEN CAST(display AS VARCHAR) = '0' AND CAST(mailer AS VARCHAR) <> '0' THEN 'mailer_only'
        ELSE 'display_and_mailer'
    END AS promo_state_group
FROM raw_causal_data;
