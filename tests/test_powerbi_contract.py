from pathlib import Path

from src.export_powerbi import POWERBI_OUTPUT_NAMES


ROOT = Path(__file__).resolve().parents[1]


def test_powerbi_model_contract_is_curated_and_six_pages():
    import yaml

    contract = yaml.safe_load(
        (ROOT / "powerbi" / "semantic_model.yaml").read_text(encoding="utf-8")
    )
    assert contract["storage_policy"] == "Drive-only"
    assert contract["raw_source_allowed"] is False
    assert len(contract["tables"]) == 29
    assert len(contract["pages"]) == 6
    assert all(item["source_file"].endswith(".parquet") for item in contract["tables"])
    assert all(item["cross_filter"] == "single" for item in contract["relationships"])
    coupon_sources = contract["pages"][-1]["source_tables"]
    assert "Mart_Coupon_Summary" in coupon_sources
    assert "Analysis_Coupon_Category" in coupon_sources
    assert "Analysis_Campaign_Segment" in coupon_sources
    assert "Analysis_Coupon_Repeat_Category" in coupon_sources
    assert "Analysis_Category_Decomposition" in contract["pages"][3]["source_tables"]
    assert "Analysis_Promotion_Dependency" in contract["pages"][4]["source_tables"]
    table_grains = {item["name"]: item.get("grain") for item in contract["tables"]}
    assert table_grains["Mart_Category_Weekly"] == "week_number, department, commodity"
    assert table_grains["Mart_Brand_Category"] == "department, commodity, brand_type"
    assert table_grains["Mart_Promotion_Category_Week"] == (
        "week_number, department, commodity, promo_state_group"
    )
    assert table_grains["Mart_Decision_Alerts"] == "metric, scope"


def test_powerbi_dax_contract_contains_governed_measures():
    dax = (ROOT / "powerbi" / "measures.dax").read_text(encoding="utf-8")
    for measure in (
        "Panel Net Spend",
        "Active Panel Households",
        "Total Recorded Discount",
        "Trips per Active Household",
        "Spend per Active Household",
        "Spend per Basket",
        "Private Label Share",
        "Coupon Basket Rate",
        "Campaign Redemption Rate",
    ):
        assert measure in dax


def test_powerbi_export_names_match_semantic_contract():
    assert POWERBI_OUTPUT_NAMES["dim_day"] == "Dim_Day"
    assert POWERBI_OUTPUT_NAMES["mart_basket"] == "Mart_Basket"
    assert POWERBI_OUTPUT_NAMES["mart_campaign_household"] == "Mart_Campaign_Household"
    assert POWERBI_OUTPUT_NAMES["analysis_coupon_category"] == "Analysis_Coupon_Category"
    assert POWERBI_OUTPUT_NAMES["analysis_category_decomposition"] == "Analysis_Category_Decomposition"
    assert POWERBI_OUTPUT_NAMES["analysis_promotion_dependency"] == "Analysis_Promotion_Dependency"
    assert POWERBI_OUTPUT_NAMES["analysis_campaign_segment"] == "Analysis_Campaign_Segment"
    assert POWERBI_OUTPUT_NAMES["analysis_coupon_repeat_category"] == "Analysis_Coupon_Repeat_Category"
    assert len(POWERBI_OUTPUT_NAMES) == 31
