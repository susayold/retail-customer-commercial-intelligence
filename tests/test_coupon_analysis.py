from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_coupon_analysis_covers_plan_questions_and_fanout_boundaries():
    sql = (ROOT / "sql/08_analysis/coupon_analysis.sql").read_text(
        encoding="utf-8"
    )
    for table_name in (
        "analysis_coupon_campaign",
        "analysis_coupon_segment",
        "analysis_coupon_category",
        "analysis_coupon_basket",
        "analysis_coupon_repeat_category",
    ):
        assert table_name in sql
    for token in (
        "recipient_households",
        "redeemer_households",
        "redemption_rate",
        "mapped_redemption_events",
        "median_basket_net_spend",
        "first_observed_coupon_households",
        "later_observed_repeat_households",
        "interpretation_boundary",
    ):
        assert token in sql
    assert "COUNT(DISTINCT r.redemption_event_id)" in sql
    assert "not true acquisition or causal repeat" in sql
    assert "not exact redemption attribution" in sql
