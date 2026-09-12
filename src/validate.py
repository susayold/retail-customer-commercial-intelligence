"""Run the full transformation chain, then export QA result tables to Drive."""

from __future__ import annotations

import argparse
import csv
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.utils.duckdb_client import connect, register_raw_views


QA_TABLES = (
    "qa_source_reconciliation",
    "qa_key_audit",
    "qa_grain_audit",
    "qa_discount_audit",
    "qa_quantity_audit",
    "qa_campaign_observability",
    "qa_demographic_coverage",
    "qa_reference_coverage",
    "qa_transaction_anomalies",
)

RUN_LOG_FIELDS = [
    "run_id",
    "timestamp",
    "file",
    "rows_read",
    "rows_written",
    "duration_seconds",
    "warnings",
    "errors",
]


def run_sql_files(connection, sql_paths: list[Path]) -> None:
    for sql_path in sql_paths:
        connection.execute(sql_path.read_text(encoding="utf-8"))


def relation_row_count(connection, relation_name: str) -> int:
    value = connection.execute(
        f"SELECT COUNT(*) FROM {relation_name}"
    ).fetchone()[0]
    return int(value)


def write_run_log(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RUN_LOG_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def log_record(
    run_id: str,
    file_name: str,
    rows_read: int | None,
    rows_written: int | None,
    started_at: float,
    warnings: str = "",
    errors: str = "",
) -> dict[str, object]:
    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "file": file_name,
        "rows_read": rows_read,
        "rows_written": rows_written,
        "duration_seconds": round(time.perf_counter() - started_at, 6),
        "warnings": warnings,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--sql-dir", type=Path, default=Path("sql"))
    args = parser.parse_args()

    sql_root = args.sql_dir
    if sql_root.name == "07_quality":
        sql_root = sql_root.parent

    qa_dir = args.artifact_root / "04_qa_reports"
    database_dir = args.artifact_root / "03_duckdb_and_marts"
    qa_dir.mkdir(parents=True, exist_ok=True)
    database_dir.mkdir(parents=True, exist_ok=True)
    database = database_dir / "retail_intelligence.duckdb"
    run_id = uuid.uuid4().hex[:12]
    run_log: list[dict[str, object]] = []
    model_paths = sorted(
        path
        for path in sql_root.rglob("*.sql")
        if "07_quality" not in path.parts and "09_exports" not in path.parts
    )
    qa_paths = sorted((sql_root / "07_quality").glob("*.sql"))

    connection = connect(database)
    try:
        register_raw_views(connection, args.data_root)
        run_sql_files(connection, model_paths)
        run_sql_files(connection, qa_paths)
        for table_name in QA_TABLES:
            started_at = time.perf_counter()
            output_path = qa_dir / f"{table_name}.csv"
            try:
                rows_read = relation_row_count(connection, table_name)
                connection.execute(
                    f"COPY (SELECT * FROM {table_name}) TO ? (HEADER, DELIMITER ',')",
                    [output_path.as_posix()],
                )
                run_log.append(
                    log_record(
                        run_id,
                        output_path.name,
                        rows_read,
                        rows_read,
                        started_at,
                    )
                )
            except Exception as exc:
                run_log.append(
                    log_record(
                        run_id,
                        output_path.name,
                        None,
                        None,
                        started_at,
                        errors=f"{type(exc).__name__}: {exc}",
                    )
                )
                raise
    except Exception as exc:
        if not any(row["errors"] for row in run_log):
            run_log.append(
                log_record(
                    run_id,
                    "validate_pipeline",
                    None,
                    None,
                    time.perf_counter(),
                    errors=f"{type(exc).__name__}: {exc}",
                )
            )
        raise
    finally:
        connection.close()
        write_run_log(qa_dir / "qa_run_log.csv", run_log)


if __name__ == "__main__":
    main()
