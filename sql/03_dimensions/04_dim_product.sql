CREATE OR REPLACE TABLE dim_product AS
SELECT
    product_id,
    MAX(manufacturer_id) AS manufacturer_id,
    MAX(department) AS department,
    MAX(brand_type_raw) AS brand_type_raw,
    MAX(brand_type) AS brand_type,
    MAX(commodity) AS commodity,
    MAX(sub_commodity) AS sub_commodity,
    MAX(product_size) AS product_size
FROM stg_product
GROUP BY product_id;
