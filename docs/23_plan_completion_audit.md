# Non-Power BI plan completion audit

This file is the acceptance record for `retail_non_powerbi_project_strengthening_plan.md`. It separates implementation completeness from the final physical rerun of the real source files. A repository feature is not marked real-data verified merely because the code exists.

## Implementation status

| Plan layer | Implemented evidence | Status |
|---|---|---|
| Source governance | `config/source_contracts.yaml`, `src/inventory.py`, `src/schema_contracts.py`, `sql/07_quality/11_q11_source_contract_audit.sql` | Complete in code |
| Curated layer and lineage | `src/build_parquet.py`, `src/write_data_readiness.py`; row-level source, run and schema metadata | Complete in code |
| Dimensions, facts and bridge | `sql/03_dimensions/`, `sql/04_facts/`, `sql/05_bridges/` | Complete in code |
| Governed marts | `sql/06_marts/`, including category-household-week and store-week marts | Complete in code |
| Category, private label and segment analysis | `sql/08_analysis/`, including materiality, LMDI, stability and anomaly outputs | Complete in code |
| Promotion scope | `src/audit_promotion_universe.py`, `sql/08_analysis/04_promotion_universe_audit.sql` | Complete in code; no-promo claims remain blocked unless a valid `none` universe is observed |
| Campaign/coupon analytics | denominator split, observability flags, Wilson intervals and coupon-repeat wording | Complete in code |
| Root cause and decisions | `sql/08_analysis/02_root_cause_lmdi.sql`, `sql/08_analysis/05_executive_decisions.sql`, evidence builders | Complete in code |
| QA and reconciliation | source-contract QA, key/grain/reference/layer QA, quality gate and SQL-to-export reconciliation | Complete in code |
| Governed BI exports | `src/export_powerbi.py`, 46 declared artifacts and 44 semantic tables | Complete in code; current Drive snapshot predates this contract |
| Reproducibility | `src/run_pipeline.py`, run manifest, commit/hash lineage, `Makefile`, CI and fixtures | Complete in code |
| Documentation and diagrams | metric/data lineage, limitations, methodology, decision docs, four SVG diagrams, README and CV/interview package | Complete in repository |
| Web parity | `web-dashboard/` consumes governed exports and applies the promotion/private-label/self-pair guardrails | Complete in code |

## Verification gates

| Gate | Evidence | Status |
|---|---|---|
| Unit/contract tests | `97 passed` on 2026-09-22 | PASS |
| Python/JavaScript syntax | `compileall`, `node --check`, `git diff --check` | PASS |
| Web snapshot contract | `python -m src.verify_web_snapshot` | PASS |
| GitHub delivery | `main` pushed at commit `32acc9ad25b5b96e125c17d6052e9f12f148cd35` | PASS |
| Latest real-data full run | Requires the 8 raw Drive files to be visible through a local Drive mount | PENDING |
| Latest Drive release audit | Existing Drive evidence is the older 31-export snapshot; it does not prove the current 46-export contract | PENDING |

## What “100%” means here

The implementation requested by the plan is complete and pushed. The project must not be called 100% release-ready until the current commit is executed once against the eight Drive raw sources and the resulting `data_ready.json`, QA outputs, 46 exports, manifest and release audit are uploaded back to Drive. Native Power BI refresh/UAT is a separate gate after that data release.

The current machine has no Google Drive for Desktop mount. The pipeline therefore remains fail-closed and has not copied raw or curated retail data into the local checkout.
