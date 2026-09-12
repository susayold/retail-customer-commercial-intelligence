from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_category_mart_declares_panel_penetration():
    sql = (ROOT / "sql/06_marts/06_mart_category_weekly.sql").read_text()
    assert "active_panel_households" in sql
    assert "category_penetration" in sql



def test_category_weekly_grain_includes_department():
    contract = (ROOT / "docs/04_grain_and_join_contracts.md").read_text(
        encoding="utf-8"
    )
    assert "department × commodity × week" in contract
    assert "three-column key" in contract
