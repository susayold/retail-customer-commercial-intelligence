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
    relationships = {
        (item["from"], item["to"])
        for item in contract["relationships"]
    }
    assert (
        "Dim_Week[week_number]",
        "Mart_Category_Weekly[week_number]",
    ) in relationships
    assert (
        "Dim_Week[week_number]",
        "Mart_Promotion_Category_Week[week_number]",
    ) in relationships


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
        "Category Household Penetration",
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


def test_powerbi_tables_match_exporter_contract():
    import yaml

    contract = yaml.safe_load(
        (ROOT / "powerbi" / "semantic_model.yaml").read_text(encoding="utf-8")
    )
    semantic_tables = {item["name"] for item in contract["tables"]}
    exported_curated_tables = {
        output_name
        for table_name, output_name in POWERBI_OUTPUT_NAMES.items()
        if not table_name.startswith("export_")
    }
    assert semantic_tables == exported_curated_tables



def test_sql_reconciliation_uses_governed_panel_household_label():
    sql = (
        ROOT / "sql/09_exports/01_powerbi_metric_reconciliation.sql"
    ).read_text(encoding="utf-8")
    assert "'Active Panel Households'" in sql
    assert "'Active Households'" not in sql



def test_declared_grains_and_relationship_columns_exist_in_synthetic_warehouse():
    import yaml

    from src.utils.duckdb_client import connect, register_raw_views

    contract = yaml.safe_load(
        (ROOT / "powerbi" / "semantic_model.yaml").read_text(encoding="utf-8")
    )
    connection = connect(":memory:")
    try:
        register_raw_views(connection, ROOT / "tests/fixtures")
        sql_root = ROOT / "sql"
        model_paths = sorted(
            path
            for path in sql_root.rglob("*.sql")
            if "07_quality" not in path.parts and "09_exports" not in path.parts
        )
        for sql_path in model_paths:
            connection.execute(sql_path.read_text(encoding="utf-8"))

        output_to_table = {value: key for key, value in POWERBI_OUTPUT_NAMES.items()}
        for item in contract["tables"]:
            table_name = output_to_table[item["name"]]
            columns = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = ?
                    """,
                    [table_name],
                ).fetchall()
            }
            for field in item.get("grain", "").split(","):
                assert field.strip() in columns, (
                    f"{item['name']} grain field {field.strip()} is missing"
                )

        for relationship in contract["relationships"]:
            from_table, from_column = relationship["from"].split("[")
            to_table, to_column = relationship["to"].split("[")
            assert from_table in output_to_table
            assert to_table in output_to_table
            assert from_column.rstrip("]") in {
                row[0]
                for row in connection.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = ?
                    """,
                    [output_to_table[from_table]],
                ).fetchall()
            }
            assert to_column.rstrip("]") in {
                row[0]
                for row in connection.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = ?
                    """,
                    [output_to_table[to_table]],
                ).fetchall()
            }
    finally:
        connection.close()
