# Data lineage

This is the canonical short-form lineage map. Raw and derived data stay in the
Drive project root; GitHub contains the executable contracts and transformations.

```text
transaction_data.csv
  → transaction_data.parquet
  → raw_transaction_data / stg_transaction
  → fct_transaction_line
  → fct_basket
  → mart_panel_weekly
  → Mart_Panel_Weekly.parquet
  → executive Power BI / web snapshot
```

Other governed paths:

```text
product.csv → product.parquet → dim_product → dim_category
  → mart_category_weekly / mart_category_household_weekly
  → category penetration, materiality and LMDI exports

causal_data.csv → causal_data.parquet → stg_promotion_state
  → fct_promotion_product_store_week → Mart_Promotion_Category_Week
  → promotion association, dependency boundary and universe audit

campaign_table.csv + campaign_desc.csv
  → campaign marts → exposure/unique-household denominators + Wilson CI

coupon.csv + coupon_redempt.csv
  → bridge_coupon_product_campaign + redemption fact
  → coupon summary and observed repeat-category analysis
```

Each run records `run_id`, source manifest hash, repository commit, output
hashes, QA outputs and start/end timestamps in
`06_source_docs/data_run_manifest.json`.

See [20_data_lineage.md](20_data_lineage.md) for the expanded table-level map.

Curated source Parquet carries `source_file`, `ingestion_timestamp`, `pipeline_run_id` and `schema_version`; governed BI Parquet carries `pipeline_run_id`. These fields are technical lineage metadata only and do not change metric definitions.
