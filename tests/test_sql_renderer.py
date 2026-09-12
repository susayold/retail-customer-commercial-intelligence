from pathlib import Path

import pytest

from src.sql_renderer import load_thresholds, render_sql_file, render_sql_text


ROOT = Path(__file__).resolve().parents[1]


def test_sql_renderer_expands_configured_analysis_thresholds():
    thresholds = load_thresholds(ROOT / "config/analysis_thresholds.yaml")
    sql = render_sql_file(
        ROOT / "sql/06_marts/04_mart_customer_segment.sql",
        ROOT / "config/analysis_thresholds.yaml",
    )

    assert thresholds["TRAJECTORY_GROWING_FACTOR"] == 1.10
    assert "{" not in sql
    assert "coupon_basket_rate >= 0.3" in sql
    assert "private_label_share >= 0.6" in sql


def test_sql_renderer_fails_closed_on_missing_threshold():
    with pytest.raises(KeyError, match="MISSING"):
        render_sql_text("SELECT {{ MISSING }}", {})


def test_category_analysis_uses_centralized_trajectory_thresholds():
    sql = render_sql_file(
        ROOT / "sql/08_analysis/category_analysis.sql",
        ROOT / "config/analysis_thresholds.yaml",
    )

    assert "late_spend >= early_spend * 1.1" in sql
    assert "late_spend <= early_spend * 0.9" in sql
    assert "{{" not in sql

def test_shared_window_and_cross_category_thresholds_are_rendered():
    household_sql = render_sql_file(
        ROOT / "sql/06_marts/03_mart_household_summary.sql",
        ROOT / "config/analysis_thresholds.yaml",
    )
    category_sql = render_sql_file(
        ROOT / "sql/08_analysis/category_analysis.sql",
        ROOT / "config/analysis_thresholds.yaml",
    )
    cross_category_sql = render_sql_file(
        ROOT / "sql/06_marts/12_mart_cross_category_pair.sql",
        ROOT / "config/analysis_thresholds.yaml",
    )

    assert "b.min_week + 13 - 1" in household_sql
    assert "b.max_week - 13" in household_sql
    assert "b.min_week + 13 - 1" in category_sql
    assert "b.max_week - 13" in category_sql
    assert "p.pair_baskets >= 100" in cross_category_sql
    assert ">= 0.01" in cross_category_sql
    assert "{{" not in household_sql + category_sql + cross_category_sql
