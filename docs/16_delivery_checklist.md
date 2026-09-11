# Delivery checklist

This checklist separates implemented repository work from outputs that require the eight real source CSVs in Drive.

| Step | Plan item | Status | Evidence / next action |
|---:|---|---|---|
| 01 | Create repo | Done | GitHub repository on main |
| 02 | Download data | Blocked by source availability | Put licensed CSVs in Drive 01_raw_source |
| 03 | Inventory files | Implemented | src/inventory.py; run to Drive QA |
| 04 | Validate schemas | Implemented | src/schema_contracts.py + config/source_contracts.yaml |
| 05 | Profile sources | Implemented | src/profile_sources.py; row/type/null/distinct/range outputs |
| 06 | Document grain | Done | docs/04_grain_and_join_contracts.md, docs/05_data_model.md |
| 07 | Document join risks | Done | docs/04_grain_and_join_contracts.md |
| 08 | Convert CSV to Parquet | Implemented | src/build_parquet.py; Drive output only |
| 09 | Initialize DuckDB | Implemented | src/build_warehouse.py |
| 10–16 | Build staging, dimensions, facts, bridge | Implemented and smoke-tested | sql/02_staging through sql/05_bridges |
| 17 | Run QA | Implemented and smoke-tested | sql/07_quality, src/validate.py |
| 18 | Reconcile totals | Implemented | src/reconcile.py + sql/09_exports |
| 19 | Metric dictionary | Done | config/metric_definitions.yaml + Drive companion |
| 20–29 | Build marts and analysis | Implemented and smoke-tested | sql/06_marts, sql/08_analysis |
| 30 | Run statistics | Implemented | src/statistical_validation.py + notebook; requires real Drive DuckDB |
| 31 | Root-cause cases | Template ready | docs/11_root_cause_cases.md; requires verified output |
| 32 | Executive decisions | Template ready | docs/12_executive_decisions.md; requires verified output |
| 33 | Export BI marts | Implemented | src/export_powerbi.py now executes sql/09_exports |
| 34 | Build Power BI | Spec ready; binary pending | powerbi/README.md; create PBIX after data refresh |
| 35 | Reconcile SQL/DAX | Implemented method; pending result | docs/14_powerbi_uat.md + Drive QA output |
| 36 | Complete UAT | Checklist ready; pending result | Drive companion UAT_Checklist |
| 37 | Excel companion | Done as Drive-native workbook | Google Sheet with six plan tabs plus tracker/readme |
| 38 | Create diagrams | Done | assets/architecture.svg, assets/star_schema.svg |
| 39 | Finalize README | Done | README.md |
| 40 | Finalize limitations | Done | docs/13_limitations.md |
| 41 | Prepare interview guide | Done | docs/15_interview_guide.md |
| 42 | Verified CV bullets | Pending by design | Only write after real-data QA |
| 43 | Clean rebuild from raw | Pending by design | Run after Drive source upload |
| 44 | Tag v1.0.0 | Pending by design | Tag only after all gates pass |

## Definition of 100% completion

The project is 100% complete only when the source is present in Drive, the clean rebuild produces QA and BI exports, SQL/DAX reconciliation passes, six Power BI pages are refreshed, UAT is evidenced, three root-cause cases and five decisions are evidence-backed, CV bullets are verified, and v1.0.0 is tagged.