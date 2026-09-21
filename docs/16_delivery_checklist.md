# Delivery checklist

This checklist separates implemented repository work from outputs that require the eight real source CSVs in Drive.

| Step | Plan item | Status | Evidence / next action |
|---:|---|---|---|
| 01 | Create repo | Done | GitHub repository on main |
| 02 | Download data | Done — verified | Official dunnhumby package manually staged on D, promoted to Drive 01_raw_source, 8/8 exact files, checksum PASS |
| 03 | Inventory files | Done — verified | src/inventory.py + storage_status.json; Drive QA inventory has 8/8 `load_status=ok` |
| 04 | Validate schemas | Done — verified | src/schema_contracts.py + config/source_contracts.yaml; 8/8 status `ok` |
| 05 | Profile sources | Done — verified | src.profile_sources.py; row/type/null/distinct/range/cardinality outputs on Drive |
| 06 | Document grain | Done | docs/04_grain_and_join_contracts.md, docs/05_data_model.md |
| 07 | Document join risks | Done | docs/04_grain_and_join_contracts.md |
| 08 | Convert CSV to Parquet | Done — verified | 8 Parquet source outputs created in Drive-backed staging and uploaded to Drive; lineage metadata is attached per row |
| 09 | Initialize DuckDB | Done — verified | DuckDB warehouse and marts created; pipeline log records model row counts |
| 10–16 | Build staging, dimensions, facts, bridge | Implemented and smoke-tested | sql/02_staging through sql/05_bridges |
| 17 | Run QA | Done — verified | QA gate `READY`; source-contract, key/grain/reference/layer checks pass; non-blocking anomaly groups retained |
| 18 | Reconcile totals | Curated-export pass | qa_layer_reconciliation.csv and eight-metric powerbi_reconciliation.csv pass at 0.01; native PBIX refresh still required |
| 19 | Metric dictionary | Done | config/metric_definitions.yaml + Drive companion |
| 20–29 | Build marts and analysis | Done — verified | Real-data marts/analysis completed from Drive-backed source; outputs uploaded to Drive, including governed category materiality/LMDI, segment stability, cohort, demographic and private-label anomaly assets |
| 30 | Run statistics | Done — verified | Statistics outputs and success run log created from real Drive-backed DuckDB |
| 31 | Root-cause cases | Done — verified | 3 evidence-backed cases with run ID, grain, action, KPI and limitation |
| 32 | Executive decisions | Done — verified | 5 evidence-backed decisions with run ID, action, KPI and limitation |
| 33 | Export BI marts | Code upgraded | 46 governed marts/analysis exports are declared; rerun the Drive pipeline to materialize the new assets |
| 34 | Build Power BI | Semantic contract ready; binary pending | powerbi/README.md + powerbi/semantic_model.yaml (44 curated tables, six pages, Drive-only source) + powerbi/measures.dax; release audit validates contract content; create PBIX after data refresh |
| 35 | Reconcile SQL/DAX | Curated-export pass; native pending | 8 required metrics pass at tolerance 0.01 in Drive `powerbi_reconciliation.csv`; native Power BI refresh must replace snapshot evidence |
| 36 | Complete UAT | Contract evidence recorded; native pending | `uat_results.csv` has stable UAT-01..UAT-12 IDs; 4 automated/contract checks pass and 8 native visual/interaction checks remain `review` |
| 37 | Excel companion | Done as Drive-native workbook | Google Sheet with Metric Dictionary, Decision Tracker, UAT Checklist, Readme, six output tabs, Plan Status and Source Register with provenance columns |
| 38 | Create diagrams | Done | assets/architecture.svg, assets/star_schema.svg, assets/segmentation_flow.svg, assets/decision_flow.svg |
| 39 | Finalize README | Done | README.md |
| 40 | Finalize limitations | Done | docs/13_limitations.md |
| 41 | Prepare interview guide | Done | docs/15_interview_guide.md |
| 42 | Verified CV bullets | Done — verified with limits | docs/19_verified_cv_bullets.md uses only Drive-backed outputs and labels panel/observational scope |
| 43 | Clean rebuild from raw | Code complete; current rerun pending | src/run_pipeline.py + Makefile `run`; the runner includes storage/source/QA/statistics/export/evidence gates. The Drive manifest currently records the older 31-export snapshot; rerun is required for the current 46-export contract |
| 44 | Tag v1.0.0 | Pending by design | Run src/release_readiness.py / Makefile `release-audit`; it fail-closes on missing Drive QA, governed asset audit, SQL/DAX reconciliation, 12 UAT checks, 3 root-cause cases, 5 decisions or 46 Power BI exports; tag only after the Drive audit is ready |

## Live Drive tracker

The Drive-native workbook contains a `Plan Status` tab covering all 44 steps in `Plan Status!A1:F45`, plus a `Source Register` tab listing the eight expected files, plan row counts, source QA gates and provenance fields for URL, acquisition time, version and SHA-256.

## Definition of 100% completion

The repository implementation is complete through real-data rebuild, QA, statistics, evidence, curated exports and code delivery. The current code has not yet been re-executed against the eight Drive sources on this machine because no Drive mount is available. Final release completion requires that rerun, a successful release audit, and native Power BI refresh/UAT before tagging `v1.0.0`.
