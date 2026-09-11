"""Run QA SQL files and export result tables to Drive."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.utils.duckdb_client import connect, register_raw_views


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--sql-dir", type=Path, default=Path("sql/07_quality"))
    args = parser.parse_args()

    qa_dir = args.artifact_root / "04_qa_reports"
    qa_dir.mkdir(parents=True, exist_ok=True)
    database = args.artifact_root / "03_duckdb_and_marts" / "retail_intelligence.duckdb"
    connection = connect(database)
    try:
        register_raw_views(connection, args.data_root)
        for sql_path in sorted(args.sql_dir.glob("*.sql")):
            connection.execute(sql_path.read_text(encoding="utf-8"))
        connection.execute(
            "COPY (SELECT * FROM qa_source_reconciliation) TO ? (HEADER, DELIMITER ',')",
            [(qa_dir / "qa_source_reconciliation.csv").as_posix()],
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
