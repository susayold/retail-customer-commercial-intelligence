from pathlib import Path

import yaml

from src.schema_contracts import validate_headers
from src.utils.duckdb_client import RAW_SOURCES

ROOT = Path(__file__).resolve().parents[1]


def test_contracts_match_the_eight_source_files():
    contracts = yaml.safe_load((ROOT / "config/source_contracts.yaml").read_text())
    assert len(contracts["sources"]) == 8
    assert set(contracts["sources"]) == set(RAW_SOURCES)
    assert all(contract["file"].endswith(".csv") for contract in contracts["sources"].values())


def test_synthetic_headers_satisfy_source_contracts():
    rows = validate_headers(ROOT / "tests/fixtures", ROOT / "config/source_contracts.yaml")
    assert all(row["status"] == "ok" for row in rows)


def test_schema_validator_flags_unexpected_and_duplicate_headers(tmp_path):
    required = [
        "household_key",
        "BASKET_ID",
        "DAY",
        "PRODUCT_ID",
        "QUANTITY",
        "SALES_VALUE",
        "STORE_ID",
        "RETAIL_DISC",
        "COUPON_DISC",
        "COUPON_MATCH_DISC",
        "TRANS_TIME",
        "WEEK_NO",
    ]
    (tmp_path / "transaction_data.csv").write_text(
        ",".join(required + ["UNEXPECTED", "BASKET_ID"]) + "\n",
        encoding="utf-8",
    )
    rows = validate_headers(tmp_path, ROOT / "config/source_contracts.yaml")
    transaction = next(row for row in rows if row["source_name"] == "transaction_data")
    assert transaction["status"] == "duplicate_columns"
    assert transaction["unexpected_columns"] == "UNEXPECTED"
    assert transaction["duplicate_columns"] == "BASKET_ID"
