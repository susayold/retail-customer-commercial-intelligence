"""DuckDB connection and raw-source view registration."""

from __future__ import annotations

from pathlib import Path

import duckdb

RAW_SOURCES = {
    "transaction_data": "transaction_data.csv",
    "causal_data": "causal_data.csv",
    "coupon": "coupon.csv",
    "coupon_redempt": "coupon_redempt.csv",
    "campaign_table": "campaign_table.csv",
    "campaign_desc": "campaign_desc.csv",
    "product": "product.csv",
    "hh_demographic": "hh_demographic.csv",
}


def connect(database: str | Path = ":memory:", threads: int = 4) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect(str(database))
    connection.execute(f"PRAGMA threads={threads}")
    return connection


def register_raw_views(connection: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    for name, filename in RAW_SOURCES.items():
        path = (raw_dir / filename).as_posix()
        connection.execute(
            f"CREATE OR REPLACE VIEW raw_{name} AS "
            "SELECT * FROM read_csv_auto(?, header=true, union_by_name=true)",
            [path],
        )
