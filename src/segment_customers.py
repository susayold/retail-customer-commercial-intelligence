"""Materialize the governed customer segmentation model in a Drive-backed DuckDB."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.sql_renderer import render_sql_file
from src.storage_paths import require_drive_path
from src.utils.duckdb_client import connect


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--sql", type=Path, default=Path("sql/06_marts/04_mart_customer_segment.sql"))
    parser.add_argument(
        "--thresholds", type=Path, default=Path("config/analysis_thresholds.yaml")
    )
    parser.add_argument("--drive-root", type=Path, required=True)
    args = parser.parse_args()

    database = require_drive_path(args.database, args.drive_root, "--database")
    connection = connect(database)
    try:
        connection.execute(render_sql_file(args.sql, args.thresholds))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
