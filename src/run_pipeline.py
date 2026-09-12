"""Run the Drive-backed retail pipeline in a dependency-safe order."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def run_command(
    stage: str,
    command: list[str],
    cwd: Path | None = None,
) -> None:
    started = time.perf_counter()
    print(
        json.dumps(
            {
                "stage": stage,
                "event": "start",
                "command": command,
                "cwd": str(cwd) if cwd else None,
            }
        )
    )
    subprocess.run(command, check=True, cwd=str(cwd) if cwd else None)
    print(
        json.dumps(
            {
                "stage": stage,
                "event": "complete",
                "duration_seconds": round(time.perf_counter() - started, 3),
            }
        )
    )


def log_event(handle, stage: str, event: str, **details: object) -> None:
    payload = {
        "stage": stage,
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **details,
    }
    handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    handle.flush()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run inventory, QA, warehouse, statistics and BI exports using Drive paths."
    )
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--contracts", type=Path, default=Path("config/source_contracts.yaml"))
    parser.add_argument("--sql-dir", type=Path, default=Path("sql"))
    parser.add_argument("--with-tests", action="store_true")
    args = parser.parse_args()

    data_root = args.data_root.resolve()
    artifact_root = args.artifact_root.resolve()
    repo_root = args.repo_root.resolve()
    contracts = (
        args.contracts
        if args.contracts.is_absolute()
        else repo_root / args.contracts
    )
    sql_dir = (
        args.sql_dir
        if args.sql_dir.is_absolute()
        else repo_root / args.sql_dir
    )
    qa_root = artifact_root / "04_qa_reports"
    parquet_root = artifact_root / "02_curated_parquet"
    database = artifact_root / "03_duckdb_and_marts" / "retail_intelligence.duckdb"

    storage_command = [
        sys.executable,
        "-m",
        "src.storage_policy",
        "--data-root",
        str(data_root),
        "--artifact-root",
        str(artifact_root),
        "--repo-root",
        str(repo_root),
    ]
    run_command("storage_gate", storage_command, cwd=repo_root)

    qa_root.mkdir(parents=True, exist_ok=True)
    log_path = qa_root / "pipeline_orchestration.log"
    with log_path.open("a", encoding="utf-8") as log_handle:
        log_event(log_handle, "storage_gate", "complete")

        stages: list[tuple[str, list[str]]] = [
            (
                "schema",
                [
                    sys.executable,
                    "-m",
                    "src.schema_contracts",
                    "--input",
                    str(data_root),
                    "--contracts",
                    str(contracts),
                    "--output",
                    str(qa_root / "schema_validation.csv"),
                ],
            ),
            (
                "inventory",
                [
                    sys.executable,
                    "-m",
                    "src.inventory",
                    "--input",
                    str(data_root),
                    "--output",
                    str(qa_root / "raw_file_inventory.csv"),
                ],
            ),
            (
                "profile",
                [
                    sys.executable,
                    "-m",
                    "src.profile_sources",
                    "--data-root",
                    str(data_root),
                    "--artifact-root",
                    str(artifact_root),
                ],
            ),
            (
                "parquet",
                [
                    sys.executable,
                    "-m",
                    "src.build_parquet",
                    "--input",
                    str(data_root),
                    "--output",
                    str(parquet_root),
                ],
            ),
            (
                "warehouse",
                [
                    sys.executable,
                    "-m",
                    "src.build_warehouse",
                    "--data-root",
                    str(data_root),
                    "--artifact-root",
                    str(artifact_root),
                    "--sql-dir",
                    str(sql_dir),
                ],
            ),
            (
                "validate",
                [
                    sys.executable,
                    "-m",
                    "src.validate",
                    "--data-root",
                    str(data_root),
                    "--artifact-root",
                    str(artifact_root),
                    "--sql-dir",
                    str(sql_dir),
                ],
            ),
            (
                "statistics",
                [
                    sys.executable,
                    "-m",
                    "src.statistical_validation",
                    "--database",
                    str(database),
                    "--artifact-root",
                    str(artifact_root),
                ],
            ),
            (
                "powerbi_exports",
                [
                    sys.executable,
                    "-m",
                    "src.export_powerbi",
                    "--artifact-root",
                    str(artifact_root),
                    "--sql-dir",
                    str(sql_dir),
                    "--format",
                    "parquet",
                ],
            ),
        ]
        for stage, command in stages:
            started = time.perf_counter()
            log_event(log_handle, stage, "start", command=command)
            try:
                run_command(stage, command, cwd=repo_root)
            except subprocess.CalledProcessError as error:
                log_event(
                    log_handle,
                    stage,
                    "failed",
                    return_code=error.returncode,
                    duration_seconds=round(time.perf_counter() - started, 3),
                )
                raise
            log_event(
                log_handle,
                stage,
                "complete",
                duration_seconds=round(time.perf_counter() - started, 3),
            )

        if args.with_tests:
            started = time.perf_counter()
            test_command = [sys.executable, "-m", "pytest", "-q"]
            log_event(log_handle, "tests", "start", command=test_command)
            run_command("tests", test_command, cwd=repo_root)
            log_event(
                log_handle,
                "tests",
                "complete",
                duration_seconds=round(time.perf_counter() - started, 3),
            )

    print(json.dumps({"status": "complete", "orchestration_log": str(log_path)}))


if __name__ == "__main__":
    main()
