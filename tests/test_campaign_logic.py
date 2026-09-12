from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_campaign_mart_has_observability_and_separate_windows():
    sql = (ROOT / "sql/06_marts/09_mart_campaign_household.sql").read_text()
    for token in (
        "pre_28d_observable",
        "during_observable",
        "post_28d",
        "post_28d_observable",
        "redemption_count",
    ):
        assert token in sql



def test_during_window_requires_full_campaign_observation():
    sql = (ROOT / "sql/04_facts/04_fct_campaign_exposure.sql").read_text(
        encoding="utf-8"
    )
    assert "c.start_day >= o.min_day AND c.end_day <= o.max_day" in sql
