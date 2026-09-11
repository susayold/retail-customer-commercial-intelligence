"""Materialize the governed customer segmentation model in a Drive-backed DuckDB."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.utils.duckdb_client import connect


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--sql", type=Path, default=Path("sql/06_marts/04_mart_customer_segment.sql"))
    args = parser.parse_args()

    connection = connect(args.database)
    try:
        connection.execute(args.sql.read_text(encoding="utf-8"))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
