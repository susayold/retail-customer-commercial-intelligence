-- Category-spend LMDI: buying households x frequency x spend per basket.
CREATE OR REPLACE TABLE analysis_category_lmdi AS
WITH valid AS (
    SELECT
        category_key,
        department,
        commodity,
        early_spend,
        late_spend,
        late_spend - early_spend AS spend_change,
        early_buying_households,
        late_buying_households,
        early_category_baskets / NULLIF(early_buying_households, 0) AS early_frequency,
        late_category_baskets / NULLIF(late_buying_households, 0) AS late_frequency,
        early_spend / NULLIF(early_category_baskets, 0) AS early_basket_value,
        late_spend / NULLIF(late_category_baskets, 0) AS late_basket_value
    FROM analysis_category_materiality
),
eligible AS (
    SELECT
        v.*,
        CASE
            WHEN late_spend = early_spend THEN early_spend
            ELSE (late_spend - early_spend) / NULLIF(LN(late_spend) - LN(early_spend), 0)
        END AS spend_log_mean
    FROM valid v
    WHERE early_spend > 0
      AND late_spend > 0
      AND early_buying_households > 0
      AND late_buying_households > 0
      AND early_frequency > 0
      AND late_frequency > 0
      AND early_basket_value > 0
      AND late_basket_value > 0
),
decomposed AS (
    SELECT
        category_key,
        department,
        commodity,
        early_spend,
        late_spend,
        spend_change,
        spend_log_mean * LN(late_buying_households / early_buying_households) AS buying_households_contribution,
        spend_log_mean * LN(late_frequency / early_frequency) AS frequency_contribution,
        spend_log_mean * LN(late_basket_value / early_basket_value) AS basket_value_contribution
    FROM eligible
)
SELECT
    category_key,
    department,
    commodity,
    early_spend,
    late_spend,
    spend_change,
    buying_households_contribution,
    frequency_contribution,
    basket_value_contribution,
    buying_households_contribution + frequency_contribution + basket_value_contribution AS contribution_sum,
    spend_change - (buying_households_contribution + frequency_contribution + basket_value_contribution) AS reconciliation_delta,
    CASE WHEN ABS(spend_change - (buying_households_contribution + frequency_contribution + basket_value_contribution)) < 0.01 THEN 'PASS' ELSE 'REVIEW' END AS reconciliation_status,
    'Associative LMDI decomposition only; not causal attribution.' AS interpretation_boundary
FROM decomposed
UNION ALL
SELECT
    category_key,
    department,
    commodity,
    early_spend,
    late_spend,
    late_spend - early_spend,
    NULL::DOUBLE,
    NULL::DOUBLE,
    NULL::DOUBLE,
    NULL::DOUBLE,
    NULL::DOUBLE,
    'NOT_APPLICABLE',
    'Non-positive or incomplete component; LMDI withheld rather than fabricated.'
FROM valid
WHERE NOT (
    early_spend > 0 AND late_spend > 0
    AND early_buying_households > 0 AND late_buying_households > 0
    AND early_frequency > 0 AND late_frequency > 0
    AND early_basket_value > 0 AND late_basket_value > 0
);
