# Root-cause case studies

These cases are decision templates until the Drive data run produces verified outputs. Never replace a placeholder with a number unless the linked Drive artifact, QA status and metric definition are available.

## Evidence contract for every case

Record the following before writing the finding:

| Field | Required evidence |
|---|---|
| Scope | panel boundary, observation weeks and eligible population |
| Baseline/current | exact windows, denominators and null/observability treatment |
| Grain | model grain used for the comparison |
| QA | relevant QA table, reconciliation status and run ID |
| Finding | value, direction, magnitude and sample size |
| Interpretation | accounting explanation versus causal claim |
| Action | test, intervention or monitoring change |
| Limitation | censoring, targeting bias, panel coverage or missing economics |

## Case A — Panel spend decline

### Business question

What explains a change in Panel Net Spend: fewer active panel households, fewer trips per active household or lower spend per basket?

### Driver tree

`Panel Net Spend = Active Panel Households × Trips per Active Household × Spend per Basket`

### Required evidence

- `mart_panel_weekly` for the selected observation windows;
- `mart_decision_alerts` to identify candidate decline weeks; its threshold is applied to relative variance while absolute variance is retained for sizing;
- `qa_source_reconciliation.csv` and `qa_basket_reconciliation.csv`;
- segment-level movement from `mart_customer_segment`;
- category contribution from `mart_category_weekly`;
- active population and basket denominators.

### Completion table

| Driver | Baseline | Current | Absolute change | Contribution / interpretation |
|---|---:|---:|---:|---|
| Active Panel Households | pending | pending | pending | pending |
| Trips per Active Household | pending | pending | pending | pending |
| Spend per Basket | pending | pending | pending | pending |
| Panel Net Spend | pending | pending | pending | identity must reconcile |

### Decision rule

- Use `mart_decision_alerts` only as a candidate-week alert; confirm the driver with the reconciled identity and treat the threshold as relative variance.
- If active households are the primary movement, prioritize reach/re-engagement diagnostics.
- If trips per household are the primary movement, investigate visit cadence and high-value declining households.
- If spend per basket is the primary movement, investigate category mix, basket breadth and discount behavior.
- If the identity does not reconcile within tolerance, stop the case and resolve metric lineage first.

## Case B — Category erosion

### Business question

Is a category weakening because fewer households buy it, buying households visit less often, or category baskets are smaller?

### Driver tree

`Category Spend = Buying Households × Trips per Buying Household × Spend per Category Basket`

### Required evidence

- `mart_category_household` at household × department × commodity grain;
- `analysis_category_penetration` and `analysis_category_decomposition`;
- category weekly spend and basket metrics;
- private-label share and national/private mix;
- promotion state and cross-category attach;
- minimum sample-size and QA checks.

### Completion table

| Diagnostic | Baseline | Current | Change | Interpretation |
|---|---:|---:|---:|---|
| Buying households / penetration | pending | pending | pending | pending |
| Trips per buying household | pending | pending | pending | pending |
| Spend per category basket | pending | pending | pending | pending |
| Category spend | pending | pending | pending | pending |

### Decision rule

Do not call a category “declining” from spend alone. Require at least one supporting decomposition branch and a reviewed sample size. Use “observed category erosion within the panel” rather than a market-level claim.

## Case C — Weak campaign or coupon response

### Business question

Which campaign or customer segment shows the strongest observed response after accounting for exposure, redemption, related-product validation and post-period observability?

### Funnel

`recipient households → redeemer households → validated related-product purchase → observable repeat purchase`

### Required evidence

- `analysis_campaign_segment` with recipient/redeemer counts and observability;
- `analysis_coupon_campaign`, `analysis_coupon_segment`, `analysis_coupon_category`, `analysis_coupon_basket` and `analysis_coupon_repeat_category`;
- `qa_campaign_observability.csv`;
- coupon bridge/reference coverage and fan-out checks;
- pre/during/post averages with NULL preserved outside the observation horizon.

### Completion table

| Funnel stage | Numerator | Denominator | Rate | Observable rows | Interpretation |
|---|---:|---:|---:|---:|---|
| Campaign reach | pending | eligible panel households | pending | pending | exposure, not response |
| Redemption | pending | recipient households | pending | pending | campaign/coupon response |
| Related-product purchase | pending | redeemers / mapped events | pending | pending | bridge-controlled |
| Observed repeat | pending | eligible prior purchasers | pending | pending | first-observed logic |

### Decision rule

Use response rates only with their denominators and observability counts. Treat targeted campaign comparisons as descriptive association; do not claim causal lift or ROI without a valid control design, cost and margin data.

## Case D — Promotion dependency (optional after core v1)

Compare none, display-only, mailer-only and display-and-mailer states using `analysis_promotion_association` and `analysis_promotion_dependency`. Preserve zero-sale product-store-week rows, show sample sizes and use association wording.

## Finalization gate

Cases A–C are complete only when each has:

1. a Drive output link and run ID;
2. a reconciled metric and declared grain;
3. a quantified finding with denominator/sample size;
4. an action and monitoring KPI;
5. an explicit limitation.

