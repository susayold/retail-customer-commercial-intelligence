# Verified CV bullets — real-data run

Source run: `source_rebuild_20260914_private_label`; pipeline run: `da_no_native_20260913T213859Z_341c1744`.

- Built a Drive-backed retail customer and commercial intelligence pipeline over 8 source files, validating 2.6M transaction lines and 36.8M promotion rows; implemented source contracts, profiling, Parquet, DuckDB marts, QA and 31 curated Power BI exports.
- Delivered a governed retail warehouse with basket, category, promotion, campaign and coupon grains; reconciled raw → staging → fact populations and sales totals, with the blocking quality gate passing and source anomalies retained for review.
- Produced five evidence-backed commercial decisions and three root-cause cases, including a 13-week panel spend movement decomposition, category erosion diagnostics and campaign redemption funnel analysis with denominators and observability fields.
- Reconciled eight core SQL metrics against the curated Power BI export snapshot within `0.01` tolerance, while documenting the remaining native PBIX refresh and interaction-UAT requirement.
- Repaired the private-label semantic contract by preserving raw `BRAND`, normalizing production values with `UPPER(TRIM(BRAND))`, and reconciling an independent raw baseline to warehouse/export at `27.7663%` share; segmentation assigns one label to each of 2,500 households.
- Completed the non-native release path with `DATA_READY`, `DA_ANALYSIS_READY`, 31 analytical exports and 100 passing tests; native Power BI interaction UAT remains the single deferred release gate.

Safe-claim boundary: all metrics describe the observed frequent-shopper panel. They do not establish market share, retailer-wide revenue, causal promotion/campaign lift, ROI or margin.
