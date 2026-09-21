# Verified CV bullets — real-data run

Source run: `run_20260913T001329Z_69411005`.

- Built a Drive-backed retail customer and commercial intelligence pipeline over 8 source files, validating 2.6M transaction lines and 36.8M promotion rows; implemented source contracts, profiling, Parquet, DuckDB marts, QA and a governed 40-export Power BI contract.
- Delivered a governed retail warehouse with basket, category, promotion, campaign and coupon grains; reconciled raw → staging → fact populations and sales totals, with the blocking quality gate passing and source anomalies retained for review.
- Produced five evidence-backed commercial decisions and three root-cause cases, including a 13-week panel spend movement decomposition, category erosion diagnostics and campaign redemption funnel analysis with denominators and observability fields.
- Reconciled eight core SQL metrics against the curated Power BI export snapshot within `0.01` tolerance, while documenting the remaining native PBIX refresh and interaction-UAT requirement.

Safe-claim boundary: all metrics describe the observed frequent-shopper panel. They do not establish market share, retailer-wide revenue, causal promotion/campaign lift, ROI or margin.
