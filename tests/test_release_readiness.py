import csv
import json
from pathlib import Path

from src.inventory import EXPECTED_FILES
from src.release_readiness import (
    REQUIRED_POWERBI_EXPORTS,
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
    qa_root.mkdir(parents=True, exist_ok=True)
    (artifact_root / "05_powerbi_exports").mkdir(parents=True, exist_ok=True)

    (qa_root / "storage_status.json").write_text(
        json.dumps({"ready": True}), encoding="utf-8"
    )
    (qa_root / "qa_quality_gate.json").write_text(
        json.dumps({"ready": True}), encoding="utf-8"
    )
    write_csv(
        qa_root / "raw_file_inventory.csv",
        [
            "file_name",
            "file_size_bytes",
            "row_count",
            "expected_row_count",
            "row_count_delta",
            "planning_expectation_status",
            "column_count",
            "column_names_hash",
            "content_sha256",
            "load_status",
        ],
        [
            {
                "file_name": name,
                "file_size_bytes": 10,
                "row_count": 1,
                "expected_row_count": 1,
                "row_count_delta": 0,
                "planning_expectation_status": "match",
                "column_count": 1,
                "column_names_hash": "column-hash",
                "content_sha256": f"sha-{index}",
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
    for name in (
        "source_profile_summary.csv",
        "source_cardinality.csv",
        "qa_run_log.csv",
    ):
        (qa_root / name).write_text("header\nrow\n", encoding="utf-8")
    (qa_root / "pipeline_orchestration.log").write_text(
        "pipeline complete\n", encoding="utf-8"
    )

    write_csv(
        qa_root / "statistics" / "stats_basket_by_segment.csv",
        ["segment", "n", "mean_basket_value", "ci_low", "ci_high"],
        [{"segment": "High", "n": 2, "mean_basket_value": 10.0, "ci_low": 8.0, "ci_high": 12.0}],
    )
    write_csv(
        qa_root / "statistics" / "stats_promotion_state.csv",
        ["promo_state_group", "n", "mean_panel_sales_per_product_store_week", "kruskal_wallis_p_value"],
        [{"promo_state_group": "display_only", "n": 2, "mean_panel_sales_per_product_store_week": 5.0, "kruskal_wallis_p_value": 0.5}],
    )
    write_csv(
        qa_root / "statistics" / "stats_campaign_redemption.csv",
        ["campaign_type", "n_recipients", "redeemers", "redemption_rate", "ci_low", "ci_high"],
        [{"campaign_type": "TypeA", "n_recipients": 2, "redeemers": 1, "redemption_rate": 0.5, "ci_low": 0.1, "ci_high": 0.9}],
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
                "metric": f"metric_{index}",
                "sql_value": 1,
                "powerbi_value": 1,
                "difference": 0,
                "tolerance": 0.000001,
                "status": "pass",
            }
            for index in range(8)
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
        "powerbi/semantic_model.yaml",
        "powerbi/measures.dax",
    ):
        path = repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("delivery contract\n", encoding="utf-8")


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

def test_release_readiness_rejects_incomplete_inventory(tmp_path):
    artifact_root = tmp_path / "artifacts"
    repo_root = tmp_path / "repo"
    seed_complete_delivery(artifact_root, repo_root)
    inventory = artifact_root / "04_qa_reports" / "raw_file_inventory.csv"
    inventory.write_text(
        inventory.read_text(encoding="utf-8").replace(
            "transaction_data.csv,10,1,1,0,match,1,column-hash,sha-0,ok",
            "transaction_data.csv,10,1,1,0,match,1,column-hash,sha-0,missing",
        ),
        encoding="utf-8",
    )

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
