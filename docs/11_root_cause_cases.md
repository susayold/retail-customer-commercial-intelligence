# Root-cause case studies

These cases are populated from the verified Drive-backed non-native rebuild. Every numeric claim below is scoped to the observed panel, linked to Drive evidence and paired with its limitation.

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
| Active Panel Households | 1,739 | 2,326 | +587 | Reconciled panel denominator |
| Trips per Active Household | 8.00 | 15.96 | +99.49% | Largest driver movement in the selected windows |
| Spend per Basket | $27.60 | $31.92 | +15.65% | Mix-sensitive accounting component |
| Panel Net Spend | $384,068.32 | $1,185,148.81 | +208.58% | Identity reconciles within QA tolerance |

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
| Buying households / penetration | 28 | 1 | -27 | Largest observed erosion category |
| Trips per buying household | 1.07 | 1.00 | -0.07 | Category decomposition branch |
| Spend per category basket | $15.68 | $1.98 | -87.37% | Mix-sensitive, within-panel |
| Category spend | $470.42 | $1.98 | -99.58% | DRUG GM / LAWN AND GARDEN SHOP |

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
| Campaign reach | 65 | eligible panel households | 65 eligible recipients | 65 post-28-day observable rows | exposure, not response |
| Redemption | 1 | recipient households | 1.54% | 65 post-28-day observable rows | campaign/coupon response |
| Related-product purchase | see export | redeemers / mapped events | see export | bridge-controlled | bridge-controlled |
| Observed repeat | see export | eligible prior purchasers | see export | observability retained | first-observed logic |

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

## Verified real-data run — 2026-09-14

The Drive-backed run completed with source run ID `source_rebuild_20260914_private_label` and pipeline run ID `da_no_native_20260913T213859Z_341c1744`. The three cases are recorded in `04_qa_reports/root_cause_cases.csv` and are linked to the QA and curated export evidence.

- Case A: no decline was observed between the first and last 13-week windows. Panel Net Spend moved from `$384,068.32` to `$1,185,148.81` (`+208.58%`); the largest reconciled driver movement was Trips per Active Household (`+99.49%`). This is an accounting decomposition, not causal attribution.
- Case B: the largest relative observed erosion was `DRUG GM / LAWN AND GARDEN SHOP` (`-99.58%` spend), with buying households down 27 and category baskets down 29.
- Case C: campaign 6 (TypeC) had the weakest observed redemption among campaigns with at least 50 recipients: 1/65 (`1.54%`), with 65 post-28-day observable rows.

The blocking QA gate is `READY`; anomalies remain retained for review rather than deleted. The Drive evidence index is the `04_qa_reports` folder and the exact artifact names are listed in the CSV.

The semantic repair is also complete: `Private`/`National` production values are normalized centrally, raw private-label share is independently reconciled at `27.7663%`, and segmentation assigns exactly one label to each of 2,500 households. The private-label candidate set is 28 households at the configured 60% threshold; precedence leaves 15 final `Private-Label Loyal` assignments.

