# Data-quality report template

This report is completed from Drive outputs after the source run. The planning counts in the attached blueprint are not treated as verified results.

## Required evidence

- storage_status.json: source completeness, required Drive artifact folders and repository artifact violations;
- qa_quality_gate.json: blocking key, grain, reference and layer-reconciliation decisions, plus retained anomaly warnings;
- raw_file_inventory.csv: eight files, size, rows, columns, header hash, content SHA-256, planning expectation/delta and load status;
- schema_validation.csv: required columns, missing columns, unexpected columns, duplicate headers and contract status;
- source_profile_summary.csv: types, row counts and column counts;
- source_null_profile.csv: null/blank rate, distinct count and min/max profile;
- source_cardinality.csv: per-column distinct count and cardinality ratio for key and reference profiling;
- qa_source_reconciliation.csv: source counts and distinct keys;
- qa_key_audit.csv: duplicate counts at model grain;
- qa_grain_audit.csv: basket consistency checks;
- qa_reference_coverage.csv: anti-join counts for unmatched product, promotion, campaign, household and coupon-bridge references;
- qa_discount_audit.csv: sign and value audit;
- qa_quantity_audit.csv: range, percentiles and outlier flags;
- qa_transaction_anomalies.csv: DAY/WEEK_NO range, sales, quantity, time and required-key anomalies;
- qa_layer_reconciliation.csv: raw → staging → fact row counts, household/basket populations and sales totals with pass/review status;
- qa_campaign_observability.csv: pre/during/post window availability;
- qa_demographic_coverage.csv: coverage and covered/uncovered behavior comparison;
- powerbi_reconciliation.csv: SQL/DAX metric differences;
- qa_run_log.csv: run_id, timestamp, QA file, rows read/written, duration, warnings and errors;
- pipeline_run.log: source/model run_id, timestamp, file, rows read/written, duration, warnings and errors.

## Stop conditions

Business analysis stops when a source is missing, required columns drift, a mandatory key duplicates unexpectedly, a reference anti-join is non-zero without an accepted exception, a basket maps to multiple household/day/store values, campaign pre/during/post is treated as zero without observability, or SQL/BI reconciliation exceeds tolerance.

## Interpretation

Do not delete anomalies before documenting them. Treat source scale from the blueprint as a planning expectation only. A result becomes verified only when the output exists in Drive and the corresponding code is committed to GitHub.
