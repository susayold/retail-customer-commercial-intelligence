-- Commercial materiality ranking for category erosion (runs before LMDI).
-- The score is a documented prioritization heuristic, not causal impact.
CREATE OR REPLACE TABLE analysis_category_materiality AS
WITH bounds AS (
    SELECT MIN(week_number) AS min_week, MAX(week_number) AS max_week
    FROM mart_category_household_weekly
),
active_windows AS (
    SELECT
        COUNT(DISTINCT CASE WHEN week_number <= b.min_week + {{ TRAJECTORY_WINDOW_WEEKS }} - 1 THEN household_key END) AS early_active_households,
        COUNT(DISTINCT CASE WHEN week_number > b.max_week - {{ TRAJECTORY_WINDOW_WEEKS }} THEN household_key END) AS late_active_households
    FROM mart_household_weekly h
    CROSS JOIN bounds b
),
category_windows AS (
    SELECT
        c.category_key,
        c.department,
        c.commodity,
        SUM(CASE WHEN c.week_number <= b.min_week + {{ TRAJECTORY_WINDOW_WEEKS }} - 1 THEN c.panel_net_spend ELSE 0 END) AS early_spend,
        SUM(CASE WHEN c.week_number > b.max_week - {{ TRAJECTORY_WINDOW_WEEKS }} THEN c.panel_net_spend ELSE 0 END) AS late_spend,
        COUNT(DISTINCT CASE WHEN c.week_number <= b.min_week + {{ TRAJECTORY_WINDOW_WEEKS }} - 1 THEN c.household_key END) AS early_buying_households,
        COUNT(DISTINCT CASE WHEN c.week_number > b.max_week - {{ TRAJECTORY_WINDOW_WEEKS }} THEN c.household_key END) AS late_buying_households,
        SUM(CASE WHEN c.week_number <= b.min_week + {{ TRAJECTORY_WINDOW_WEEKS }} - 1 THEN c.category_baskets ELSE 0 END) AS early_category_baskets,
        SUM(CASE WHEN c.week_number > b.max_week - {{ TRAJECTORY_WINDOW_WEEKS }} THEN c.category_baskets ELSE 0 END) AS late_category_baskets
    FROM mart_category_household_weekly c
    CROSS JOIN bounds b
    WHERE c.week_number <= b.min_week + {{ TRAJECTORY_WINDOW_WEEKS }} - 1
       OR c.week_number > b.max_week - {{ TRAJECTORY_WINDOW_WEEKS }}
    GROUP BY c.category_key, c.department, c.commodity
),
metrics AS (
    SELECT
        c.*,
        late_spend - early_spend AS spend_change,
        late_buying_households - early_buying_households AS buying_household_change,
        late_category_baskets - early_category_baskets AS basket_change,
        early_buying_households / NULLIF(a.early_active_households, 0) AS early_penetration,
        late_buying_households / NULLIF(a.late_active_households, 0) AS late_penetration,
        early_category_baskets / NULLIF(early_buying_households, 0) AS early_baskets_per_buying_household,
        late_category_baskets / NULLIF(late_buying_households, 0) AS late_baskets_per_buying_household,
        early_spend / NULLIF(early_category_baskets, 0) AS early_spend_per_category_basket,
        late_spend / NULLIF(late_category_baskets, 0) AS late_spend_per_category_basket
    FROM category_windows c
    CROSS JOIN active_windows a
),
losses AS (
    SELECT
        m.*,
        GREATEST(0, -spend_change) AS spend_loss,
        GREATEST(0, -buying_household_change) AS buying_household_loss,
        GREATEST(0, early_penetration - late_penetration) AS penetration_loss,
        GREATEST(0, early_baskets_per_buying_household - late_baskets_per_buying_household) AS frequency_loss,
        GREATEST(0, early_spend_per_category_basket - late_spend_per_category_basket) AS basket_value_loss
    FROM metrics m
),
normalized AS (
    SELECT
        l.*,
        spend_loss / NULLIF(SUM(spend_loss) OVER (), 0) AS spend_loss_share,
        buying_household_loss / NULLIF(SUM(buying_household_loss) OVER (), 0) AS buying_household_loss_share,
        penetration_loss / NULLIF(SUM(penetration_loss) OVER (), 0) AS penetration_loss_share,
        frequency_loss / NULLIF(SUM(frequency_loss) OVER (), 0) AS frequency_loss_share,
        basket_value_loss / NULLIF(SUM(basket_value_loss) OVER (), 0) AS basket_value_loss_share
    FROM losses l
),
scored AS (
    SELECT
        n.*,
        {{ MATERIALITY_SPEND_LOSS_WEIGHT }} * COALESCE(spend_loss_share, 0)
            + {{ MATERIALITY_BUYING_HOUSEHOLD_LOSS_WEIGHT }} * COALESCE(buying_household_loss_share, 0)
            + {{ MATERIALITY_PENETRATION_LOSS_WEIGHT }} * COALESCE(penetration_loss_share, 0)
            + {{ MATERIALITY_FREQUENCY_LOSS_WEIGHT }} * COALESCE(frequency_loss_share, 0)
            + {{ MATERIALITY_BASKET_VALUE_LOSS_WEIGHT }} * COALESCE(basket_value_loss_share, 0)
            AS commercial_materiality_score
    FROM normalized n
)
SELECT
    *,
    RANK() OVER (ORDER BY commercial_materiality_score DESC, ABS(spend_change) DESC) AS commercial_materiality_rank,
    'Score is a documented prioritization heuristic, not causal impact or margin.' AS interpretation_boundary
FROM scored;
