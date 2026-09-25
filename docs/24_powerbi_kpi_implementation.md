# Power BI KPI implementation

Updated the Retail Customer & Commercial Intelligence PBIP KPI layer from the
downloaded Power BI agent package.

## Scope completed

- Five visible story pages retained from the recruiter-facing plan.
- Page 1 now has the six required comparison KPIs:
  - Early 13W Panel Spend
  - Late 13W Panel Spend
  - Spend Change
  - Trips / Active HH Change
  - Spend / Basket Change
  - Late 13W Active HH
- All 24 KPI cards use the same executive treatment: short business label,
  formatted value, semantic color, 36px icon tile, delta/context line, hidden
  visual header, white rounded card, light border and subtle shadow.
- Page 1 sparklines use real weekly fields from `Dim_Week` and
  `Mart_Panel_Weekly`. Other pages intentionally omit sparklines where the
  card grain has no supported time-series baseline.
- Delta measures use early-vs-late 13-week logic on Page 1. Cards without a
  governed comparison basis display `• No prior-period comparison` rather than
  a fabricated delta.

## Validation

- `powerbi-report-author validate`: 0 errors, 0 warnings.
- PBIR layout audit: 24/24 cards have value + label + icon + delta; all cards
  are 250×105; all visual headers are hidden.
- Power BI Desktop screenshot/PDF validation remains a manual step because
  Power BI Desktop is not installed on the current machine (`DESKTOP_EXE_NOT_FOUND`).
