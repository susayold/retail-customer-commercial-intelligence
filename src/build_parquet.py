"""Convert Drive-backed CSV sources to Drive-backed Parquet outputs."""

from __future__ import annotations

import argparse
import csv
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from src.source_manifest import EXPECTED_SOURCE_FILES
from src.storage_paths import require_drive_path

FILES = tuple(path.removesuffix(".csv") for path in EXPECTED_SOURCE_FILES)


def count_csv_rows(path: Path) -> int:
    """Fallback count for runs without a Drive inventory artifact."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def load_inventory_counts(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            file_name = row.get("file_name", "")
            value = row.get("row_count", "")
            if file_name and value not in ("", None):
                counts[file_name] = int(value)
    return counts


def count_parquet_rows(connection: duckdb.DuckDBPyConnection, path: Path) -> int:
    return int(connection.execute("SELECT COUNT(*) FROM read_parquet(?)", [path.as_posix()]).fetchone()[0])


def duckdb_string_literal(value: str) -> str:
    """Return a safely quoted DuckDB string literal for a controlled file path."""
    return "'" + value.replace("'", "''") + "'"


def log_run(logger: logging.Logger, run_id: str, file_name: str, rows_read: int, rows_written: int, duration_seconds: float, warnings: str = "", errors: str = "") -> None:
    logger.info(
        "run_id=%s timestamp=%s file=%s rows_read=%s rows_written=%s duration_seconds=%.3f warnings=%s errors=%s",
        run_id, datetime.now(timezone.utc).isoformat(), file_name, rows_read, rows_written, duration_seconds, warnings, errors,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, default=None)
    parser.add_argument("--drive-root", type=Path, required=True)
    args = parser.parse_args()

    input_root = require_drive_path(args.input, args.drive_root, "--input")
    output_root = require_drive_path(args.output, args.drive_root, "--output")
    inventory_path = require_drive_path(args.inventory, args.drive_root, "--inventory") if args.inventory is not None else None
    inventory_counts = load_inventory_counts(inventory_path) if inventory_path and inventory_path.is_file() else {}
    output_root.mkdir(parents=True, exist_ok=True)
    qa_dir = output_root.parent.parent / "04_qa_reports"
    qa_dir.mkdir(parents=True, exist_ok=True)
    log_path = qa_dir / "pipeline_run.log"
    run_id = uuid.uuid4().hex
    logger = logging.getLogger("retail_parquet")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    connection = duckdb.connect(":memory:")
    total_read = 0
    total_written = 0
    pipeline_started = time.perf_counter()
    log_run(logger, run_id, "pipeline_start", 0, 0, 0.0)
    try:
        for stem in FILES:
            source_path = input_root / f"{stem}.csv"
            target_path = output_root / f"{stem}.parquet"
            file_started = time.perf_counter()
            rows_read = 0
            rows_written = 0
            try:
                rows_read = inventory_counts.get(source_path.name)
                if rows_read is None:
                    rows_read = count_csv_rows(source_path)
                source = source_path.as_posix()
                target = target_path.as_posix()
                connection.execute(
                    f"COPY (SELECT * FROM read_csv_auto({duckdb_string_literal(source)}, header=true, union_by_name=true)) "
                    f"TO {duckdb_string_literal(target)} (FORMAT PARQUET, COMPRESSION ZSTD)",
                )
                rows_written = count_parquet_rows(connection, target_path)
                if rows_written != rows_read:
                    raise ValueError(f"Parquet row-count mismatch for {source_path.name}: read={rows_read}, written={rows_written}")
                total_read += rows_read
                total_written += rows_written
                log_run(logger, run_id, source, rows_read, rows_written, time.perf_counter() - file_started)
                print(f"wrote {target}")
            except Exception as error:
                log_run(logger, run_id, source_path.as_posix(), rows_read, rows_written, time.perf_counter() - file_started, errors=repr(error))
                raise
    finally:
        connection.close()
        log_run(logger, run_id, "pipeline_end", total_read, total_written, time.perf_counter() - pipeline_started)
        logger.removeHandler(handler)
        handler.close()


if __name__ == "__main__":
    main()
