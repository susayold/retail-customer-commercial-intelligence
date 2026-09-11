from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_powerbi_model_contract_is_curated_and_six_pages():
    contract = yaml.safe_load(
        (ROOT / "powerbi" / "semantic_model.yaml").read_text(encoding="utf-8")
    )
    assert contract["storage_policy"] == "Drive-only"
    assert contract["raw_source_allowed"] is False
    assert len(contract["tables"]) == 16
    assert len(contract["pages"]) == 6
    assert all(item["source_file"].endswith(".parquet") for item in contract["tables"])
    assert all(item["cross_filter"] == "single" for item in contract["relationships"])


def test_powerbi_dax_contract_contains_governed_measures():
    dax = (ROOT / "powerbi" / "measures.dax").read_text(encoding="utf-8")
    for measure in (
        "Panel Net Spend",
        "Active Households",
        "Spend per Basket",
        "Private Label Share",
        "Coupon Basket Rate",
        "Campaign Redemption Rate",
    ):
        assert measure in dax
