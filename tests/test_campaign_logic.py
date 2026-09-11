from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_campaign_mart_has_observability_and_separate_windows():
    sql = (ROOT / "sql/06_marts/09_mart_campaign_household.sql").read_text()
    for token in ("pre_28d", "during_spend", "post_28d", "post_28d_observable", "redemption_count"):
        assert token in sql