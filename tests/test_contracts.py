from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SOURCES = {
    "transaction_data", "causal_data", "coupon", "coupon_redempt",
    "campaign_table", "campaign_desc", "product", "hh_demographic",
}


def test_expected_source_contracts_are_present():
    settings = yaml.safe_load((ROOT / "config/settings.yaml").read_text())
    assert set(settings["sources"]) == EXPECTED_SOURCES

    contracts = yaml.safe_load((ROOT / "config/source_contracts.yaml").read_text())
    assert set(contracts["sources"]) == EXPECTED_SOURCES
    assert all(item["required_columns"] for item in contracts["sources"].values())


def test_storage_policy_disallows_local_workspace_data():
    settings = yaml.safe_load((ROOT / "config/settings.yaml").read_text())
    assert settings["storage"]["local_workspace_data_allowed"] is False


def test_segments_have_fallback():
    rules = yaml.safe_load((ROOT / "config/segmentation_rules.yaml").read_text())
    assert any("Low-Engagement" in item["name"] for item in rules["rules"])


def test_one_command_runner_uses_drive_roots_for_data_artifacts():
    runner = (ROOT / "src/run_pipeline.py").read_text(encoding="utf-8")
    for token in (
        "src.storage_policy",
        "src.schema_contracts",
        "src.inventory",
        "src.profile_sources",
        "src.build_parquet",
        "src.build_warehouse",
        "src.validate",
        "src.enforce_quality_gate",
        "src.statistical_validation",
        "src.export_powerbi",
        "pipeline_orchestration.log",
        "artifact_root",
        "storage_status.json",
        "cwd=str(cwd)",
        "cwd=repo_root",
        "data_root = args.data_root.resolve()",
        "artifact_root = args.artifact_root.resolve()",
        "contracts =",
        "sql_dir =",
    ):
        assert token in runner


    assert runner.index('"inventory",') < runner.index('"schema",')
