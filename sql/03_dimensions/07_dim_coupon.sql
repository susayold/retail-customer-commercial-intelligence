CREATE OR REPLACE TABLE dim_coupon AS
SELECT DISTINCT coupon_upc
FROM (
    SELECT coupon_upc FROM stg_coupon_product
    UNION
    SELECT coupon_upc FROM stg_coupon_redemption
);
