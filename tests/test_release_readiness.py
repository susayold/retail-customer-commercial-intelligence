import csv
import json
from pathlib import Path

import yaml

from src.export_powerbi import POWERBI_OUTPUT_NAMES
from src.inventory import EXPECTED_FILES
from src.release_readiness import (
    REQUIRED_POWERBI_EXPORTS,
    REQUIRED_POWERBI_MEASURES,
    REQUIRED_RECONCILIATION_METRICS,
    evaluate_release_readiness,
)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def seed_complete_delivery(artifact_root: Path, repo_root: Path) -> None:
    qa_root = artifact_root / "04_qa_reports"
    source_docs_root = artifact_root / "06_source_docs"
    qa_root.mkdir(parents=True, exist_ok=True)
    source_docs_root.mkdir(parents=True, exist_ok=True)
    (artifact_root / "05_powerbi_exports").mkdir(parents=True, exist_ok=True)

    (qa_root / "storage_status.json").write_text(
        json.dumps({"ready": True}), encoding="utf-8"
    )
    (qa_root / "qa_quality_gate.json").write_text(
        json.dumps({"ready": True}), encoding="utf-8"
    )
    (qa_root / "governed_asset_audit.json").write_text(
        json.dumps({"status": "PASS"}), encoding="utf-8"
    )
    write_csv(
        qa_root / "governed_asset_audit.csv",
        ["run_id", "asset", "relation", "row_count", "status", "error"],
        [{"run_id": "run-001", "asset": "dim_category", "relation": "dim_category", "row_count": 1, "status": "PASS", "error": ""}],
    )
    write_csv(
        qa_root / "qa_promotion_universe.csv",
        ["run_id", "metric", "value", "status", "interpretation"],
        [{
            "run_id": "run-001",
            "metric": "none_state_status",
            "value": "VALID_CONTROL",
            "status": "PASS",
            "interpretation": "A valid none-state control is present for observational comparison.",
        }],
    )
    (qa_root / "qa_promotion_universe.json").write_text(
        json.dumps(
            {
                "run_id": "run-001",
                "status": "PASS",
                "none_state_status": "VALID_CONTROL",
                "raw_zero_zero_rows": 1,
                "modeled_rows": 1,
            }
        ),
        encoding="utf-8",
    )
    (source_docs_root / "data_ready.json").write_text(
        json.dumps(
            {
                "status": "DATA_READY",
                "source_gate": "PASS",
                "curated_gate": "PASS",
                "warehouse_gate": "PASS",
                "marts_gate": "PASS",
                "governed_asset_gate": "PASS",
                "blocking_issues": 0,
            }
        ),
        encoding="utf-8",
    )
    (source_docs_root / "data_run_manifest.json").write_text(
        json.dumps(
            {
                "source_manifest_sha": "manifest-sha",
                "source_ready_verified_at": "2026-09-12T00:00:00+00:00",
                "repo_commit_sha": "repo-sha",
                "pipeline_run_id": "run-001",
                "raw_files": list(EXPECTED_FILES),
                "parquet_files": list(EXPECTED_FILES),
                "database_path": "03_duckdb_and_marts/retail_intelligence.duckdb",
                "qa_outputs": ["04_qa_reports/qa_quality_gate.json"],
                "output_files": [{"path": "05_powerbi_exports/Dim_Day.parquet", "sha256": "sha"}],
                "output_hashes": {"05_powerbi_exports/Dim_Day.parquet": "sha"},
                "started_at": "2026-09-12T00:00:00+00:00",
                "completed_at": "2026-09-12T00:00:01+00:00",
                "status": "SUCCESS",
            }
        ),
        encoding="utf-8",
    )
    write_csv(
        qa_root / "raw_file_inventory.csv",
        [
            "source_name",
            "file_name",
            "file_size_bytes",
            "file_size",
            "row_count",
            "expected_row_count",
            "row_count_delta",
            "planning_expectation_status",
            "column_count",
            "column_names_hash",
            "content_sha256",
            "checksum",
            "expected_schema_version",
            "ingestion_status",
            "load_status",
        ],
        [
            {
                "source_name": Path(name).stem,
                "file_name": name,
                "file_size_bytes": 10,
                "file_size": 10,
                "row_count": 1,
                "expected_row_count": 1,
                "row_count_delta": 0,
                "planning_expectation_status": "match",
                "column_count": 1,
                "column_names_hash": "column-hash",
                "content_sha256": f"sha-{index}",
                "checksum": f"sha-{index}",
                "expected_schema_version": "v1",
                "ingestion_status": "ok",
                "load_status": "ok",
            }
            for index, name in enumerate(EXPECTED_FILES)
        ],
    )
    write_csv(
        qa_root / "schema_validation.csv",
        [
            "source_name",
            "file_name",
            "status",
            "missing_columns",
            "unexpected_columns",
            "duplicate_columns",
            "observed_column_count",
        ],
        [
            {
                "source_name": Path(name).stem,
                "file_name": name,
                "status": "ok",
                "missing_columns": "",
                "unexpected_columns": "",
                "duplicate_columns": "",
                "observed_column_count": 1,
            }
            for name in EXPECTED_FILES
        ],
    )
    write_csv(
        qa_root / "source_profile_summary.csv",
        ["source_name", "source_filename", "row_count", "column_count"],
        [
            {
                "source_name": Path(name).stem,
                "source_filename": name,
                "row_count": 1,
                "column_count": 1,
            }
            for name in EXPECTED_FILES
        ],
    )
    write_csv(
        qa_root / "source_cardinality.csv",
        [
            "source_name",
            "source_filename",
            "column_name",
            "row_count",
            "distinct_count",
        ],
        [
            {
                "source_name": Path(name).stem,
                "source_filename": name,
                "column_name": "household_key",
                "row_count": 1,
                "distinct_count": 1,
            }
            for name in EXPECTED_FILES
        ],
    )
    write_csv(
        qa_root / "qa_run_log.csv",
        [
            "run_id",
            "timestamp",
            "file",
            "rows_read",
            "rows_written",
            "duration_seconds",
            "warnings",
            "errors",
        ],
        [{
            "run_id": "run-001",
            "timestamp": "2026-09-12T00:00:00+00:00",
            "file": "qa_layer_reconciliation.csv",
            "rows_read": 1,
            "rows_written": 1,
            "duration_seconds": "1.000",
            "warnings": "",
            "errors": "",
        }],
    )
    write_csv(
        qa_root / "qa_source_contract_audit.csv",
        ["source_name", "check_name", "violating_rows", "severity", "status", "rule"],
        [{
            "source_name": "transaction_data",
            "check_name": "required_household_key",
            "violating_rows": 0,
            "severity": "block",
            "status": "PASS",
            "rule": "household_key must be non-null",
        }],
    )
    write_csv(
        qa_root / "qa_private_label_category_anomalies.csv",
        ["category_key", "department", "commodity", "anomaly_type", "private_label_share", "denominator", "interpretation_boundary"],
        [],
    )
    (qa_root / "pipeline_orchestration.log").write_text(
        "pipeline complete\n", encoding="utf-8"
    )

    write_csv(
        qa_root / "statistics" / "stats_basket_by_segment.csv",
        ["segment", "n", "mean_basket_value", "ci_low", "ci_high", "effect_size_cohens_d", "limitation"],
        [{"segment": "High", "n": 2, "mean_basket_value": 10.0, "ci_low": 8.0, "ci_high": 12.0, "effect_size_cohens_d": 0.1, "limitation": "Observed panel comparison."}],
    )
    write_csv(
        qa_root / "statistics" / "stats_promotion_state.csv",
        ["promo_state_group", "n", "mean_panel_sales_per_product_store_week", "kruskal_wallis_p_value", "effect_size_eta_squared", "limitation"],
        [{"promo_state_group": "display_only", "n": 2, "mean_panel_sales_per_product_store_week": 5.0, "kruskal_wallis_p_value": 0.5, "effect_size_eta_squared": 0.1, "limitation": "Observed association."}],
    )
    write_csv(
        qa_root / "statistics" / "stats_campaign_redemption.csv",
        ["campaign_type", "n_recipients", "redeemers", "redemption_rate", "ci_low", "ci_high", "effect_size_cramers_v", "limitation"],
        [{"campaign_type": "TypeA", "n_recipients": 2, "redeemers": 1, "redemption_rate": 0.5, "ci_low": 0.1, "ci_high": 0.9, "effect_size_cramers_v": 0.1, "limitation": "Observed response."}],
    )
    write_csv(
        qa_root / "statistics" / "statistics_run_log.csv",
        ["run_id", "started_at_utc", "finished_at_utc", "status", "database", "output_files", "duration_seconds", "error"],
        [{
            "run_id": "run-001",
            "started_at_utc": "2026-09-12T00:00:00+00:00",
            "finished_at_utc": "2026-09-12T00:00:01+00:00",
            "status": "success",
            "database": "drive://retail_intelligence.duckdb",
            "output_files": "stats_basket_by_segment.csv|stats_promotion_state.csv|stats_campaign_redemption.csv",
            "duration_seconds": "1.000",
            "error": "",
        }],
    )

    write_csv(
        qa_root / "qa_layer_reconciliation.csv",
        ["audit_name", "status"],
        [{"audit_name": "raw_vs_fact", "status": "pass"}],
    )
    write_csv(
        qa_root / "powerbi_reconciliation.csv",
        ["metric", "sql_value", "powerbi_value", "difference", "tolerance", "status"],
        [
            {
                "metric": metric,
                "sql_value": 1,
                "powerbi_value": 1,
                "difference": 0,
                "tolerance": 0.000001,
                "status": "pass",
            }
            for metric in REQUIRED_RECONCILIATION_METRICS
        ],
    )
    write_csv(
        qa_root / "uat_results.csv",
        ["check_id", "status"],
        [{"check_id": f"UAT-{index:02d}", "status": "pass"} for index in range(1, 13)],
    )
    write_csv(
        qa_root / "root_cause_cases.csv",
        ["case_id", "status", "evidence_uri", "run_id", "limitation"],
        [
            {
                "case_id": f"Case-{index}",
                "status": "complete",
                "evidence_uri": f"drive://case-{index}",
                "run_id": "run-001",
                "limitation": "panel scope",
            }
            for index in range(3)
        ],
    )
    write_csv(
        qa_root / "executive_decisions.csv",
        ["decision_id", "status", "evidence_uri", "run_id", "limitation"],
        [
            {
                "decision_id": f"D{index:02d}",
                "status": "complete",
                "evidence_uri": f"drive://decision-{index}",
                "run_id": "run-001",
                "limitation": "observational evidence",
            }
            for index in range(1, 6)
        ],
    )

    for name in REQUIRED_POWERBI_EXPORTS:
        (artifact_root / "05_powerbi_exports" / name).write_bytes(b"parquet placeholder")

    for relative_path in (
        "docs/11_root_cause_cases.md",
        "docs/12_executive_decisions.md",
        "docs/13_limitations.md",
        "docs/14_powerbi_uat.md",
        "docs/data_lineage.md",
        "docs/metric_lineage.md",
        "assets/segmentation_flow.svg",
        "assets/decision_flow.svg",
    ):
        path = repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("delivery contract\n", encoding="utf-8")

    semantic_contract = {
        "storage_policy": "Drive-only",
        "source_folder": "05_powerbi_exports",
        "raw_source_allowed": False,
        "tables": [
            {"name": name, "source_file": f"{name}.parquet"}
            for table_name, name in POWERBI_OUTPUT_NAMES.items()
            if not table_name.startswith("export_")
        ],
        "relationships": [],
        "pages": [{"name": f"Page {index}"} for index in range(6)],
    }
    semantic_path = repo_root / "powerbi/semantic_model.yaml"
    semantic_path.parent.mkdir(parents=True, exist_ok=True)
    semantic_path.write_text(yaml.safe_dump(semantic_contract), encoding="utf-8")
    measures_path = repo_root / "powerbi/measures.dax"
    measures_path.write_text("\n".join(REQUIRED_POWERBI_MEASURES), encoding="utf-8")


