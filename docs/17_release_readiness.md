# Release readiness audit

The final tag is gated by a fail-closed audit. It is deliberately separate from the ordinary rebuild because root-cause findings, executive decisions, Power BI reconciliation and UAT are evidence artifacts that require human review after refresh.

Run only with Drive-backed paths. The normal rebuild and every standalone data-writing stage must set `RETAIL_DRIVE_ROOT` and pass `--drive-root`; the storage gate fails closed if the mount is unavailable, the roots are not underneath that explicit boundary, or a path points into the repository:

~~~powershell
python -m src.release_readiness --artifact-root $env:RETAIL_ARTIFACT_ROOT --repo-root "." --drive-root $env:RETAIL_DRIVE_ROOT
~~~

The command writes 04_qa_reports/release_readiness.json to the Drive artifact root and exits non-zero while any check is missing or fails. It never writes raw or curated data into the repository.

## Required evidence

The audit requires:

- storage policy ready and blocking QA gate ready;
- inventory with exactly the eight expected filenames and `load_status=ok`, schema validation with exactly those filenames and `status=ok`, source profile/cardinality rows, a non-empty error-free QA run log, layer reconciliation and statistics outputs;
- all 31 declared Power BI exports;
- 04_qa_reports/powerbi_reconciliation.csv with exactly the eight required metrics and pass status;
- 04_qa_reports/uat_results.csv with exactly one pass row for each stable ID UAT-01 through UAT-12 (missing, unexpected or duplicate IDs fail the audit);
- 04_qa_reports/root_cause_cases.csv with three completed cases, Drive evidence URI, run ID and limitation;
- 04_qa_reports/executive_decisions.csv with five completed decisions, Drive evidence URI, run ID and limitation;
- repository contracts for the three root-cause cases, five executive decisions, limitations and UAT; the semantic model must validate as Drive-only with 29 curated tables, six pages, single-direction relationships, and all required governed measures present.

## SQL–Power BI reconciliation sequence

Complete the reconciliation only after the Drive-backed pipeline has run and Power BI has been refreshed:

~~~powershell
$env:RETAIL_SQL_RECONCILIATION = "$env:RETAIL_ARTIFACT_ROOT/04_qa_reports/sql_metric_totals.csv"
$env:RETAIL_BI_RECONCILIATION = "$env:RETAIL_ARTIFACT_ROOT/04_qa_reports/powerbi_metric_totals.csv"
make reconcile
~~~

Both input files and the generated `powerbi_reconciliation.csv` must be under the explicit Drive root. The target fails when a required metric is missing, duplicated, outside its tolerance, or has an invalid numeric value. The eight required metrics are Panel Net Spend, Baskets, Active Panel Households, Spend per Basket, Private Label Share, Campaign Recipients, Campaign Redeemers and Redemption Rate.

After reconciliation, complete the 12 UAT checks, three root-cause cases and five executive decision records with Drive evidence URIs, then run the release audit:

~~~powershell
make release-audit
~~~

Do not create tag `v1.0.0` until the audit returns pass. The audit output is the release evidence index. It does not invent a finding, downgrade a failed QA result or treat a synthetic fixture as a real-data result.
