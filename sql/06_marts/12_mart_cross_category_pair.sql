CREATE OR REPLACE TABLE mart_cross_category_pair AS
WITH basket_commodity AS (
    SELECT DISTINCT
        t.basket_id,
        p.commodity
    FROM fct_transaction_line t
    JOIN dim_product p USING (product_id)
    WHERE p.commodity IS NOT NULL
),
pairs AS (
    SELECT
        a.basket_id,
        a.commodity AS commodity_a,
        b.commodity AS commodity_b
    FROM basket_commodity a
    JOIN basket_commodity b
      ON a.basket_id = b.basket_id
     AND a.commodity < b.commodity
),
basket_counts AS (
    SELECT COUNT(DISTINCT basket_id) AS total_baskets FROM fct_basket
),
category_counts AS (
    SELECT commodity, COUNT(DISTINCT basket_id) AS baskets_with_commodity
    FROM basket_commodity
    GROUP BY commodity
),
pair_counts AS (
    SELECT commodity_a, commodity_b, COUNT(DISTINCT basket_id) AS pair_baskets
    FROM pairs
    GROUP BY commodity_a, commodity_b
)
SELECT
    p.commodity_a,
    p.commodity_b,
    p.pair_baskets,
    p.pair_baskets / NULLIF(b.total_baskets, 0) AS support,
    p.pair_baskets / NULLIF(a.baskets_with_commodity, 0) AS confidence_a_to_b,
    (p.pair_baskets / NULLIF(a.baskets_with_commodity, 0))
        / NULLIF(bc.baskets_with_commodity / NULLIF(bc2.total_baskets, 0), 0) AS lift_a_to_b
FROM pair_counts p
CROSS JOIN basket_counts b
JOIN category_counts a ON a.commodity = p.commodity_a
JOIN category_counts bc ON bc.commodity = p.commodity_b
CROSS JOIN basket_counts bc2
WHERE p.pair_baskets >= 100
  AND p.pair_baskets / NULLIF(b.total_baskets, 0) >= 0.01;
