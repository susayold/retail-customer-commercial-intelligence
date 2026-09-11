CREATE OR REPLACE VIEW stg_campaign_exposure AS
SELECT DISTINCT
    CAST(household_key AS BIGINT) AS household_key,
    CAST(CAMPAIGN AS INTEGER) AS campaign_id
FROM raw_campaign_table;
