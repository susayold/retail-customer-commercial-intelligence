# Data lineage

The project keeps raw and derived data under the declared Google Drive project root. The GitHub repository contains contracts, SQL, Python orchestration, documentation and synthetic fixtures only.

```text
01_raw_source/transaction_data.csv
  → 02_curated_parquet/transaction_data.parquet
  → raw_transaction_data / stg_transaction
  → fct_transaction_line
  → fct_basket
  → mart_panel_weekly / mart_household_weekly
  → 05_powerbi_exports/Mart_Panel_Weekly.parquet
  → Executive Customer & Commercial Health
```

The governed category lineage is:

```text
product.csv
  → dim_product
  → dim_category (department × commodity)
  → mart_category_weekly
  → mart_category_household_weekly
  → analysis_category_penetration / analysis_category_decomposition
  → Power BI category pages
```

Promotion, campaign and coupon lineage is kept separate to prevent fan-out:

```text
causal_data.csv → fct_promotion_product_store_week → mart_promotion_category_week → promotion audit/statistics
campaign_table.csv + campaign_desc.csv → fct_campaign_exposure → mart_campaign_household → campaign denominators/CI
coupon.csv + coupon_redempt.csv → bridge_coupon_product_campaign + fct_coupon_redemption → coupon marts
```

Every full run records source checksums, curated-file hashes, Power BI export hashes, the DuckDB path, QA outputs, repository commit and `pipeline_run_id` in `06_source_docs/data_run_manifest.json`.