def test_release_readiness_is_fail_closed_without_drive_evidence(tmp_path):
    result = evaluate_release_readiness(tmp_path / "artifacts", tmp_path / "repo")

    assert result["ready"] is False
    assert result["failure_count"] > 0
    assert any(item["name"] == "storage_policy" for item in result["failures"])
    assert any(item["name"] == "powerbi_exports" for item in result["failures"])


def test_release_readiness_passes_only_with_complete_evidence(tmp_path):
    artifact_root = tmp_path / "artifacts"
    repo_root = tmp_path / "repo"
    seed_complete_delivery(artifact_root, repo_root)

    result = evaluate_release_readiness(artifact_root, repo_root)

    assert result["ready"] is True
    assert result["failure_count"] == 0


def test_release_readiness_rejects_blank_decision_evidence(tmp_path):
    artifact_root = tmp_path / "artifacts"
    repo_root = tmp_path / "repo"
    seed_complete_delivery(artifact_root, repo_root)
    decisions = artifact_root / "04_qa_reports" / "executive_decisions.csv"
    decisions.write_text(
        "decision_id,status,evidence_uri,run_id,limitation\n"
        "D01,complete,,run-001,observational evidence\n"
        "D02,complete,drive://d02,run-001,observational evidence\n"
        "D03,complete,drive://d03,run-001,observational evidence\n"
        "D04,complete,drive://d04,run-001,observational evidence\n"
        "D05,complete,drive://d05,run-001,observational evidence\n",
        encoding="utf-8",
    )

    result = evaluate_release_readiness(artifact_root, repo_root)

    assert result["ready"] is False
    decision_check = next(
        item
        for item in result["failures"]
        if item["name"] == "04_qa_reports/executive_decisions.csv"
    )
    assert "blank" in decision_check["reason"]

