from pathlib import Path

from src.sql_renderer import render_sql_file

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = ROOT / "config/analysis_thresholds.yaml"


def test_campaign_mart_has_observability_and_separate_windows():
    sql = render_sql_file(
        ROOT / "sql/06_marts/09_mart_campaign_household.sql",
        THRESHOLDS,
    )
    for token in (
        "pre_28d_observable",
        "during_observable",
        "post_28d",
        "post_28d_observable",
        "redemption_count",
    ):
        assert token in sql



def test_during_window_requires_full_campaign_observation():
    sql = render_sql_file(
        ROOT / "sql/04_facts/04_fct_campaign_exposure.sql",
        THRESHOLDS,
    )
    assert "c.start_day >= o.min_day AND c.end_day <= o.max_day" in sql

def test_campaign_windows_are_configured_and_rendered():
    config = (THRESHOLDS).read_text(encoding="utf-8")
    assert "pre_days: 28" in config
    assert "post_short_days: 14" in config
    assert "post_days: 28" in config
