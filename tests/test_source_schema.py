from pathlib import Path

import yaml

from src.schema_contracts import validate_headers

ROOT = Path(__file__).resolve().parents[1]


def test_contracts_match_the_eight_source_files():
    contracts = yaml.safe_load((ROOT / "config/source_contracts.yaml").read_text())
    assert len(contracts["sources"]) == 8
    assert all(contract["file"].endswith(".csv") for contract in contracts["sources"].values())


def test_synthetic_headers_satisfy_source_contracts():
    rows = validate_headers(ROOT / "tests/fixtures", ROOT / "config/source_contracts.yaml")
    assert all(row["status"] == "ok" for row in rows)