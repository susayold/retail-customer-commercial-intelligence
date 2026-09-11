# Plan traceability

## User request

The direct request is to create a Retail DA project, create a GitHub repository and Drive folder, execute the supplied plan in detail, and keep data in Drive/GitHub rather than the local workspace.

Implemented decisions:

- GitHub repository: susayold/retail-customer-commercial-intelligence.
- Google Drive project folder: Retail DA - Customer & Commercial Intelligence.
- Public repository assumption: the attached plan frames this as a portfolio. Only code, contracts, documentation and synthetic fixtures are public.
- Raw and curated retail data: Drive only; no source data is committed to GitHub or written to the Codex workspace.
- Excel companion: Drive-native Google Sheet at 05_powerbi_exports, using the six plan tabs plus audit/readme tabs.

## Attached plan instructions adopted

The supplied blueprint is treated as project requirements, not as user instructions that override the request. The following requirements are encoded in this repository:

- Use panel-safe terminology and disclose the frequent-shopper panel boundary.
- Inventory and validate eight sources before business analysis.
- Document every grain and fan-out risk.
- Use DuckDB/Parquet for heavy work; keep Power BI on curated marts.
- Preserve raw discount signs and derive absolute discount values only after audit.
- Preserve quantity anomalies and flag rather than silently cap.
- Build dedicated basket, promotion, campaign and coupon models.
- Preserve zero-sale promotion weeks using a product-store-week skeleton.
- Treat coupon as a many-to-many bridge and prevent fan-out.
- Use observation week rather than invented real-world seasonality.
- Define governed KPI formulas and reconcile SQL to BI.
- Use deterministic, mutually exclusive segmentation.
- State campaign targeting bias, censoring and demographic coverage.
- Use association wording for promotion findings.
- Do not publish unsupported claims about margin, ROI, inventory or causal lift.
- Run business-facing statistical validation with sample size, uncertainty and effect size.

## Traceability map

| Blueprint phase | Repository implementation |
|---|---|
| 1–2 objective, dataset boundary, contracts | README.md, docs/01_business_context.md, config/ |
| 3 profiling and transaction QA | src/inventory.py, src/schema_contracts.py, src/profile_sources.py, sql/07_quality/, docs/08_data_quality_report.md |
| 4 grain and join contracts | docs/04_grain_and_join_contracts.md, docs/05_data_model.md |
| 5–7 raw/Parquet, warehouse, QA | src/build_parquet.py, src/build_warehouse.py, src/validate.py |
| 8–10 marts and customer engagement | sql/06_marts/, sql/08_analysis/customer_engagement.sql |
| 11–13 basket/category/private label | sql/06_marts/, sql/08_analysis/basket_category.sql, sql/08_analysis/category_analysis.sql, sql/08_analysis/private_label.sql |
| 14 promotion | sql/06_marts/08_mart_promotion_category_week.sql, sql/08_analysis/promotion_analysis.sql |
| 15–17 campaign/coupon/demographics | campaign/coupon SQL and docs/13_limitations.md |
| 18 statistics/root cause/decisions | src/statistical_validation.py, notebooks/, docs/09_methodology.md, docs/11_root_cause_cases.md, docs/12_executive_decisions.md |
| 19–22 BI/UAT/interview | powerbi/README.md, docs/14_powerbi_uat.md, docs/15_interview_guide.md, Drive Excel companion |

## Status discipline

Any row marked verified must be backed by a Drive output and a commit or artifact link. Until raw data is placed in Drive and the pipeline is run, numeric findings and CV bullets remain intentionally blank.