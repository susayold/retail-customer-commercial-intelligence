-- Keep exposure-level and unique-household campaign denominators separate.
CREATE OR REPLACE TABLE analysis_campaign_denominators AS
WITH base AS (
    SELECT
        campaign_id,
        campaign_type,
        COUNT(*) AS campaign_household_exposures,
        COUNT(DISTINCT household_key) AS unique_exposed_households,
        COUNT(*) FILTER (WHERE redeemed_coupon_flag) AS redeeming_exposures,
        COUNT(DISTINCT household_key) FILTER (WHERE redeemed_coupon_flag) AS unique_redeeming_households
    FROM mart_campaign_household
    GROUP BY campaign_id, campaign_type
),
rates AS (
    SELECT
        *,
        redeeming_exposures / NULLIF(campaign_household_exposures, 0) AS exposure_redemption_rate,
        unique_redeeming_households / NULLIF(unique_exposed_households, 0) AS unique_household_redemption_rate
    FROM base
)
SELECT
    *,
    CASE WHEN campaign_household_exposures > 0 THEN
        (exposure_redemption_rate + 1.96 * 1.96 / (2 * campaign_household_exposures)
            - 1.96 * SQRT((exposure_redemption_rate * (1 - exposure_redemption_rate)
                + 1.96 * 1.96 / (4 * campaign_household_exposures)) / campaign_household_exposures))
        / (1 + 1.96 * 1.96 / campaign_household_exposures) END AS exposure_rate_ci_low,
    CASE WHEN campaign_household_exposures > 0 THEN
        (exposure_redemption_rate + 1.96 * 1.96 / (2 * campaign_household_exposures)
            + 1.96 * SQRT((exposure_redemption_rate * (1 - exposure_redemption_rate)
                + 1.96 * 1.96 / (4 * campaign_household_exposures)) / campaign_household_exposures))
        / (1 + 1.96 * 1.96 / campaign_household_exposures) END AS exposure_rate_ci_high,
    CASE WHEN unique_exposed_households > 0 THEN
        (unique_household_redemption_rate + 1.96 * 1.96 / (2 * unique_exposed_households)
            - 1.96 * SQRT((unique_household_redemption_rate * (1 - unique_household_redemption_rate)
                + 1.96 * 1.96 / (4 * unique_exposed_households)) / unique_exposed_households))
        / (1 + 1.96 * 1.96 / unique_exposed_households) END AS unique_rate_ci_low,
    CASE WHEN unique_exposed_households > 0 THEN
        (unique_household_redemption_rate + 1.96 * 1.96 / (2 * unique_exposed_households)
            + 1.96 * SQRT((unique_household_redemption_rate * (1 - unique_household_redemption_rate)
                + 1.96 * 1.96 / (4 * unique_exposed_households)) / unique_exposed_households))
        / (1 + 1.96 * 1.96 / unique_exposed_households) END AS unique_rate_ci_high,
    'Exposure and unique-household rates are different estimands; response is observational' AS interpretation_boundary
FROM rates;
