"""Run SQL models against Drive-backed sources and write the warehouse to Drive."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.utils.duckdb_client import connect, register_raw_views


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

    logging.basicConfig(filename=log_path, level=logging.INFO)
    connection = connect(database)
    try:
        register_raw_views(connection, args.data_root)
        for sql_path in sorted(args.sql_dir.rglob("*.sql")):
            if "09_exports" in sql_path.parts:
                continue
            logging.info("running sql=%s", sql_path)
            connection.execute(sql_path.read_text(encoding="utf-8"))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
