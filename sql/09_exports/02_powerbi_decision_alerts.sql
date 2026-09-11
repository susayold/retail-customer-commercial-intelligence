CREATE OR REPLACE TABLE export_powerbi_decision_alerts AS
SELECT *
FROM mart_decision_alerts
WHERE severity IN ('high', 'medium');