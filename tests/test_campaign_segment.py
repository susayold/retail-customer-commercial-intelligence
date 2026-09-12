from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_campaign_segment_analysis_preserves_funnel_denominators_and_observability():
    sql = (ROOT / "sql/08_analysis/campaign_analysis.sql").read_text(
        encoding="utf-8"
    )
    assert "analysis_campaign_segment" in sql
    for token in (
        "recipient_households",
        "redeemer_households",
        "redemption_rate",
        "pre_28d_observable_rows",
        "during_observable_rows",
        "post_28d_observable_rows",
        "demographic_households",
        "interpretation_boundary",
    ):
        assert token in sql
