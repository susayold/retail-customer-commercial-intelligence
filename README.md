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
- Which campaigns and coupons show higher observed response?
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
Blocking quality gate
        ↓
Analytical marts
        ↓
SQL/statistics + Power BI
        ↓
Executive decisions
~~~

Heavy transformation belongs in DuckDB. Power BI consumes curated marts and aggregates, never the raw 36M-row promotion file by default. The governed P0 layer now includes `Dim_Category`, `Dim_Segment`, `Mart_Store_Weekly`, `Mart_Category_Household_Weekly`, campaign denominator/CI outputs, promotion-universe audit, LMDI root-cause output and a five-row decision register.

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

GitHub stores code, configuration, SQL, documentation, tests and small synthetic fixtures only. Raw source data is never committed to this public repository. The pipeline requires explicit Drive-backed input/output paths; it does not default to the repository or Codex workspace for data artifacts. Every data-writing CLI and Make target, including standalone inventory, Parquet, warehouse, QA, statistics, Power BI and release-audit commands, requires an explicit `--drive-root` and rejects an unavailable or repository-backed root. The [Drive-native Excel companion](https://docs.google.com/spreadsheets/d/16Iz47jiHM2nl5gGuhP5Py_xbNjLVLO5FaFpiL-_dR4k/edit) includes Metric Dictionary, Decision Tracker, UAT Checklist, Plan Status for all 44 plan steps, Source Register for the eight expected files, and the six planned output tabs. The expanded contract now covers 38 curated semantic tables exported as 40 Drive artifacts, including reconciliation outputs; definitions are versioned in `powerbi/semantic_model.yaml` and `powerbi/measures.dax`.

For Drive-only source acquisition, use the [Colab ingestion notebook](https://colab.research.google.com/github/susayold/retail-customer-commercial-intelligence/blob/main/notebooks/drive_ingest_source.ipynb). It streams the official package into the Drive project, extracts the eight CSVs into `01_raw_source`, and writes provenance metadata to Drive; it does not save raw data in the Colab runtime or repository.

## 7. Reproducibility

Run the pipeline from an environment that can read/write the Drive folders, such as Drive for Desktop, a mounted Google Drive runtime or a controlled notebook runtime. Set RETAIL_DRIVE_ROOT to the mounted project folder, then keep RETAIL_DATA_ROOT and RETAIL_ARTIFACT_ROOT underneath it. Do not use the repository as a data lake. Run `make storage` first; the storage gate requires the explicit Drive root, verifies both data paths are underneath it, checks all eight source names, required Drive artifact folders and repository artifact exclusions, and fails before creating artifacts when the Drive root is missing or outside the declared boundary.

~~~powershell
python -m pip install -r requirements.txt
$env:RETAIL_DRIVE_ROOT = "D:\path\to\Drive\Retail DA - Customer & Commercial Intelligence"
$env:RETAIL_DATA_ROOT = "$env:RETAIL_DRIVE_ROOT\01_raw_source"
$env:RETAIL_ARTIFACT_ROOT = "$env:RETAIL_DRIVE_ROOT"
python -m src.run_pipeline --data-root $env:RETAIL_DATA_ROOT --artifact-root $env:RETAIL_ARTIFACT_ROOT --drive-root $env:RETAIL_DRIVE_ROOT --repo-root "." --with-tests
~~~

The D path above is a runtime mount example; the persistent source of truth remains Drive. The runner writes storage_status.json and qa_quality_gate.json to Drive and stops before statistics/BI when blocking checks fail. No raw or curated data is written into the GitHub checkout. After the human-reviewed UAT, SQL/DAX reconciliation, root-cause and decision evidence are placed in Drive, run `make release-audit`; it writes release_readiness.json and fails closed until the final release contract is complete.

## 8. Repository map

~~~text
config/                 contracts, metrics, thresholds
data/                   storage policy only; no raw files
src/                    inventory, profiling, Parquet, DuckDB, QA, reconciliation
sql/                    staging, dimensions, facts, bridges, marts, QA, analysis
notebooks/              statistical validation scaffold
docs/                   business, grain, KPI, methodology, decisions, UAT, interview
tests/                  contract tests and synthetic fixtures
powerbi/                semantic model, DAX measures, UAT and export instructions
~~~

## 9. Build status

| Milestone | Scope | Status |
|---|---|---|
| M1 | inventory, source contracts, profiling, warehouse, QA | scaffolded; run against Drive data |
| M2 | engagement, segmentation, basket/category analytics | real-data marts, statistics and evidence verified in Drive |
| M3 | promotion, campaign, coupon analytics | real-data promotion/campaign/coupon outputs verified in Drive |
| M4 | Power BI, UAT, decisions, interview story | 40 governed exports in the upgraded contract; native PBIX/UAT pending |

Numeric CV bullets are available in `docs/19_verified_cv_bullets.md`; they are explicitly scoped to the observed panel and must not be presented as retailer-wide or causal results.

## 10. KPI guardrails

- Panel Net Spend = SUM(SALES_VALUE).
- Active Panel Households = distinct households with at least one basket in the selected period.
- Baskets/Trips = COUNT(DISTINCT basket_id).
- Spend per Basket = Panel Net Spend / Baskets.
- Spend driver identity = Active Panel Households × Trips per Active Household × Spend per Basket.
- Category penetration = buying households / active panel households.
- Decision alert thresholds apply to relative variance; absolute variance remains available for sizing the movement.
- Promotion and campaign findings are association/observed-response statements, not causal claims.

## 11. Definition of done

A decision-facing number must trace:

~~~text
source → raw → staging → fact/dimension/bridge → metric definition → mart → SQL → Power BI → finding → recommendation
~~~

The final quality gate requires eight sources inventoried, schemas and grains validated, fan-out tests passing, governed assets audited, SQL/DAX reconciled, campaign observability handled, demographic coverage disclosed, zero-sale promotion weeks preserved and three root-cause cases supported by at least five evidence-backed decisions.

## 12. License and source rights

The source files are not redistributed here. The primary acquisition reference is the official [dunnhumby Source Files](https://www.dunnhumby.com/source-files/) page; verify the applicable dunnhumby/Kaggle terms before sharing any raw or derived files. This repository is a portfolio implementation scaffold and must not be treated as an official retailer dataset.

## 13. SQL–Power BI reconciliation command

After the Power BI refresh, place two small comparison inputs on Drive. Each input must contain a metric column and one numeric value column (value, sql_value or powerbi_value). Set the paths and write the result back to the Drive QA folder:

~~~powershell
$env:RETAIL_SQL_RECONCILIATION = "$env:RETAIL_ARTIFACT_ROOT\04_qa_reports\sql_metric_values.csv"
$env:RETAIL_BI_RECONCILIATION = "$env:RETAIL_ARTIFACT_ROOT\04_qa_reports\powerbi_metric_values.csv"
make reconcile
~~~

The target requires RETAIL_DRIVE_ROOT, writes 04_qa_reports/powerbi_reconciliation.csv under the declared Drive root, and fails on any metric outside the configured tolerance. Do not put either input file in the GitHub checkout.


## 14. Source acquisition commands

The source acquisition module is the single implementation for official, Kaggle fallback and manual Drive-backed inputs. It writes temporary bytes and all raw records only below the declared Drive root, and it fails closed on unsafe ZIP paths, unexpected files, checksum mismatches or non-Drive inputs. See docs/18_source_acquisition_runbook.md.

~~~bash
export RETAIL_DRIVE_ROOT="/path/to/Drive/Retail DA - Customer & Commercial Intelligence"
export RETAIL_DATA_ROOT="$RETAIL_DRIVE_ROOT/01_raw_source"
export RETAIL_ARTIFACT_ROOT="$RETAIL_DRIVE_ROOT"
make acquire-official
make verify-source
~~~

For an already licensed Drive-backed fallback, set RETAIL_ACQUISITION_INPUT and run make acquire-manual. Use make acquire-kaggle only after the official source is unavailable and the applicable terms are confirmed. GitHub Actions uses synthetic fixtures only; it never downloads or stores the production source package.
