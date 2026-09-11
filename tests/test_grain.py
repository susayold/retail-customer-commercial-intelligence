from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_grain_contract_documented_for_core_facts():
    text = (ROOT / "docs/04_grain_and_join_contracts.md").read_text()
    for phrase in (
        "one product line in basket",
        "one basket",
        "product × store × week",
        "household × campaign",
        "coupon UPC × product × campaign",
    ):
        assert phrase in text


def test_basket_metrics_are_aggregated_before_line_level_private_label_join():
    sql = (ROOT / "sql/06_marts/01_mart_panel_weekly.sql").read_text()
    basket_cte = sql.split("private_label_weekly AS", maxsplit=1)[0]
    assert "FROM fct_basket" in basket_cte
    assert "fct_transaction_line" not in basket_cte
