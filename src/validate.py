"""Run the full transformation chain, then export QA result tables to Drive."""

from __future__ import annotations

import argparse
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
)


def run_sql_files(connection, sql_paths: list[Path]) -> None:
    for sql_path in sql_paths:
        connection.execute(sql_path.read_text(encoding="utf-8"))


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
            output_path = qa_dir / f"{table_name}.csv"
            connection.execute(
                f"COPY (SELECT * FROM {table_name}) TO ? (HEADER, DELIMITER ',')",
                [output_path.as_posix()],
            )
    finally:
        connection.close()


if __name__ == "__main__":
    main()