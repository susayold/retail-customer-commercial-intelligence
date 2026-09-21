-- Governed segment dimension. Assignment logic remains in mart_customer_segment.
CREATE OR REPLACE TABLE dim_segment AS
SELECT * FROM (VALUES
    ('High-Value Declining', 1, 'High observed spend with declining late-window spend', 'v1_deterministic'),
    ('High-Value Engaged', 2, 'High observed spend with growing or stable late-window spend', 'v1_deterministic'),
    ('Frequent Core', 3, 'High basket frequency outside the high-monetary group', 'v1_deterministic'),
    ('Promotion-Responsive', 4, 'High observed coupon-basket or discount share', 'v1_deterministic'),
    ('Private-Label Loyal', 5, 'High observed private-label spend share', 'v1_deterministic'),
    ('Occasional', 6, 'Low frequency and limited active-week history', 'v1_deterministic'),
    ('Low-Engagement', 7, 'Observed households not assigned to a higher-priority rule', 'v1_deterministic')
) AS t(segment, segment_order, description, rule_version);
