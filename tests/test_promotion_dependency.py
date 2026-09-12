from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_promotion_dependency_outputs_required_plan_metrics():
    sql = (ROOT / "sql/08_analysis/promotion_analysis.sql").read_text(
        encoding="utf-8"
    )
    assert "analysis_promotion_dependency" in sql
    assert "share_of_observed_sales_during_promoted_states" in sql
    assert "share_of_product_store_weeks_promoted" in sql
    assert "Association only" in sql
