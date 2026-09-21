from pathlib import Path

import yaml

from src.audit_governed_assets import REQUIRED_RELATIONS
from src.export_powerbi import POWERBI_OUTPUT_NAMES


ROOT = Path(__file__).resolve().parents[1]


def test_p0_governed_sql_assets_are_present():
    expected = {
        "dim_category": ROOT / "sql/03_dimensions/08_dim_category.sql",
        "dim_segment": ROOT / "sql/03_dimensions/09_dim_segment.sql",
        "mart_category_household_weekly": ROOT / "sql/06_marts/15_mart_category_household_weekly.sql",
        "mart_store_weekly": ROOT / "sql/06_marts/16_mart_store_weekly.sql",
        "analysis_root_cause_lmdi": ROOT / "sql/08_analysis/02_root_cause_lmdi.sql",
        "analysis_campaign_denominators": ROOT / "sql/08_analysis/03_campaign_denominators.sql",
        "analysis_promotion_universe_audit": ROOT / "sql/08_analysis/04_promotion_universe_audit.sql",
        "analysis_executive_decisions": ROOT / "sql/08_analysis/05_executive_decisions.sql",
        "analysis_category_materiality": ROOT / "sql/08_analysis/z_01_category_materiality.sql",
        "analysis_category_lmdi": ROOT / "sql/08_analysis/z_02_category_lmdi.sql",
        "analysis_segment_stability": ROOT / "sql/08_analysis/z_segment_stability.sql",
        "analysis_first_observed_cohort": ROOT / "sql/08_analysis/z_first_observed_cohort.sql",
        "analysis_demographic_summary": ROOT / "sql/08_analysis/z_demographic_summary.sql",
    }
    assert set(expected) == set(REQUIRED_RELATIONS)
    assert all(path.is_file() for path in expected.values())


def test_governed_assets_preserve_plan_boundaries():
    campaign_sql = (ROOT / "sql/08_analysis/03_campaign_denominators.sql").read_text(encoding="utf-8")
    assert "campaign_household_exposures" in campaign_sql
    assert "unique_exposed_households" in campaign_sql
    assert "ci_low" in campaign_sql
    promotion_sql = (ROOT / "sql/08_analysis/04_promotion_universe_audit.sql").read_text(encoding="utf-8")
    assert "none_state_status" in promotion_sql
    assert "NOT_OBSERVED" in promotion_sql
    lmdi_sql = (ROOT / "sql/08_analysis/02_root_cause_lmdi.sql").read_text(encoding="utf-8")
    assert "reconciliation_delta" in lmdi_sql
    assert "associative accounting decomposition only" in lmdi_sql


def test_semantic_contract_contains_governed_assets_and_export_parity():
    contract = yaml.safe_load((ROOT / "powerbi/semantic_model.yaml").read_text(encoding="utf-8"))
    names = {item["name"] for item in contract["tables"]}
    assert len(names) == 44
    assert {"Dim_Category", "Dim_Segment", "Mart_Store_Weekly", "Mart_Category_Household_Weekly", "Analysis_Root_Cause_LMDI", "Analysis_Executive_Decisions"} <= names
    exported = {name for key, name in POWERBI_OUTPUT_NAMES.items() if not key.startswith("export_")}
    assert names == exported
