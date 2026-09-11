# Interview guide

## Three-minute story

Problem: understand observed household engagement, basket/category behavior, merchandising association and direct-marketing response.

Data: eight-source panel of transaction lines, products, demographics, promotions, campaigns and coupons.

Hardest challenge: sources have different grains, so uncontrolled joins silently duplicate metrics.

Solution: DuckDB + Parquet, explicit facts/dimensions/bridge, QA, governed metrics, analytical marts and Power BI reconciliation.

Outcome: decision-ready retail recommendations with sample and causal limitations stated clearly.

## Questions to answer

1. Why is panel spend not retailer revenue?
2. What is the transaction grain?
3. Why is coupon a bridge?
4. What fan-out risks exist?
5. Why build a basket fact?
6. Why are dates synthetic?
7. Why is first observed purchase not acquisition?
8. How are trajectory thresholds and segments defined?
9. How is category penetration calculated?
10. Why preserve zero-sale promotion weeks?
11. Why is promotion analysis not causal?
12. How is campaign censoring handled?
13. How is demographic coverage handled?
14. How were SQL and Power BI reconciled?
15. What would inventory and margin data add?
