"""Profile Drive-backed source files without copying source data into the repository."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.utils.duckdb_client import RAW_SOURCES, connect, register_raw_views


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    args = parser.parse_args()

    qa_dir = args.artifact_root / "04_qa_reports"
    qa_dir.mkdir(parents=True, exist_ok=True)
    connection = connect(":memory:")
    try:
        register_raw_views(connection, args.data_root)
        connection.execute(
            """
            CREATE OR REPLACE TABLE source_profile_summary (
                source_name VARCHAR,
                source_filename VARCHAR,
                row_count BIGINT
            )
            """
        )
        summary_rows = []
        column_rows = []
        for source_name, source_filename in RAW_SOURCES.items():
            row_count = connection.execute(
                f"SELECT COUNT(*) FROM raw_{source_name}"
            ).fetchone()[0]
            summary_rows.append((source_name, source_filename, row_count))
            columns = connection.execute(
                f"DESCRIBE SELECT * FROM raw_{source_name}"
            ).fetchall()
            column_rows.extend(
                (source_name, ordinal, column_name, column_type)
                for ordinal, (column_name, column_type, *_rest) in enumerate(columns, start=1)
            )
        connection.executemany(
            "INSERT INTO source_profile_summary VALUES (?, ?, ?)",
            summary_rows,
        )
        connection.execute(
            """
            CREATE OR REPLACE TABLE source_profile_columns (
                source_name VARCHAR,
                ordinal INTEGER,
                column_name VARCHAR,
                column_type VARCHAR
            )
            """
        )
        connection.executemany(
            "INSERT INTO source_profile_columns VALUES (?, ?, ?, ?)",
            column_rows,
        )
        for table_name in ("source_profile_summary", "source_profile_columns"):
            output_path = qa_dir / f"{table_name}.csv"
            connection.execute(
                f"COPY (SELECT * FROM {table_name}) TO ? (HEADER, DELIMITER ',')",
                [output_path.as_posix()],
            )
    finally:
        connection.close()


if __name__ == "__main__":
    main()