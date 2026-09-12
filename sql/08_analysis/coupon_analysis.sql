-- Coupon analysis keeps bridge, redemption, basket and repeat-purchase grains separate.
CREATE OR REPLACE TABLE analysis_coupon_campaign AS
WITH exposure AS (
    SELECT
        campaign_id,
        MAX(campaign_type) AS campaign_type,
        COUNT(DISTINCT household_key) AS recipient_households
    FROM fct_campaign_exposure
    GROUP BY campaign_id
),
redemption AS (
    SELECT
        campaign_id,
        COUNT(*) AS redemption_events,
        COUNT(DISTINCT household_key) AS redeemer_households
    FROM fct_coupon_redemption
    GROUP BY campaign_id
),
mapping AS (
    SELECT
        campaign_id,
        COUNT(DISTINCT coupon_upc) AS linked_coupons,
        COUNT(DISTINCT product_id) AS linked_products
    FROM bridge_coupon_product_campaign
    GROUP BY campaign_id
)
SELECT
    e.campaign_id,
    e.campaign_type,
    e.recipient_households,
    COALESCE(r.redemption_events, 0) AS redemption_events,
    COALESCE(r.redeemer_households, 0) AS redeemer_households,
    COALESCE(r.redeemer_households, 0)
        / NULLIF(e.recipient_households, 0) AS redemption_rate,
    COALESCE(m.linked_coupons, 0) AS linked_coupons,
    COALESCE(m.linked_products, 0) AS linked_products,
    'Observed redemption; denominator is exposed panel households' AS interpretation_boundary
FROM exposure e
LEFT JOIN redemption r USING (campaign_id)
LEFT JOIN mapping m USING (campaign_id);

CREATE OR REPLACE TABLE analysis_coupon_segment AS
WITH recipients AS (
    SELECT
        e.campaign_id,
        MAX(e.campaign_type) AS campaign_type,
        COALESCE(s.segment, 'Unknown') AS customer_segment,
        COUNT(DISTINCT e.household_key) AS recipient_households
    FROM fct_campaign_exposure e
    LEFT JOIN mart_customer_segment s USING (household_key)
    GROUP BY e.campaign_id, COALESCE(s.segment, 'Unknown')
),
redeemers AS (
    SELECT
        r.campaign_id,
        COALESCE(s.segment, 'Unknown') AS customer_segment,
        COUNT(*) AS redemption_events,
        COUNT(DISTINCT r.household_key) AS redeemer_households
    FROM fct_coupon_redemption r
    LEFT JOIN mart_customer_segment s USING (household_key)
    GROUP BY r.campaign_id, COALESCE(s.segment, 'Unknown')
)
SELECT
    p.campaign_id,
    p.campaign_type,
    p.customer_segment,
    p.recipient_households,
    COALESCE(r.redeemer_households, 0) AS redeemer_households,
    COALESCE(r.redemption_events, 0) AS redemption_events,
    COALESCE(r.redeemer_households, 0)
        / NULLIF(p.recipient_households, 0) AS redemption_rate,
    'Observed segment redemption; recipient targeting bias applies' AS interpretation_boundary
FROM recipients p
LEFT JOIN redeemers r
  ON r.campaign_id = p.campaign_id
 AND r.customer_segment = p.customer_segment;

CREATE OR REPLACE TABLE analysis_coupon_category AS
WITH mapped AS (
    SELECT
        b.campaign_id,
        b.coupon_upc,
        b.product_id,
        COALESCE(NULLIF(TRIM(CAST(p.department AS VARCHAR)), ''), 'Unknown') AS department,
        COALESCE(NULLIF(TRIM(CAST(p.commodity AS VARCHAR)), ''), 'Unknown') AS commodity
    FROM bridge_coupon_product_campaign b
    LEFT JOIN dim_product p USING (product_id)
),
redemptions AS (
    SELECT
        campaign_id,
        coupon_upc,
        COUNT(DISTINCT redemption_event_id) AS redemption_events,
        COUNT(DISTINCT household_key) AS redeemer_households
    FROM fct_coupon_redemption
    GROUP BY campaign_id, coupon_upc
)
SELECT
    m.campaign_id,
    m.department,
    m.commodity,
    COUNT(DISTINCT m.coupon_upc) AS linked_coupons,
    COUNT(DISTINCT m.product_id) AS linked_products,
    COUNT(DISTINCT r.redemption_event_id) AS mapped_redemption_events,
    COUNT(DISTINCT r.household_key) AS mapped_redeemer_households,
    'Category-linked redemption; event counts are not additive across categories' AS interpretation_boundary
FROM mapped m
LEFT JOIN fct_coupon_redemption r
  ON r.campaign_id = m.campaign_id
 AND r.coupon_upc = m.coupon_upc
GROUP BY m.campaign_id, m.department, m.commodity;

CREATE OR REPLACE TABLE analysis_coupon_basket AS
SELECT
    COALESCE(segment, 'Unknown') AS customer_segment,
    CASE
        WHEN has_coupon_discount THEN 'Coupon-discounted'
        ELSE 'No-coupon-discount'
    END AS basket_type,
    COUNT(*) AS basket_count,
    COUNT(DISTINCT household_key) AS households,
    AVG(basket_net_spend) AS avg_basket_net_spend,
    MEDIAN(basket_net_spend) AS median_basket_net_spend,
    AVG(basket_distinct_products) AS avg_distinct_products,
    AVG(basket_line_count) AS avg_line_count,
    AVG(basket_coupon_discount) AS avg_coupon_discount,
    'Basket coupon flag; not exact redemption attribution' AS interpretation_boundary
FROM mart_basket
GROUP BY 1, 2;

CREATE OR REPLACE TABLE analysis_coupon_repeat_category AS
WITH coupon_category_days AS (
    SELECT DISTINCT
        t.household_key,
        COALESCE(NULLIF(TRIM(CAST(p.commodity AS VARCHAR)), ''), 'Unknown') AS commodity,
        t.day_key
    FROM fct_transaction_line t
    LEFT JOIN dim_product p USING (product_id)
    WHERE COALESCE(t.coupon_discount_value, 0)
        + COALESCE(t.coupon_match_discount_value, 0) > 0
),
first_observed AS (
    SELECT
        household_key,
        commodity,
        MIN(day_key) AS first_observed_coupon_day
    FROM coupon_category_days
    GROUP BY household_key, commodity
),
repeat_flags AS (
    SELECT
        f.household_key,
        f.commodity,
        f.first_observed_coupon_day,
        EXISTS (
            SELECT 1
            FROM fct_transaction_line t2
            LEFT JOIN dim_product p2 USING (product_id)
            WHERE t2.household_key = f.household_key
              AND t2.day_key > f.first_observed_coupon_day
              AND COALESCE(NULLIF(TRIM(CAST(p2.commodity AS VARCHAR)), ''), 'Unknown')
                    = f.commodity
        ) AS later_observed_category_purchase
    FROM first_observed f
)
SELECT
    commodity,
    COUNT(*) AS first_observed_coupon_households,
    COUNT(*) FILTER (WHERE later_observed_category_purchase) AS later_observed_repeat_households,
    COUNT(*) FILTER (WHERE later_observed_category_purchase)
        / NULLIF(COUNT(*), 0) AS observed_repeat_rate,
    'First observed coupon-discounted category purchase; not true acquisition or causal repeat' AS interpretation_boundary
FROM repeat_flags
GROUP BY commodity;
