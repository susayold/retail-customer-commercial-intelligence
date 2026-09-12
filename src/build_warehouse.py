"""Run SQL models against Drive-backed sources and write the warehouse to Drive."""

from __future__ import annotations

import argparse
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.sql_renderer import render_sql_file
from src.storage_paths import require_drive_path
from src.utils.duckdb_client import connect, register_raw_views

CREATE_TABLE_RE = re.compile(
    r"CREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)
RELATION_RE = re.compile(
    r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("retail_pipeline")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


def output_table_names(sql_text: str) -> list[str]:
    """Return every table created by a SQL file, preserving statement order."""
    return CREATE_TABLE_RE.findall(sql_text)


def output_table_name(sql_text: str) -> str | None:
    """Return the first created table for backward-compatible callers."""
    names = output_table_names(sql_text)
    return names[0] if names else None


def referenced_relations(sql_text: str, available: set[str]) -> set[str]:
    return {name for name in RELATION_RE.findall(sql_text) if name in available}


def relation_count(connection, relation: str, cache: dict[str, int]) -> int:
    if relation not in cache:
        cache[relation] = int(
            connection.execute(f"SELECT COUNT(*) FROM {relation}").fetchone()[0]
        )
    return cache[relation]


def available_relations(connection) -> set[str]:
    rows = connection.execute(
        "SELECT table_name FROM information_schema.tables"
    ).fetchall()
    return {row[0] for row in rows}


def log_run(
    logger: logging.Logger,
    run_id: str,
    file_name: str,
    rows_read: int,
    rows_written: int,
    duration_seconds: float,
    warnings: str = "",
    errors: str = "",
) -> None:
    logger.info(
        "run_id=%s timestamp=%s file=%s rows_read=%s rows_written=%s duration_seconds=%.3f warnings=%s errors=%s",
        run_id,
        datetime.now(timezone.utc).isoformat(),
        file_name,
        rows_read,
        rows_written,
        duration_seconds,
        warnings,
        errors,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--database", type=Path, default=None)
    parser.add_argument("--drive-root", type=Path, required=True)
    parser.add_argument("--sql-dir", type=Path, default=Path("sql"))
    parser.add_argument(
        "--thresholds", type=Path, default=Path("config/analysis_thresholds.yaml")
    )
    args = parser.parse_args()

    data_root = require_drive_path(args.data_root, args.drive_root, "--data-root")
    artifact_root = require_drive_path(args.artifact_root, args.drive_root, "--artifact-root")
    warehouse_dir = artifact_root / "03_duckdb_and_marts"
    qa_dir = artifact_root / "04_qa_reports"
    warehouse_dir.mkdir(parents=True, exist_ok=True)
    qa_dir.mkdir(parents=True, exist_ok=True)
    database = (
        require_drive_path(args.database, args.drive_root, "--database")
        if args.database is not None
        else warehouse_dir / "retail_intelligence.duckdb"
    )
    thresholds_path = args.thresholds.expanduser().resolve()
    log_path = qa_dir / "pipeline_run.log"
    run_id = uuid.uuid4().hex
    logger = configure_logger(log_path)
    pipeline_started = time.perf_counter()
    log_run(logger, run_id, "pipeline_start", 0, 0, 0.0)

    connection = connect(database)
    row_counts: dict[str, int] = {}
    total_read = 0
    total_written = 0
    try:
        register_raw_views(connection, data_root)
        model_paths = sorted(
            path for path in args.sql_dir.rglob("*.sql")
            if "09_exports" not in path.parts
        )
        for sql_path in model_paths:
            sql_text = render_sql_file(sql_path, thresholds_path)
            file_started = time.perf_counter()
            available = available_relations(connection)
            inputs = referenced_relations(sql_text, available)
            rows_read = sum(
                relation_count(connection, relation, row_counts)
                for relation in inputs
            )
            outputs = output_table_names(sql_text)
            try:
                for output in outputs:
                    row_counts.pop(output, None)
                connection.execute(sql_text)
                rows_written = sum(
                    relation_count(connection, output, row_counts)
                    for output in outputs
                )
                total_read += rows_read
                total_written += rows_written
                log_run(
                    logger,
                    run_id,
                    sql_path.as_posix(),
                    rows_read,
                    rows_written,
                    time.perf_counter() - file_started,
                )
            except Exception as error:
                log_run(
                    logger,
                    run_id,
                    sql_path.as_posix(),
                    rows_read,
                    0,
                    time.perf_counter() - file_started,
                    errors=repr(error),
                )
                raise
    finally:
        connection.close()
        log_run(
            logger,
            run_id,
            "pipeline_end",
            total_read,
            total_written,
            time.perf_counter() - pipeline_started,
        )
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    main()
