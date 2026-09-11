# Data-quality report template

This report is completed from Drive outputs after the source run. The planning counts in the attached blueprint are not treated as verified results.

## Required evidence

- raw_file_inventory.csv: eight files, size, rows, columns, header hash and load status;
- source_profile_summary.csv: types, nulls, distinct counts, numeric ranges;
- qa_source_reconciliation.csv: source counts and distinct keys;
- qa_key_audit.csv: duplicate counts at model grain;
- qa_grain_audit.csv: basket consistency checks;
- qa_discount_audit.csv: sign and value audit;
- qa_quantity_audit.csv: range, percentiles and outlier flags;
- qa_campaign_observability.csv: pre/during/post window availability;
- qa_demographic_coverage.csv: coverage and covered/uncovered comparison;
- powerbi_reconciliation.csv: SQL/DAX metric differences.

## Stop conditions

Business analysis stops when a source is missing, required columns drift, a mandatory key duplicates unexpectedly, a basket maps to multiple household/day/store values, campaign post-period is treated as zero without observability, or SQL/BI reconciliation exceeds tolerance.

## Interpretation

Do not delete anomalies before documenting them. Treat source scale from the blueprint as a planning expectation only. A result becomes verified only when the output exists in Drive and the corresponding code is committed to GitHub.
