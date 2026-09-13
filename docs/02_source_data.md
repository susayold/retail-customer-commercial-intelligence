# Source data

## Source inventory

| Source | Expected grain | Key fields | Approx. scale |
|---|---|---|---:|
| transaction_data.csv | product line in basket | household, basket, day, product, store, sales, discounts | 2.6M |
| causal_data.csv | product × store × week | product, store, week, display, mailer | 36.8M |
| coupon.csv | coupon × product × campaign bridge | coupon UPC, product, campaign | 124K |
| coupon_redempt.csv | redemption event | household, day, coupon UPC, campaign | 2.3K |
| campaign_table.csv | household × campaign exposure | household, campaign | 7.2K |
| campaign_desc.csv | campaign | campaign, type, start/end day | 30 |
| product.csv | product | manufacturer, department, brand, commodity | 92K |
| hh_demographic.csv | household demographic record | household and demographic descriptors | 801 |

The 2026-09-14 official-source rebuild verified the planning scale: 2,595,732 transaction rows, 36,786,524 causal rows, 92,353 products, 801 demographic records and the full eight-file set. The Drive inventory records the observed count, delta, column count, header hash and content SHA-256 for every file.

## Exact source contract

The raw layer is valid only when 01_raw_source contains exactly these eight direct CSV files:

1. transaction_data.csv
2. causal_data.csv
3. coupon.csv
4. coupon_redempt.csv
5. campaign_table.csv
6. campaign_desc.csv
7. product.csv
8. hh_demographic.csv

The canonical name and planning-count contract lives in GitHub src/source_manifest.py. Required headers live in config/source_contracts.yaml. Both are metadata only and contain no source records.

## Acquisition

The canonical acquisition reference is the official [dunnhumby Source Files](https://www.dunnhumby.com/source-files/) page. The configured operational asset URL is stored in config/source_acquisition.yaml. The Drive-only implementation and fallback procedure are documented in [the source acquisition runbook](18_source_acquisition_runbook.md).

Run from a mounted Drive-backed environment:

~~~bash
export RETAIL_DRIVE_ROOT="/path/to/Drive/Retail DA - Customer & Commercial Intelligence"
export RETAIL_DATA_ROOT="$RETAIL_DRIVE_ROOT/01_raw_source"
export RETAIL_ARTIFACT_ROOT="$RETAIL_DRIVE_ROOT"
make acquire-official
make verify-source
~~~

The module streams the package to Drive 06_source_docs/acquisition_staging, validates safe archive paths, exact recursive discovery, non-empty CSVs, required headers and SHA-256 values, then promotes only verified files to 01_raw_source. A failed run keeps its manifest and log without mutating raw. An identical existing raw set is recorded as NO_OP; a different, partial or extra set fails closed.

Kaggle is a fallback only after official acquisition is unavailable and its terms are confirmed. A manual ZIP/folder must already be under the declared Drive root. Do not download or stage raw records in the GitHub checkout, Codex workspace or any other local data directory.

## Drive evidence

A successful run writes these metadata artifacts to 06_source_docs:

- source_provenance.json: provider, landing/direct URL, acquisition time, archive metadata and per-file records;
- source_checksums.csv: file, size and SHA-256;
- acquisition_manifest.json: run state, staging path and outcome;
- acquisition_run.log: append-only JSONL run events;
- source_ready.json: READY marker consumed by the pipeline gate.

The corrected project source gate is READY. The rebuild used the official archive (`dunnhumby_The-Complete-Journey.zip`, SHA-256 `5e0a3d72…0558f9a`) and promoted the exact eight-file raw set to Drive. Raw and curated production data are not committed to GitHub and are removed from the local staging area after delivery.

## Acquisition QA

No business analysis starts until:

1. all eight files are inventoried;
2. required columns match contracts;
3. row counts and key uniqueness are reported;
4. anomalies are understood, not silently deleted;
5. provenance and checksums reconcile;
6. the source location is a Drive-backed path;
7. source_ready.json and make verify-source both report READY.

Do not redistribute raw source files until the applicable rights are verified.
