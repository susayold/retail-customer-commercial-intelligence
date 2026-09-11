CREATE OR REPLACE TABLE analysis_category_decomposition AS
WITH bounds AS (
    SELECT MIN(week_number) AS min_week, MAX(week_number) AS max_week
    FROM mart_category_weekly
),
windowed AS (
    SELECT
        c.department,
        c.commodity,
        SUM(CASE WHEN c.week_number <= b.min_week + 12 THEN c.panel_net_spend ELSE 0 END) AS early_spend,
        SUM(CASE WHEN c.week_number > b.max_week - 13 THEN c.panel_net_spend ELSE 0 END) AS late_spend,
        SUM(CASE WHEN c.week_number <= b.min_week + 12 THEN c.buying_households ELSE 0 END) AS early_buying_household_week_records,
        SUM(CASE WHEN c.week_number > b.max_week - 13 THEN c.buying_households ELSE 0 END) AS late_buying_household_week_records,
        SUM(CASE WHEN c.week_number <= b.min_week + 12 THEN c.category_baskets ELSE 0 END) AS early_category_baskets,
        SUM(CASE WHEN c.week_number > b.max_week - 13 THEN c.category_baskets ELSE 0 END) AS late_category_baskets
    FROM mart_category_weekly c
    CROSS JOIN bounds b
    GROUP BY c.department, c.commodity
)
SELECT
    department,
    commodity,
    early_spend,
    late_spend,
    late_spend - early_spend AS spend_change,
    early_buying_household_week_records,
    late_buying_household_week_records,
    late_buying_household_week_records - early_buying_household_week_records AS household_record_change,
    early_category_baskets,
    late_category_baskets,
    late_category_baskets - early_category_baskets AS basket_change,
    CASE
        WHEN late_spend >= early_spend * 1.10 THEN 'Growing'
        WHEN late_spend <= early_spend * 0.90 THEN 'Declining'
        ELSE 'Stable'
    END AS category_trajectory
FROM windowed;