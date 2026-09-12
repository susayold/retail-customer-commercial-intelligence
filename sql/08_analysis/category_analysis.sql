CREATE OR REPLACE TABLE analysis_category_penetration AS
WITH panel AS (
    SELECT COUNT(DISTINCT household_key) AS panel_households
    FROM dim_household
),
category AS (
    SELECT
        department,
        commodity,
        COUNT(DISTINCT household_key) AS buying_households,
        SUM(panel_net_spend) AS panel_net_spend,
        SUM(category_baskets) AS category_baskets,
        SUM(active_weeks) AS household_category_active_weeks,
        SUM(panel_net_spend) / NULLIF(SUM(category_baskets), 0)
            AS spend_per_category_basket,
        SUM(panel_net_spend) / NULLIF(COUNT(DISTINCT household_key), 0)
            AS spend_per_buying_household,
        SUM(category_baskets) / NULLIF(COUNT(DISTINCT household_key), 0)
            AS purchase_frequency_per_buying_household,
        SUM(discount_value)
            / NULLIF(SUM(panel_net_spend + discount_value), 0)
            AS discount_rate,
        SUM(coupon_baskets) / NULLIF(SUM(category_baskets), 0)
            AS coupon_basket_rate,
        SUM(private_label_spend) / NULLIF(SUM(panel_net_spend), 0)
            AS private_label_share
    FROM mart_category_household
    GROUP BY department, commodity
)
SELECT
    c.*,
    p.panel_households,
    c.buying_households / NULLIF(p.panel_households, 0)
        AS household_penetration
FROM category c
CROSS JOIN panel p;

CREATE OR REPLACE TABLE analysis_category_decomposition AS
WITH bounds AS (
    SELECT MIN(week_number) AS min_week, MAX(week_number) AS max_week
    FROM mart_category_weekly
),
category_period AS (
    SELECT
        p.department,
        p.commodity,
        CASE
            WHEN t.week_number <= b.min_week + 12 THEN 'Early'
            ELSE 'Late'
        END AS period,
        SUM(t.sales_value) AS spend,
        COUNT(DISTINCT t.household_key) AS buying_households,
        COUNT(DISTINCT t.basket_id) AS category_baskets
    FROM fct_transaction_line t
    LEFT JOIN dim_product p USING (product_id)
    CROSS JOIN bounds b
    WHERE t.week_number <= b.min_week + 12
       OR t.week_number > b.max_week - 13
    GROUP BY
        p.department,
        p.commodity,
        CASE
            WHEN t.week_number <= b.min_week + 12 THEN 'Early'
            ELSE 'Late'
        END
),
pivoted AS (
    SELECT
        department,
        commodity,
        MAX(CASE WHEN period = 'Early' THEN spend END) AS early_spend,
        MAX(CASE WHEN period = 'Late' THEN spend END) AS late_spend,
        MAX(CASE WHEN period = 'Early' THEN buying_households END)
            AS early_buying_households,
        MAX(CASE WHEN period = 'Late' THEN buying_households END)
            AS late_buying_households,
        MAX(CASE WHEN period = 'Early' THEN category_baskets END)
            AS early_category_baskets,
        MAX(CASE WHEN period = 'Late' THEN category_baskets END)
            AS late_category_baskets
    FROM category_period
    GROUP BY department, commodity
)
SELECT
    department,
    commodity,
    early_spend,
    late_spend,
    late_spend - early_spend AS spend_change,
    early_buying_households,
    late_buying_households,
    late_buying_households - early_buying_households
        AS buying_household_change,
    early_category_baskets,
    late_category_baskets,
    late_category_baskets - early_category_baskets AS basket_change,
    early_category_baskets / NULLIF(early_buying_households, 0)
        AS early_baskets_per_buying_household,
    late_category_baskets / NULLIF(late_buying_households, 0)
        AS late_baskets_per_buying_household,
    early_spend / NULLIF(early_category_baskets, 0)
        AS early_spend_per_category_basket,
    late_spend / NULLIF(late_category_baskets, 0)
        AS late_spend_per_category_basket,
    CASE
        WHEN early_spend IS NULL OR late_spend IS NULL THEN 'Insufficient History'
        WHEN early_spend = 0 AND late_spend > 0 THEN 'Emerging'
        WHEN late_spend >= early_spend * {{ TRAJECTORY_GROWING_FACTOR }} THEN 'Growing'
        WHEN late_spend <= early_spend * {{ TRAJECTORY_DECLINING_FACTOR }} THEN 'Declining'
        ELSE 'Stable'
    END AS category_trajectory
FROM pivoted;
