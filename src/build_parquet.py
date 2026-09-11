"""Convert Drive-backed CSV sources to Drive-backed Parquet outputs."""

from __future__ import annotations

import argparse
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
    try:
        for stem in FILES:
            source = (args.input / f"{stem}.csv").as_posix()
            target = (args.output / f"{stem}.parquet").as_posix()
            started_at = time.perf_counter()
            connection.execute(
                "COPY (SELECT * FROM read_csv_auto(?, header=true, union_by_name=true)) "
                "TO ? (FORMAT PARQUET, COMPRESSION ZSTD)",
                [source, target],
            )
            logger.info(
                "run_id=%s timestamp=%s file=%s rows_read=%s rows_written=%s duration_seconds=%.3f warnings=%s errors=%s",
                run_id, datetime.now(timezone.utc).isoformat(), source,
                "unknown", "unknown", time.perf_counter() - started_at, "", "",
            )
            print(f"wrote {target}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
