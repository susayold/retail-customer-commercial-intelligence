# Retail Customer & Commercial Intelligence

End-to-end Retail Data Analyst portfolio built on the dunnhumby The Complete Journey panel.

> Trusted retail data → governed metrics → customer/basket/category intelligence → promotion/campaign evidence → root-cause diagnosis → business decisions.

## 1. Executive summary

This project answers how observed panel households engage, shop baskets, buy categories and brands, respond to merchandising support, and interact with campaigns/coupons. It is designed for Retail Data Analyst, BI Analyst, CRM/Customer Analytics and Commercial Analyst roles.

The project is intentionally not an ML competition. The differentiators are grain discipline, SQL-first warehouse design, QA/reconciliation, explainable segmentation, decision-ready marts and honest interpretation of observational evidence.

## 2. Business problem

A retail commercial team needs to know:

- What is changing in observed panel spend, active households, trips and basket value?
- Which customer segments are growing, stable or declining?
- Which categories and brands explain the movement?
- Where is private-label activity broad or concentrated?
- Which display/mailer states are associated with stronger panel activity?
- Which campaigns and coupons show stronger observed response?
- What actions should be monitored next?

The final product is a six-page Power BI decision surface plus reproducible SQL/Python lineage.

## 3. Dataset and panel boundary

The Complete Journey contains roughly two years of transactions for approximately 2,500 frequent-shopper households. It is an observed panel, not the retailer's entire customer population or store sales.

Use: observed panel spend, panel households, observed baskets, category penetration within the panel, campaign-recipient behavior and promotion-associated panel activity.

Do not claim total retailer revenue, market share, full store traffic, causal promotion uplift, causal campaign lift, campaign ROI, profit margin, inventory optimization or true customer lifetime value.

The source has no true calendar dates. DAY and WEEK_NO are observation indexes. Any synthetic calendar field is labeled synthetic_date and is never interpreted as real-world seasonality.

## 4. Decision questions

1. Which accounting driver explains a panel-spend movement: active households, trips per household or spend per basket?
2. Which high-value observed households show declining engagement?
3. Which categories are broad/deep versus deteriorating?
4. Which private-label patterns are supported by observed behavior?
5. Which promotion states are associated with stronger activity, with sample sizes visible?
6. Which campaign types and customer groups show higher observed redemption?
7. Which five decisions should a commercial/CRM team test or monitor?

## 5. Architecture

~~~text
Drive raw source files
        ↓
Python inventory + schema validation
        ↓
DuckDB raw views
        ↓
Parquet curated layer
        ↓
Staging
        ↓
Facts + dimensions + coupon bridge
        ↓
QA + reconciliation
        ↓
Analytical marts
        ↓
SQL/statistics + Power BI
        ↓
Executive decisions
~~~

Heavy transformation belongs in DuckDB. Power BI consumes curated marts and aggregates, never the raw 36M-row promotion file by default.

## 6. Storage policy: Drive + GitHub only

The data source of truth is the linked Google Drive folder:

[Retail DA - Customer & Commercial Intelligence](https://drive.google.com/drive/folders/1MvLDI23G-3TsUQEo4d_EjcYbvAKjnoh0)

Drive subfolders:

- 01_raw_source: the eight source CSVs, subject to redistribution rights.
- 02_curated_parquet: Parquet outputs.
- 03_duckdb_and_marts: DuckDB file and analytical marts.
- 04_qa_reports: inventories, profiles, QA and reconciliation outputs.
- 05_powerbi_exports: PBIX/PDF/Excel exports.
- 06_source_docs: source notes and evidence.

GitHub stores code, configuration, SQL, documentation, tests and small synthetic fixtures only. Raw source data is never committed to this public repository. The pipeline requires explicit Drive-backed input/output paths; it does not default to the repository or Codex workspace for data artifacts.

## 7. Reproducibility

Run the pipeline from an environment that can read/write the Drive folders, such as Drive for Desktop, a mounted Google Drive runtime or a controlled notebook runtime. Keep RETAIL_DATA_ROOT and RETAIL_ARTIFACT_ROOT pointed at Drive. Do not use the repository as a data lake.

~~~powershell
python -m pip install -r requirements.txt
$env:RETAIL_DATA_ROOT = "D:\path\to\Drive\Retail DA - Customer & Commercial Intelligence\01_raw_source"
$env:RETAIL_ARTIFACT_ROOT = "D:\path\to\Drive\Retail DA - Customer & Commercial Intelligence"
python -m src.inventory --input $env:RETAIL_DATA_ROOT --output "$env:RETAIL_ARTIFACT_ROOT\04_qa_reports\raw_file_inventory.csv"
python -m src.build_parquet --input $env:RETAIL_DATA_ROOT --output "$env:RETAIL_ARTIFACT_ROOT\02_curated_parquet"
python -m src.build_warehouse --data-root $env:RETAIL_DATA_ROOT --artifact-root $env:RETAIL_ARTIFACT_ROOT
python -m src.validate --data-root $env:RETAIL_DATA_ROOT --artifact-root $env:RETAIL_ARTIFACT_ROOT
pytest
~~~

The D path above is a runtime mount example; the persistent source of truth remains Drive. No raw or curated data is written into the GitHub checkout.

## 8. Repository map

~~~text
config/                 contracts, metrics, thresholds
data/                   storage policy only; no raw files
src/                    inventory, Parquet, DuckDB, QA, reconciliation
sql/                    staging, dimensions, facts, bridges, marts, QA, analysis
docs/                   business, grain, KPI, methodology, decisions, UAT, interview
tests/                  contract tests and synthetic fixtures
powerbi/                semantic model, UAT and export instructions
~~~

## 9. Build status

| Milestone | Scope | Status |
|---|---|---|
| M1 | inventory, contracts, profiling, warehouse, QA | scaffolded; run against Drive data |
| M2 | engagement, segmentation, basket/category analytics | SQL contracts ready; findings pending data run |
| M3 | promotion, campaign, coupon analytics | SQL contracts ready; findings pending data run |
| M4 | Power BI, UAT, decisions, interview story | design ready; verified outputs pending data run |

No numeric CV bullets are included until the full data run produces verified numbers.

## 10. KPI guardrails

- Panel Net Spend = SUM(SALES_VALUE).
- Active Panel Households = distinct households with at least one basket in the selected period.
- Baskets/Trips = COUNT(DISTINCT basket_id).
- Spend per Basket = Panel Net Spend / Baskets.
- Spend driver identity = Active Households × Trips per Active Household × Spend per Basket.
- Category penetration = buying households / active panel households.
- Promotion and campaign findings are association/observed-response statements, not causal claims.

## 11. Definition of done

A decision-facing number must trace:

~~~text
source → raw → staging → fact/dimension/bridge → metric definition → mart → SQL → Power BI → finding → recommendation
~~~

The final quality gate requires eight sources inventoried, schemas and grains validated, fan-out tests passing, SQL/DAX reconciled, campaign observability handled, demographic coverage disclosed, zero-sale promotion weeks preserved and three root-cause cases supported by at least five evidence-backed decisions.

## 12. License and source rights

The source files are not redistributed here. Verify dunnhumby/Kaggle terms before sharing any raw or derived files. This repository is a portfolio implementation scaffold and must not be treated as an official retailer dataset.
