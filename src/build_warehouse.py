"""Run SQL models against Drive-backed sources and write the warehouse to Drive."""

from __future__ import annotations

import argparse
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.utils.duckdb_client import connect, register_raw_views


def configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("retail_pipeline")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--database", type=Path, default=None)
    parser.add_argument("--sql-dir", type=Path, default=Path("sql"))
    args = parser.parse_args()

    warehouse_dir = args.artifact_root / "03_duckdb_and_marts"
    qa_dir = args.artifact_root / "04_qa_reports"
    warehouse_dir.mkdir(parents=True, exist_ok=True)
    qa_dir.mkdir(parents=True, exist_ok=True)
    database = args.database or warehouse_dir / "retail_intelligence.duckdb"
    log_path = qa_dir / "pipeline_run.log"
    run_id = uuid.uuid4().hex
    logger = configure_logger(log_path)
    connection = connect(database)
    started_at = datetime.now(timezone.utc).isoformat()
    logger.info(
        "run_id=%s timestamp=%s file=%s rows_read=%s rows_written=%s duration_seconds=%s warnings=%s errors=%s",
        run_id, started_at, "pipeline_start", "unknown", "unknown", 0, "", "",
    )
    try:
        register_raw_views(connection, args.data_root)
        model_paths = sorted(
            path for path in args.sql_dir.rglob("*.sql")
            if "09_exports" not in path.parts
        )
        for sql_path in model_paths:
            step_started = time.perf_counter()
            try:
                connection.execute(sql_path.read_text(encoding="utf-8"))
                logger.info(
                    "run_id=%s timestamp=%s file=%s rows_read=%s rows_written=%s duration_seconds=%.3f warnings=%s errors=%s",
                    run_id, datetime.now(timezone.utc).isoformat(), sql_path.as_posix(),
                    "unknown", "unknown", time.perf_counter() - step_started, "", "",
                )
            except Exception as error:
                logger.error(
                    "run_id=%s timestamp=%s file=%s rows_read=%s rows_written=%s duration_seconds=%.3f warnings=%s errors=%s",
                    run_id, datetime.now(timezone.utc).isoformat(), sql_path.as_posix(),
                    "unknown", "unknown", time.perf_counter() - step_started, "", repr(error),
                )
                raise
    finally:
        connection.close()
        logger.info(
            "run_id=%s timestamp=%s file=%s rows_read=%s rows_written=%s duration_seconds=%s warnings=%s errors=%s",
            run_id, datetime.now(timezone.utc).isoformat(), "pipeline_end", "unknown", "unknown", "unknown", "", "",
        )


if __name__ == "__main__":
    main()
