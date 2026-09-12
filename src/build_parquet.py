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

FILES = (
    "transaction_data",
    "causal_data",
    "coupon",
    "coupon_redempt",
    "campaign_table",
    "campaign_desc",
    "product",
    "hh_demographic",
)


def count_csv_rows(path: Path) -> int:
    """Count data rows without materializing the source."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def count_parquet_rows(connection: duckdb.DuckDBPyConnection, path: Path) -> int:
    """Count rows written to a Parquet file using DuckDB's reader."""
    return int(
        connection.execute(
            "SELECT COUNT(*) FROM read_parquet(?)",
            [path.as_posix()],
        ).fetchone()[0]
    )


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
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    qa_dir = args.output.parent.parent / "04_qa_reports"
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
            source_path = args.input / f"{stem}.csv"
            target_path = args.output / f"{stem}.parquet"
            file_started = time.perf_counter()
            rows_read = 0
            rows_written = 0
            try:
                rows_read = count_csv_rows(source_path)
                source = source_path.as_posix()
                target = target_path.as_posix()
                connection.execute(
                    "COPY (SELECT * FROM read_csv_auto(?, header=true, union_by_name=true)) "
                    "TO ? (FORMAT PARQUET, COMPRESSION ZSTD)",
                    [source, target],
                )
                rows_written = count_parquet_rows(connection, target_path)
                if rows_written != rows_read:
                    raise ValueError(
                        f"Parquet row-count mismatch for {source_path.name}: "
                        f"read={rows_read}, written={rows_written}"
                    )
                total_read += rows_read
                total_written += rows_written
                log_run(
                    logger,
                    run_id,
                    source,
                    rows_read,
                    rows_written,
                    time.perf_counter() - file_started,
                )
                print(f"wrote {target}")
            except Exception as error:
                log_run(
                    logger,
                    run_id,
                    source_path.as_posix(),
                    rows_read,
                    rows_written,
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
        logger.removeHandler(handler)
        handler.close()


if __name__ == "__main__":
    main()
