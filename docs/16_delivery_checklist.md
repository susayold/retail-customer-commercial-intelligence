# Delivery checklist

This checklist separates implemented repository work from outputs that require the eight real source CSVs in Drive.

| Step | Plan item | Status | Evidence / next action |
|---:|---|---|---|
| 01 | Create repo | Done | GitHub repository on main |
| 02 | Download data | Blocked by source availability | Put licensed CSVs in Drive 01_raw_source |
| 03 | Inventory files | Implemented | src/inventory.py + storage_status.json; run to Drive QA |
| 04 | Validate schemas | Implemented | src/schema_contracts.py + config/source_contracts.yaml |
| 05 | Profile sources | Implemented | src/profile_sources.py; row/type/null/distinct/range/cardinality outputs |
| 06 | Document grain | Done | docs/04_grain_and_join_contracts.md, docs/05_data_model.md |
| 07 | Document join risks | Done | docs/04_grain_and_join_contracts.md |
| 08 | Convert CSV to Parquet | Implemented; audited logging | src/build_parquet.py; Drive output only; exact rows read/written logged |
| 09 | Initialize DuckDB | Implemented; audited logging | src/build_warehouse.py; per-model rows read/written logged |
| 10–16 | Build staging, dimensions, facts, bridge | Implemented and smoke-tested | sql/02_staging through sql/05_bridges |
| 17 | Run QA | Implemented; anomaly QA, logging and blocking gate added | sql/07_quality/09_q09_transaction_anomalies.sql, sql/07_quality/10_q10_layer_reconciliation.sql, src/validate.py, src/enforce_quality_gate.py, QA exports + qa_run_log.csv + qa_quality_gate.json |
| 18 | Reconcile totals | Implemented; layer and BI checks defined | qa_layer_reconciliation.csv for raw/staging/fact rows, populations and sales; src/reconcile.py + sql/09_exports for SQL/DAX; release audit validates exact eight required reconciliation metrics |
| 19 | Metric dictionary | Done | config/metric_definitions.yaml + Drive companion |
| 20–29 | Build marts and analysis | Implemented and smoke-tested | sql/06_marts including mart_category_household and cross-category pairs; sql/08_analysis including promotion/campaign/coupon; campaign windows, trajectory windows and category-pair minimums are configurable and rendered from config/analysis_thresholds.yaml |
| 30 | Run statistics | Implemented | src/statistical_validation.py + notebook; statistics_run_log.csv records run ID, UTC timestamps, status, database path, outputs and error; requires real Drive DuckDB |
| 31 | Root-cause cases | Template ready | docs/11_root_cause_cases.md; requires verified output |
| 32 | Executive decisions | Template ready | docs/12_executive_decisions.md + Drive Decision_Tracker |
| 33 | Export BI marts | Implemented | src/export_powerbi.py exports 31 curated marts/analysis/QA outputs, including category, promotion, campaign and coupon aggregates |
| 34 | Build Power BI | Semantic contract ready; binary pending | powerbi/README.md + powerbi/semantic_model.yaml (29 curated tables, six pages, Drive-only source) + powerbi/measures.dax; release audit validates contract content; create PBIX after data refresh |
| 35 | Reconcile SQL/DAX | Implemented method; pending result | docs/14_powerbi_uat.md + Drive QA output |
| 36 | Complete UAT | Checklist ready; pending result | Drive companion UAT_Checklist with stable UAT-01..UAT-12 IDs; release audit enforces exact unique IDs |
| 37 | Excel companion | Done as Drive-native workbook | Google Sheet with six plan tabs plus tracker/readme + Plan Status |
| 38 | Create diagrams | Done | assets/architecture.svg, assets/star_schema.svg |
| 39 | Finalize README | Done | README.md |
| 40 | Finalize limitations | Done | docs/13_limitations.md |
| 41 | Prepare interview guide | Done | docs/15_interview_guide.md |
| 42 | Verified CV bullets | Pending by design | Only write after real-data QA |
| 43 | Clean rebuild from raw | Runner ready; pending source | src/run_pipeline.py + Makefile `run`; every standalone data-writing stage also requires `--drive-root`, rejects unavailable/repository-backed roots, and persists storage status and blocking QA gate only to Drive; execute full Drive-only rebuild after source upload |
| 44 | Tag v1.0.0 | Pending by design | Run src/release_readiness.py / Makefile `release-audit`; it fail-closes on missing Drive QA, SQL/DAX reconciliation, 12 UAT checks, 3 root-cause cases, 5 decisions or 31 Power BI exports; tag only after the Drive audit is ready |

## Live Drive tracker

The Drive-native workbook contains a `Plan Status` tab covering all 44 steps in `Plan Status!A1:F45`, plus a `Source Register` tab listing the eight expected files, plan row counts and source QA gates.

## Definition of 100% completion

The project is 100% complete only when the source is present in Drive, the clean rebuild produces QA and BI exports, SQL/DAX reconciliation passes, six Power BI pages are refreshed, UAT is evidenced, three root-cause cases and five decisions are evidence-backed, CV bullets are verified, and v1.0.0 is tagged.
