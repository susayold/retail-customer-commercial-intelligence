from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_profile_contract_emits_cardinality_report():
    source = (ROOT / "src" / "profile_sources.py").read_text(encoding="utf-8")
    assert "CREATE OR REPLACE TABLE source_cardinality" in source
    assert '"source_cardinality"' in source
    assert "distinct_pct" in source
