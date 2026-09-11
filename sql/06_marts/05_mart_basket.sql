CREATE OR REPLACE TABLE mart_basket AS
SELECT
    b.*,
    s.segment
FROM fct_basket b
LEFT JOIN mart_customer_segment s USING (household_key);
