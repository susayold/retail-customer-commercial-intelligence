# Raw layer

The raw layer is represented by DuckDB views registered from the eight CSVs in the Drive `01_raw_source` folder. No raw CSV is copied into this repository.

Runtime registration is implemented in `src/utils/duckdb_client.py`:

- `raw_transaction_data`
- `raw_causal_data`
- `raw_coupon`
- `raw_coupon_redempt`
- `raw_campaign_table`
- `raw_campaign_desc`
- `raw_product`
- `raw_hh_demographic`

The views are read-only inputs for the SQL transformation chain. Source presence, schema and expected grain must pass `src/storage_policy.py`, `src/schema_contracts.py` and `src/inventory.py` before warehouse models run.

