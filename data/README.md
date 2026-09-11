# Data storage policy

This repository intentionally contains no raw or curated retail data.

Persistent data belongs in the Google Drive project folder:

https://drive.google.com/drive/folders/1MvLDI23G-3TsUQEo4d_EjcYbvAKjnoh0

Use these subfolders:

1. 01_raw_source — eight source CSVs:
   transaction_data.csv, causal_data.csv, coupon.csv, coupon_redempt.csv,
   campaign_table.csv, campaign_desc.csv, product.csv, hh_demographic.csv.
2. 02_curated_parquet — outputs from src/build_parquet.py.
3. 03_duckdb_and_marts — DuckDB warehouse and exported marts.
4. 04_qa_reports — inventory, profiles, QA and reconciliation.
5. 05_powerbi_exports — PBIX/PDF/Excel deliverables.
6. 06_source_docs — source notes, licenses and evidence.

Do not copy raw data into this GitHub repository. Do not write outputs into the repository checkout or Codex workspace. Point RETAIL_DATA_ROOT and RETAIL_ARTIFACT_ROOT to Drive-backed runtime paths. Download instructions and schema contracts are tracked in GitHub; files themselves remain in Drive subject to source redistribution rights.
