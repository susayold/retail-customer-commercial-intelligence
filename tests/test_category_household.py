from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_category_household_mart_and_penetration_decomposition_exist():
    mart = (
        ROOT / "sql/06_marts/14_mart_category_household.sql"
    ).read_text(encoding="utf-8")
    analysis = (
        ROOT / "sql/08_analysis/category_analysis.sql"
    ).read_text(encoding="utf-8")
    for token in (
        "household_key",
        "category_baskets",
        "active_weeks",
        "coupon_baskets",
        "private_label_spend",
    ):
        assert token in mart
    for token in (
        "analysis_category_penetration",
        "household_penetration",
        "purchase_frequency_per_buying_household",
        "analysis_category_decomposition",
        "early_buying_households",
        "late_buying_households",
        "early_spend_per_category_basket",
        "late_spend_per_category_basket",
    ):
        assert token in analysis
