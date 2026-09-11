"""Convert Drive-backed CSV sources to Drive-backed Parquet outputs."""

from __future__ import annotations

import argparse
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

    connection = duckdb.connect(":memory:")
    try:
        for stem in FILES:
            source = (args.input / f"{stem}.csv").as_posix()
            target = (args.output / f"{stem}.parquet").as_posix()
            connection.execute(
                "COPY (SELECT * FROM read_csv_auto(?, header=true, union_by_name=true)) "
                "TO ? (FORMAT PARQUET, COMPRESSION ZSTD)",
                [source, target],
            )
            print(f"wrote {target}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
