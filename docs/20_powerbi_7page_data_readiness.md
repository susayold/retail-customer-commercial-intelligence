# Power BI seven-page data readiness

## Status

The seven-page dashboard supplement was rebuilt from the verified retail source on 2026-09-21 and written to the Drive `05_powerbi_exports` folder. The repository now folds those supplements into the governed 46-export contract; the Drive snapshot still needs a fresh rerun to materialize the expanded set. These assets close the data/model gaps identified during the seven-page dashboard review.

The native PBIX interaction UAT remains a separate final gate after the report is built.

## New Power BI data assets

### Dimensions
- `PBIX_Dim_Category.csv` — one row per department × commodity with `category_key`.
- `PBIX_Dim_Segment.csv` — the seven deterministic customer segments.

### Week-aware analytical marts
- `PBIX_Mart_Store_Weekly.csv` — week × store; supports Top Stores and week filtering.
- `PBIX_Mart_Category_Weekly.csv` — week × category_key; keyed category trend and brand/private-label pages.
- `PBIX_Mart_Category_Household_Weekly_W001_W013.csv` through `...W092_W102.csv` — household × week × category_key. Import these with the Power Query Folder/Combine pattern. This table supplies exact DISTINCTCOUNT household denominators across arbitrary selected weeks rather than summing weekly unique counts.
- `PBIX_Mart_Brand_Category.csv` — category_key × brand_type.

### Category analyses
- `PBIX_Analysis_Category_Penetration.csv` — full-window category penetration.
- `PBIX_Analysis_Category_Decomposition_13W.csv` — exact Weeks 1–13 vs 90–102 category comparison.
- `PBIX_Private_Label_Category_Audit.csv` — category-level private-label ratio audit. The rebuild found no full-period category with private-label share above 100%; the previous web snapshot anomaly was a presentation/aggregation issue, not the governed full-period metric.

### Campaign / promotion scope
- `PBIX_Campaign_KPI_Scope.csv` — explicitly separates 7,208 household×campaign exposures / 889 redeeming exposures from 1,584 unique exposed households / 434 unique redeeming households.
- `PBIX_Promotion_Model_Audit.csv` — records that the modeled promotion universe currently contains only display_only, mailer_only and display_and_mailer. There is no modeled `none` reference, so no-promotion uplift/dependency claims are blocked.

### Root cause / decision layer
- `PBIX_Root_Cause_Panel_Spend_Periods.csv`
- `PBIX_Root_Cause_Panel_Spend_Drivers.csv`
- `PBIX_Analysis_Root_Cause_Cases.csv`
- `PBIX_Analysis_Executive_Decisions.csv`

Case A now uses the exact period-level identity:

`Panel Spend = distinct active households × baskets per active household × spend per basket`

and LMDI decomposition. Weeks 1–13 vs 90–102:
- active panel households: +33.76%, accounting for 25.81% of the observed spend change;
- trips per active household: +99.49%, accounting for 61.29%;
- spend per basket: +15.65%, accounting for 12.90%.

The three dollar contributions sum exactly to the observed panel-spend change.

### QA / manifest
- `PBIX_7Page_Supplement_QA.csv` — 11 reconciliation checks; all pass.
- `PBIX_7Page_Data_Manifest_v2.csv` — inventory of the supplemental files.

## Seven-page semantic files

Use:
- `powerbi/semantic_model_7page.yaml`
- `powerbi/measures_7page.dax`

The original six-page contract is retained for backward compatibility.

## Important semantic rules

1. Add `Dim_Week[week_number] -> Mart_Basket[week_number]` as a single-direction one-to-many relationship.
2. Use `PBIX_Dim_Category[category_key]` for the keyed category supplement tables.
3. Use `PBIX_Dim_Segment[segment]` for segment filtering.
4. Segment assignment is fixed from the full 102-week observation window; week filters change observed behavior but do not recompute the segment label.
5. Do not sum weekly unique household counts to calculate multi-week penetration. Use DISTINCTCOUNT over the household-week-category supplement.
6. Keep Page 5 language observational. The current modeled promotion universe has no valid `none` reference.
7. Keep campaign exposure and unique-household rates visibly separate.
8. Week numbers are observation indexes, not calendar dates.

## Page mapping

1. Executive Customer & Commercial Health
2. Customer Engagement & Segmentation
3. Basket & Category Intelligence
4. Category, Brand & Private Label
5. Promotion & Merchandising
6. Campaign & Coupon Intelligence
7. Root Cause & Decision Center

The data layer for these seven pages is now available. The remaining release work is native Power BI construction, interaction testing, tooltip/drill-through UAT, and final SQL/BI reconciliation after the PBIX refresh.
