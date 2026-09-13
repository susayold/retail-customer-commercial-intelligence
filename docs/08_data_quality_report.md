# Data-quality report template

This report is completed from Drive outputs after the source run. The planning counts in the supplied blueprint are not treated as verified results.

## Readiness prerequisite

The data-quality workflow starts only after the Drive source gate reports READY. The prerequisite evidence is 06_source_docs/source_ready.json, source_provenance.json, source_checksums.csv, acquisition_manifest.json and acquisition_run.log. The raw layer must contain exactly the eight direct CSVs defined in src/source_manifest.py. GitHub Actions uses synthetic fixtures only and never downloads or stores production source records.

## Required evidence

- storage_status.json: storage_boundary_ready, source readiness status, required Drive artifact folders and repository artifact violations;
- source_ready.json: exact file count and checksum PASS marker;
- source_provenance.json: provider, landing/direct URL, acquisition time, archive metadata and per-file checksums;
- source_checksums.csv: file, size and SHA-256 values reconciled to raw;
- acquisition_manifest.json: run ID, staging location, raw state and promotion/NO_OP outcome;
- acquisition_run.log: acquisition events and failures;
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
- qa_brand_domain.csv: expected PRIVATE/NATIONAL domain counts and spend after brand normalization;
- qa_private_label_reconciliation.csv: independent raw semantic baseline reconciled to warehouse and export;
- qa_segment_integrity.csv and qa_segment_distribution.csv: one assignment per 2,500 households plus distribution;
- qa_private_label_summary.csv: private-label candidate versus final segment assignment and precedence note;
- powerbi_reconciliation.csv: SQL/DAX metric differences;
- qa_run_log.csv: run_id, timestamp, QA file, rows read/written, duration, warnings and errors;
- pipeline_run.log: source/model run_id, timestamp, file, rows read/written, duration, warnings and errors.

## Stop conditions

Business analysis stops when source readiness fails, a source is missing, required columns drift, a mandatory key duplicates unexpectedly, a reference anti-join is non-zero without an accepted exception, a basket maps to multiple household/day/store values, campaign pre/during/post is treated as zero without observability, or SQL/BI reconciliation exceeds tolerance.

The acquisition layer additionally fails closed on zero-byte sources, corrupt/non-ZIP official responses, unsafe ZIP paths or symlinks, duplicate expected basenames, unexpected CSV names, partial raw state, extra raw files, checksum mismatch and attempted writes outside the declared Drive root.

## Interpretation

Do not delete anomalies before documenting them. A result becomes verified only when the output exists in Drive and the corresponding code is committed to GitHub. The corrected run retains the three source anomaly groups (18,850 zero-sale rows, 14,466 non-positive-quantity rows and 39,872 quantity outliers) as review warnings. Promotion and campaign findings remain observational associations, not causal claims.