def test_release_readiness_rejects_failed_reconciliation_status(tmp_path):
    artifact_root = tmp_path / "artifacts"
    repo_root = tmp_path / "repo"
    seed_complete_delivery(artifact_root, repo_root)
    reconciliation = artifact_root / "04_qa_reports" / "powerbi_reconciliation.csv"
    reconciliation.write_text(
        reconciliation.read_text(encoding="utf-8").replace(
            "Panel Net Spend,1,1,0,1e-06,pass",
            "Panel Net Spend,1,1,0,1e-06,review",
        ),
        encoding="utf-8",
    )

    result = evaluate_release_readiness(artifact_root, repo_root)

    assert result["ready"] is False
    reconciliation_check = next(
        item
        for item in result["failures"]
        if item["name"] == "04_qa_reports/powerbi_reconciliation.csv"
    )
    assert "not pass" in reconciliation_check["reason"]


def test_release_readiness_rejects_incomplete_powerbi_contract(tmp_path):
    artifact_root = tmp_path / "artifacts"
    repo_root = tmp_path / "repo"
    seed_complete_delivery(artifact_root, repo_root)
    semantic = repo_root / "powerbi" / "semantic_model.yaml"
    contract = yaml.safe_load(semantic.read_text(encoding="utf-8"))
    contract["pages"] = contract["pages"][:5]
    semantic.write_text(yaml.safe_dump(contract), encoding="utf-8")

    result = evaluate_release_readiness(artifact_root, repo_root)

    assert result["ready"] is False
    semantic_check = next(
        item for item in result["failures"] if item["name"] == "powerbi_semantic_model"
    )
    assert "6 pages" in semantic_check["reason"]


