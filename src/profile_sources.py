"""Profile Drive-backed source files without copying source data into the repository."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.utils.duckdb_client import RAW_SOURCES, connect, register_raw_views


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


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
                row_count BIGINT,
                column_count INTEGER
            )
            """
        )
        connection.execute(
            """
            CREATE OR REPLACE TABLE source_null_profile (
                source_name VARCHAR,
                column_name VARCHAR,
                column_type VARCHAR,
                row_count BIGINT,
                null_or_blank_count BIGINT,
                null_or_blank_pct DOUBLE,
                distinct_count BIGINT,
                min_value VARCHAR,
                max_value VARCHAR
            )
            """
        )

        for source_name, source_filename in RAW_SOURCES.items():
            columns = connection.execute(
                f"DESCRIBE SELECT * FROM raw_{source_name}"
            ).fetchall()
            quoted_columns = [(quote_identifier(row[0]), row[0], row[1]) for row in columns]
            expressions = ["COUNT(*) AS row_count"]
            for ordinal, (identifier, _name, _type) in enumerate(quoted_columns):
                expressions.extend(
                    [
                        f"SUM(CASE WHEN {identifier} IS NULL OR TRIM(CAST({identifier} AS VARCHAR)) = '' THEN 1 ELSE 0 END) AS null_{ordinal}",
                        f"COUNT(DISTINCT {identifier}) AS distinct_{ordinal}",
                        f"MIN(CAST({identifier} AS VARCHAR)) AS min_{ordinal}",
                        f"MAX(CAST({identifier} AS VARCHAR)) AS max_{ordinal}",
                    ]
                )
            row = connection.execute(
                f"SELECT {', '.join(expressions)} FROM raw_{source_name}"
            ).fetchone()
            row_count = int(row[0] or 0)
            connection.execute(
                "INSERT INTO source_profile_summary VALUES (?, ?, ?, ?)",
                [source_name, source_filename, row_count, len(columns)],
            )
            for ordinal, (_identifier, column_name, column_type) in enumerate(quoted_columns):
                offset = 1 + ordinal * 4
                null_count = int(row[offset] or 0)
                distinct_count = int(row[offset + 1] or 0)
                min_value = row[offset + 2]
                max_value = row[offset + 3]
                null_pct = null_count / row_count if row_count else None
                connection.execute(
                    "INSERT INTO source_null_profile VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [
                        source_name,
                        column_name,
                        column_type,
                        row_count,
                        null_count,
                        null_pct,
                        distinct_count,
                        None if min_value is None else str(min_value),
                        None if max_value is None else str(max_value),
                    ],
                )

        for table_name in ("source_profile_summary", "source_null_profile"):
            output_path = qa_dir / f"{table_name}.csv"
            connection.execute(
                f"COPY (SELECT * FROM {table_name}) TO ? (HEADER, DELIMITER ',')",
                [output_path.as_posix()],
            )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
