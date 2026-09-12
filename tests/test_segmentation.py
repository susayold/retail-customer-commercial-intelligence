from pathlib import Path

import yaml

from src.sql_renderer import render_sql_file

ROOT = Path(__file__).resolve().parents[1]


def test_segmentation_rules_have_a_fallback_and_explicit_priority():
    rules = yaml.safe_load((ROOT / "config/segmentation_rules.yaml").read_text())["rules"]
    assert any(rule["name"] == "Low-Engagement" for rule in rules)
    assert all("priority" in rule for rule in rules)


def test_high_value_engaged_requires_observed_trajectory():
    sql = render_sql_file(
        ROOT / "sql/06_marts/04_mart_customer_segment.sql",
        ROOT / "config/analysis_thresholds.yaml",
    )
    assert (
        "monetary_quintile >= 4 AND trajectory IN ('Growing', 'Stable')"
        in sql
    )
