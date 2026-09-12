# Business rules

1. The unit of transaction analysis is one source product line inside one basket.
2. Basket count is COUNT DISTINCT basket_id or rows in fct_basket, never transaction-line count.
3. Panel Net Spend is SUM(SALES_VALUE), and is never renamed retailer revenue.
4. Discount signs are preserved in raw fields; absolute values are derived after audit.
5. gross_spend_before_recorded_discounts is a descriptive reconstruction, not official list-price revenue.
6. Raw quantity is preserved. Outliers are flagged and not silently capped.
7. DAY and WEEK_NO are observation indexes. Synthetic dates are for BI mechanics only.
8. First observed purchase is not customer acquisition.
9. Customer trajectory uses early and late 13-observation-week windows. Thresholds are Growing at +10%, Declining at -10%, otherwise Stable; missing window coverage is Insufficient History.
10. Segments are deterministic and assigned once using listed precedence.
11. Category household penetration uses buying households divided by active panel households for the selected period.
12. Coupon is a many-to-many coupon UPC × product × campaign bridge.
13. Campaign redemption rate uses recipient households as the denominator.
14. Campaign post windows are blank when not observable; they are never zero-filled.
15. Promotion findings use associated with, not caused.
16. Demographic findings are limited to households with demographic records and include coverage.
17. No COGS, campaign cost, inventory or geography is invented.
18. v1 decision alerts are limited to panel net spend, active households and trips per household week-over-week declines. Each alert exposes metric, baseline, current, absolute variance, relative variance, threshold, severity and scope; the -10% threshold is applied to relative variance. Optional category, campaign, promotion-dependency and private-label alerts remain disabled until their denominators and real-source QA are verified.
