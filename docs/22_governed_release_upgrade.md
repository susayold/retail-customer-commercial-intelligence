# Governed release upgrade — 2026-09-21

This upgrade turns the previous supplemental-output pattern into first-class pipeline assets and adds the remaining stability, materiality, cohort and demographic analyses.

## Added P0 assets

- `dim_category` and `dim_segment` are built in the warehouse.
- `mart_store_weekly` and `mart_category_household_weekly` have explicit grains.
- Existing category, brand and promotion marts carry the stable `category_key`.
- `analysis_campaign_denominators` separates exposure-level and unique-household rates and adds Wilson intervals.
- `analysis_promotion_universe_audit` records whether a valid `none` state exists.
- `analysis_root_cause_lmdi` reconciles the panel-spend driver identity.
- `analysis_executive_decisions` is a governed five-row decision register.
- `audit_governed_assets` blocks a run when any required P0 relation is missing or empty.
- Power BI export inventory is now generated from the expanded governed table contract.
- Private-label anomaly QA is materialized as `qa_private_label_category_anomalies.csv`; an empty file with a valid header means no anomaly was detected and is not silently capped.

## Run order

```text
source gate → schema/inventory/profile → curated Parquet → DuckDB SQL
→ QA/reconciliation → governed asset audit → quality gate → statistics
→ Power BI Parquet exports → tests → data readiness manifest
```

The promotion audit may return `NOT_OBSERVED`. That is a valid data finding, not a zero-filled control group; the project must retain association-only language in that case.
