from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_key_and_grain_audits_exist():
    quality_dir = ROOT / "sql/07_quality"
    assert sorted(path.name for path in quality_dir.glob("*.sql")) == [
        "01_q01_source_reconciliation.sql",
        "02_q02_key_audit.sql",
        "03_q03_grain_audit.sql",
        "04_q04_discount_audit.sql",
        "05_q05_quantity_audit.sql",
        "06_q06_campaign_observability.sql",
        "07_q07_demographic_coverage.sql",
    ]