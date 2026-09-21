"""Run the complete non-native-Power-BI retail DA rebuild.

This runner deliberately keeps source data and generated artifacts under the
declared Drive root.  The repository checkout is code-only and is never used
as an artifact root.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def run_stage(stage: str, command: list[str], repo_root: Path) -> None:
    started = time.perf_counter()
    print(json.dumps({"stage": stage, "event": "start", "command": command}, ensure_ascii=False), flush=True)
    subprocess.run(command, check=True, cwd=repo_root)
    print(
        json.dumps(
            {"stage": stage, "event": "complete", "duration_seconds": round(time.perf_counter() - started, 3)},
            ensure_ascii=False,
        ),
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run retail DA through DATA_READY, excluding native Power BI.")
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--drive-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()

    repo_root = args.repo_root.expanduser().resolve()
    data_root = args.data_root.expanduser().resolve()
    artifact_root = args.artifact_root.expanduser().resolve()
    drive_root = args.drive_root.expanduser().resolve()
    qa_root = artifact_root / "04_qa_reports"
    database = artifact_root / "03_duckdb_and_marts" / "retail_intelligence.duckdb"
    pipeline_run_id = f"da_no_native_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}"
    started_at = datetime.now(timezone.utc).isoformat()

    common = ["--drive-root", str(drive_root)]
    stages: list[tuple[str, list[str]]] = [
        (
            "storage_gate",
            [sys.executable, "-m", "src.storage_policy", "--data-root", str(data_root), "--artifact-root", str(artifact_root), *common, "--repo-root", str(repo_root), "--output", str(qa_root / "storage_status.json")],
        ),
        ("source_ready_gate", [sys.executable, "-m", "src.verify_source_ready", *common]),
        (
            "schema",
            [sys.executable, "-m", "src.schema_contracts", "--input", str(data_root), "--contracts", str(repo_root / "config" / "source_contracts.yaml"), "--output", str(qa_root / "schema_validation.csv"), *common],
        ),
        (
            "inventory",
            [sys.executable, "-m", "src.inventory", "--input", str(data_root), "--output", str(qa_root / "raw_file_inventory.csv"), *common],
        ),
        ("profile", [sys.executable, "-m", "src.profile_sources", "--data-root", str(data_root), "--artifact-root", str(artifact_root), *common]),
        (
            "parquet",
            [sys.executable, "-m", "src.build_parquet", "--input", str(data_root), "--output", str(artifact_root / "02_curated_parquet"), "--inventory", str(qa_root / "raw_file_inventory.csv"), "--pipeline-run-id", pipeline_run_id, *common],
        ),
        (
            "warehouse",
            [sys.executable, "-m", "src.build_warehouse", "--data-root", str(data_root), "--artifact-root", str(artifact_root), "--sql-dir", str(repo_root / "sql"), "--thresholds", str(repo_root / "config" / "analysis_thresholds.yaml"), *common],
        ),
        (
            "validate",
            [sys.executable, "-m", "src.validate", "--data-root", str(data_root), "--artifact-root", str(artifact_root), "--sql-dir", str(repo_root / "sql"), "--thresholds", str(repo_root / "config" / "analysis_thresholds.yaml"), *common],
        ),
        ("promotion_universe_audit", [sys.executable, "-m", "src.audit_promotion_universe", "--database", str(database), "--data-root", str(data_root), "--artifact-root", str(artifact_root), *common, "--run-id", pipeline_run_id]),
        ("governed_asset_audit", [sys.executable, "-m", "src.audit_governed_assets", "--database", str(database), "--artifact-root", str(artifact_root), *common, "--run-id", pipeline_run_id]),
        ("quality_gate", [sys.executable, "-m", "src.enforce_quality_gate", "--artifact-root", str(artifact_root), *common]),
        ("statistics", [sys.executable, "-m", "src.statistical_validation", "--database", str(database), "--artifact-root", str(artifact_root), *common]),
        ("real_evidence", [sys.executable, "-m", "src.build_real_evidence", "--artifact-root", str(artifact_root), *common]),
        ("powerbi_analytical_exports", [sys.executable, "-m", "src.export_powerbi", "--artifact-root", str(artifact_root), "--sql-dir", str(repo_root / "sql"), "--format", "parquet", "--run-id", pipeline_run_id, *common]),
        ("metric_totals", [sys.executable, "-m", "src.build_metric_totals", "--artifact-root", str(artifact_root), *common]),
        ("uat_contract", [sys.executable, "-m", "src.build_uat_evidence", "--artifact-root", str(artifact_root), *common]),
        (
            "data_readiness",
            [sys.executable, "-m", "src.write_data_readiness", "--artifact-root", str(artifact_root), *common, "--repo-root", str(repo_root), "--pipeline-run-id", pipeline_run_id, "--started-at", started_at],
        ),
    ]

    qa_root.mkdir(parents=True, exist_ok=True)
    orchestration_log = qa_root / "pipeline_orchestration.log"
    with orchestration_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": "run_start", "pipeline_run_id": pipeline_run_id, "started_at": started_at}) + "\n")
        for stage, command in stages:
            try:
                run_stage(stage, command, repo_root)
                handle.write(json.dumps({"stage": stage, "event": "complete", "pipeline_run_id": pipeline_run_id}) + "\n")
                handle.flush()
            except subprocess.CalledProcessError as error:
                handle.write(json.dumps({"stage": stage, "event": "failed", "return_code": error.returncode, "pipeline_run_id": pipeline_run_id}) + "\n")
                handle.flush()
                raise

    run_stage("tests_final", [sys.executable, "-m", "pytest", "-q"], repo_root)
    print(json.dumps({"status": "DA_ANALYSIS_READY", "pipeline_run_id": pipeline_run_id, "orchestration_log": str(orchestration_log)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
