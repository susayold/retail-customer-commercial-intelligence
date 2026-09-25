# Retail Customer & Commercial Intelligence

Recruiter-facing Power BI project generated from the five-page story plan.

- 7 curated tables from Drive-backed Parquet exports
- 5 visible story pages
- Source files remain in Drive; no production Parquet/CSV is staged locally
- Refresh the Power Query sources after the connector URLs are renewed

## Build and verification

- Authored and verified with the downloaded Power BI agent at `D:\PowerBI-Codex\skills-for-fabric`.
- `powerbi-report-author validate`: 0 errors, 0 warnings.
- `powerbi-report-author preview-pages` and `preview-visuals`: 5 pages and 54 visuals discovered.
- `powerbi-desktop` bridge: project opened, reloaded, and all 5 pages rendered to PNG for QA.

## Data connection note

The report uses Power Query `Web.Contents` against the curated Drive exports, so the package contains the model and report definitions but not a local copy of the raw data. Power BI Desktop may show a refresh banner on first open; use the displayed refresh action after signing in/allowing the source if prompted. The Drive download links are temporary and may need to be renewed later.
