# Reports and generated artifacts

Generated inventories, profiles, QA reports, reconciliation files, statistics, Parquet, DuckDB, Power BI exports and Excel/PDF deliverables are stored in the linked Google Drive project, not in this GitHub checkout.

Drive destinations:

- `04_qa_reports`: inventory, source profiles, QA, reconciliation, logs and statistical outputs.
- `03_duckdb_and_marts`: DuckDB warehouse and analytical marts.
- `02_curated_parquet`: curated Parquet source layer.
- `05_powerbi_exports`: curated Power BI exports and final presentation artifacts.

This directory contains documentation only. Do not add raw or generated retail data here; the repository policy allows only the small synthetic fixtures under `tests/fixtures`.
