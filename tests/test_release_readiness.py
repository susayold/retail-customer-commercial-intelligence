import csv
import json
from pathlib import Path

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
    for name in (
        "raw_file_inventory.csv",
        "schema_validation.csv",
        "source_profile_summary.csv",
        "source_cardinality.csv",
        "qa_run_log.csv",
    ):
        (qa_root / name).write_text("header\nrow\n", encoding="utf-8")
    (qa_root / "pipeline_orchestration.log").write_text(
        "pipeline complete\n", encoding="utf-8"
    )

    for name in (
        "stats_basket_by_segment.csv",
        "stats_promotion_state.csv",
        "stats_campaign_redemption.csv",
    ):
        stats_path = qa_root / "statistics" / name
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        stats_path.write_text("header\\nrow\\n", encoding="utf-8")

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
        [{"check_id": f"UAT-{index:02d}", "status": "pass"} for index in range(12)],
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