def test_release_readiness_rejects_incomplete_inventory(tmp_path):
    artifact_root = tmp_path / "artifacts"
    repo_root = tmp_path / "repo"
    seed_complete_delivery(artifact_root, repo_root)
    inventory = artifact_root / "04_qa_reports" / "raw_file_inventory.csv"
    rows = []
    with inventory.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows[0]["load_status"] = "missing"
    write_csv(inventory, list(rows[0]), rows)

    result = evaluate_release_readiness(artifact_root, repo_root)

    assert result["ready"] is False
    inventory_check = next(
        item
        for item in result["failures"]
        if item["name"] == "04_qa_reports/raw_file_inventory.csv"
    )
    assert "load_status" in inventory_check["reason"]


def test_release_readiness_rejects_invalid_uat_ids(tmp_path):
    artifact_root = tmp_path / "artifacts"
    repo_root = tmp_path / "repo"
    seed_complete_delivery(artifact_root, repo_root)
    uat = artifact_root / "04_qa_reports" / "uat_results.csv"
    uat.write_text(
        "check_id,status\n"
        + "".join(f"UAT-{index:02d},pass\n" for index in range(1, 12))
        + "UAT-99,pass\n",
        encoding="utf-8",
    )

    result = evaluate_release_readiness(artifact_root, repo_root)

    assert result["ready"] is False
    uat_check = next(
        item
        for item in result["failures"]
        if item["name"] == "04_qa_reports/uat_results.csv"
    )
    assert "UAT-12" in uat_check["reason"]
