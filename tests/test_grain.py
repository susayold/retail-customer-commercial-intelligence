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


def test_basket_mart_does_not_join_line_grain():
    sql = (ROOT / "sql/06_marts/01_mart_panel_weekly.sql").read_text()
    assert "fct_transaction_line" not in sql
