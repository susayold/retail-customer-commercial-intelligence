from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SOURCES = {
    "transaction_data", "causal_data", "coupon", "coupon_redempt",
    "campaign_table", "campaign_desc", "product", "hh_demographic",
}


def test_analysis_thresholds_are_centralized():
    thresholds = yaml.safe_load(
        (ROOT / "config/analysis_thresholds.yaml").read_text(encoding="utf-8")
    )
    assert thresholds["trajectory"]["growing_factor"] == 1.10
    assert thresholds["trajectory"]["declining_factor"] == 0.90
    assert thresholds["trajectory"]["window_weeks"] == 13
    assert thresholds["basket"]["category_pair_min_support"] == 0.01
    assert thresholds["basket"]["category_pair_min_baskets"] == 100
    assert thresholds["decision_alerts"]["relative_decline_threshold"] == -0.10
    assert thresholds["campaign"]["pre_days"] == 28
    assert thresholds["campaign"]["post_short_days"] == 14
    assert thresholds["campaign"]["post_days"] == 28


def test_expected_source_contracts_are_present():
    settings = yaml.safe_load((ROOT / "config/settings.yaml").read_text())
    assert set(settings["sources"]) == EXPECTED_SOURCES

    contracts = yaml.safe_load((ROOT / "config/source_contracts.yaml").read_text())
    assert set(contracts["sources"]) == EXPECTED_SOURCES
    assert all(item["required_columns"] for item in contracts["sources"].values())


def test_storage_policy_disallows_local_workspace_data():
    settings = yaml.safe_load((ROOT / "config/settings.yaml").read_text())
    assert settings["storage"]["local_workspace_data_allowed"] is False
    assert settings["storage"]["drive_root_env"] == "RETAIL_DRIVE_ROOT"


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
        "drive_root",
        "storage_status.json",
        "pipeline_orchestration.log",
        "storage_gate",
        "output=str(qa_root / \"storage_status.json\")",
        "cwd=str(cwd)",
        "cwd=repo_root",
        "data_root = args.data_root.resolve()",
        "artifact_root = args.artifact_root.resolve()",
        "contracts =",
        "sql_dir =",
        "args.thresholds",
        "str(thresholds)",
    ):
        assert token in runner

    assert runner.index('\"inventory\",') < runner.index('\"schema\",')


def test_makefile_exposes_drive_storage_and_quality_gate_targets():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "--output \"$$RETAIL_ARTIFACT_ROOT/04_qa_reports/storage_status.json\"" in makefile
    assert "quality-gate:" in makefile
    assert "src.enforce_quality_gate" in makefile
    assert "release-audit:" in makefile
    assert "src.release_readiness" in makefile
    for target in (
        "schema",
        "inventory",
        "profile",
        "parquet",
        "warehouse",
        "segment",
        "validate",
        "quality-gate",
        "stats",
        "powerbi",
        "release-audit",
    ):
        target_block = makefile.split(f"{target}:\n", 1)[1].split("\n\n", 1)[0]
        drive_root_token = "--drive-root " + chr(34) + "$" * 2 + "RETAIL_DRIVE_ROOT" + chr(34)
        assert drive_root_token in target_block


def test_all_data_stages_receive_drive_root():
    runner = (ROOT / "src/run_pipeline.py").read_text(encoding="utf-8")
    assert runner.count('\"--drive-root\"') >= 9


def test_standalone_data_writers_require_drive_boundary():
    stage_paths = (
        "src/inventory.py",
        "src/schema_contracts.py",
        "src/profile_sources.py",
        "src/build_parquet.py",
        "src/build_warehouse.py",
        "src/validate.py",
        "src/enforce_quality_gate.py",
        "src/statistical_validation.py",
        "src/export_powerbi.py",
        "src/segment_customers.py",
        "src/reconcile.py",
        "src/release_readiness.py",
    )
    for relative_path in stage_paths:
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "require_drive_path" in source
        assert "\"--drive-root\"" in source
        assert "required=True" in source
