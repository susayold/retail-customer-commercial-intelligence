CREATE OR REPLACE TABLE dim_store AS
SELECT DISTINCT store_id
FROM stg_transaction
WHERE store_id IS NOT NULL;
