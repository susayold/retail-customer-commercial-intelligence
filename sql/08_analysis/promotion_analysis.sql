-- Promotion analysis is descriptive and preserves the product-store-week denominator.
CREATE OR REPLACE TABLE analysis_promotion_association AS
SELECT
    department,
    commodity,
    promo_state_group,
    SUM(product_store_weeks) AS product_store_weeks,
    SUM(panel_sales) AS panel_sales,
    SUM(panel_units) AS panel_units,
    SUM(panel_buying_households) AS panel_buying_households,
    SUM(panel_baskets) AS panel_baskets,
    SUM(panel_sales) / NULLIF(SUM(product_store_weeks), 0) AS avg_panel_sales_per_product_store_week,
    SUM(panel_baskets) / NULLIF(SUM(product_store_weeks), 0) AS avg_panel_baskets_per_product_store_week
FROM mart_promotion_category_week
GROUP BY department, commodity, promo_state_group;

CREATE OR REPLACE TABLE analysis_promotion_dependency AS
WITH category_totals AS (
    SELECT
        department,
        commodity,
        SUM(panel_sales) AS total_panel_sales,
        SUM(product_store_weeks) AS total_product_store_weeks,
        SUM(
            CASE
                WHEN promo_state_group IN ('display_only', 'mailer_only', 'display_and_mailer')
                THEN panel_sales
                ELSE 0
            END
        ) AS promoted_panel_sales,
        SUM(
            CASE
                WHEN promo_state_group IN ('display_only', 'mailer_only', 'display_and_mailer')
                THEN product_store_weeks
                ELSE 0
            END
        ) AS promoted_product_store_weeks
    FROM mart_promotion_category_week
    GROUP BY department, commodity
)
SELECT
    department,
    commodity,
    total_panel_sales,
    promoted_panel_sales,
    total_product_store_weeks,
    promoted_product_store_weeks,
    promoted_panel_sales / NULLIF(total_panel_sales, 0)
        AS share_of_observed_sales_during_promoted_states,
    promoted_product_store_weeks / NULLIF(total_product_store_weeks, 0)
        AS share_of_product_store_weeks_promoted,
    'Association only; no profitability or causal lift claim' AS interpretation_boundary
FROM category_totals;
