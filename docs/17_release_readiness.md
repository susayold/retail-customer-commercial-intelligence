# Release readiness audit

The final tag is gated by a fail-closed audit. It is deliberately separate from the ordinary rebuild because root-cause findings, executive decisions, Power BI reconciliation and UAT are evidence artifacts that require human review after refresh.

Run only with Drive-backed paths. The normal rebuild must set `RETAIL_DRIVE_ROOT` and pass `--drive-root`; the storage gate fails closed if the roots are not underneath that explicit boundary:

~~~powershell
python -m src.release_readiness --artifact-root $env:RETAIL_ARTIFACT_ROOT --repo-root "."
~~~

The command writes 04_qa_reports/release_readiness.json to the Drive artifact root and exits non-zero while any check is missing or fails. It never writes raw or curated data into the repository.

## Required evidence

The audit requires:

- storage policy ready and blocking QA gate ready;
- inventory, schema, profile, QA run log, layer reconciliation and statistics outputs;
- all 31 declared Power BI exports;
- 04_qa_reports/powerbi_reconciliation.csv with the eight required metrics and pass status;
- 04_qa_reports/uat_results.csv with exactly one pass row for each stable ID UAT-01 through UAT-12 (missing, unexpected or duplicate IDs fail the audit);
- 04_qa_reports/root_cause_cases.csv with three completed cases, Drive evidence URI, run ID and limitation;
- 04_qa_reports/executive_decisions.csv with five completed decisions, Drive evidence URI, run ID and limitation;
- repository contracts for the three root-cause cases, five executive decisions, limitations, UAT, semantic model and governed measures.

The audit output is the release evidence index. It does not invent a finding, downgrade a failed QA result or treat a synthetic fixture as a real-data result.
