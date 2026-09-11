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
| product.csv | product | product, manufacturer, department, brand, commodities | 92K |
| hh_demographic.csv | household demographic record | household and demographic descriptors | 801 |

The approximate counts are planning expectations from the supplied blueprint. Replace them with the Drive inventory before publishing metrics.

## Acquisition

Primary source: [official dunnhumby Source Files](https://www.dunnhumby.com/source-files/), which provides The Complete Journey download. A permitted mirror such as [the Kaggle dataset](https://www.kaggle.com/datasets/frtgnn/dunnhumby-the-complete-journey) may be used only after confirming its terms and recording the exact URL, download date, version and checksum in Drive `06_source_docs`.

The current project acquisition check on 2026-09-12 found no source CSVs in Drive `01_raw_source`. The connected Drive workflow cannot import a remote URL directly; place the licensed files in Drive before running the pipeline. Do not download or stage raw records in the GitHub checkout or Codex workspace.

Do not redistribute raw source files until rights are verified.

## Acquisition QA

No business analysis starts until:

1. all eight files are inventoried;
2. required columns match contracts;
3. row counts and key uniqueness are reported;
4. anomalies are understood, not silently deleted;
5. the source location is a Drive-backed path.
