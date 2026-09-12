# Drive-only source acquisition runbook

## Purpose

This project does not store the licensed dunnhumby records in the GitHub repository or the local workspace. The eight raw CSVs, temporary ZIP/staging bytes, Parquet, DuckDB, QA outputs and Power BI exports belong under the Google Drive project root:

- 01_raw_source: exactly the eight validated CSVs;
- 02_curated_parquet: curated Parquet;
- 03_duckdb_and_marts: DuckDB and analytical marts;
- 04_qa_reports: inventory, schema, profiling, QA and reconciliation;
- 05_powerbi_exports: BI exports;
- 06_source_docs: provenance, checksums, manifests and run logs.

GitHub stores code, contracts, configuration, documentation, tests and small synthetic fixtures only.

## Acquisition contract

The exact raw file set is defined once in src/source_manifest.py:

transaction_data.csv, causal_data.csv, coupon.csv, coupon_redempt.csv, campaign_table.csv, campaign_desc.csv, product.csv, hh_demographic.csv.

config/source_acquisition.yaml contains the official landing page, the operational direct asset URL, the documented Kaggle fallback slug and the Drive paths. It contains no credentials or source records.

## Official path

1. Confirm the applicable dunnhumby source-use terms from the official Source Files page.
2. Mount or open the Drive project root and confirm at least 3–5 GB of free space.
3. Pull the repository code into the runtime; the checkout is code-only.
4. Set the Drive root. Example:

~~~bash
export RETAIL_DRIVE_ROOT="/path/to/Drive/Retail DA - Customer & Commercial Intelligence"
export RETAIL_DATA_ROOT="$RETAIL_DRIVE_ROOT/01_raw_source"
export RETAIL_ARTIFACT_ROOT="$RETAIL_DRIVE_ROOT"
~~~

5. Run the official provider:

~~~bash
make acquire-official
make verify-source
~~~

The module streams the ZIP in 8 MiB chunks to Drive 06_source_docs/acquisition_staging/run_<run_id>/download, safely extracts it below the same Drive staging run, validates the exact eight CSVs and their header contracts, computes SHA-256 checksums, and promotes only verified files into 01_raw_source.

The official landing page is canonical. The direct URL is operational and may rotate; if the request fails, inspect the landing page and update config/source_acquisition.yaml before considering a fallback.

## Fallbacks

Use Kaggle only after the official source is unavailable and the applicable terms have been checked:

~~~bash
make acquire-kaggle
make verify-source
~~~

Use a manual ZIP or folder only when it is already Drive-backed:

~~~bash
export RETAIL_ACQUISITION_INPUT="$RETAIL_DRIVE_ROOT/06_source_docs/licensed_source.zip"
make acquire-manual
make verify-source
~~~

The manual input must be under the declared Drive root. The acquisition code rejects local/repository paths, zero-byte files, corrupt archives, ZIP path traversal, symlinks, duplicate expected names, missing names and unexpected CSV names.

## Idempotency and failure behavior

- Empty 01_raw_source: validate and promote.
- Exact eight existing files with identical checksums: record NO_OP; do not overwrite.
- Exact eight existing files with different checksums: fail closed; do not replace.
- Partial, nested, zero-byte or extra raw state: fail closed; resolve it in Drive first.
- A failed run retains acquisition_manifest.json and acquisition_run.log and does not mark source_ready.json as READY.
- A successful run writes source_provenance.json, source_checksums.csv, acquisition_manifest.json, acquisition_run.log and source_ready.json under 06_source_docs.

## Downstream closure sequence

After make verify-source succeeds, run these stages in order, with every output on Drive:

~~~bash
make storage
make schema
make inventory
make profile
make parquet
make warehouse
make validate
make quality-gate
make stats
make powerbi
~~~

The one-command runner enforces the same order and stops at storage_boundary_gate or source_ready_gate before any transform. Parquet uses 04_qa_reports/raw_file_inventory.csv row counts when available and checks the written row counts again with DuckDB.

Do not publish business findings until source provenance, schema, grain, key/reference, layer-reconciliation and quality-gate evidence are present. Campaign and promotion outputs remain observational associations; they are not causal uplift or ROI claims.

## CI and readiness

GitHub Actions runs tests with synthetic fixtures only. CI must not download the production package, call Kaggle, upload files or write raw data. Real readiness is evidenced by the Drive marker and checksums plus the Drive QA outputs. Only after those gates pass should the project update the companion tracker to Verified, complete the root-cause/decision/UAT evidence, and produce a release audit.

Official references:

- https://www.dunnhumby.com/source-files/
- https://www.kaggle.com/datasets/frtgnn/dunnhumby-the-complete-journey
