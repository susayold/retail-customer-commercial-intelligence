from pathlib import Path

from src.validate import QA_TABLES

ROOT = Path(__file__).resolve().parents[1]


def test_transaction_anomaly_qa_is_registered_and_covers_plan_checks():
    assert "qa_transaction_anomalies" in QA_TABLES
    sql = (ROOT / "sql/07_quality/09_q09_transaction_anomalies.sql").read_text(
        encoding="utf-8"
    )
    for audit_name in (
        "day_range",
        "week_range",
        "sales_negative",
        "sales_zero",
        "quantity_non_positive",
        "quantity_outlier",
        "trans_time_invalid",
        "missing_product",
        "missing_household",
        "missing_basket",
    ):
        assert audit_name in sql


def test_layer_reconciliation_qa_is_registered():
    assert "qa_layer_reconciliation" in QA_TABLES
    sql = (ROOT / "sql/07_quality/10_q10_layer_reconciliation.sql").read_text(
        encoding="utf-8"
    )
    for token in (
        "transaction_raw_vs_staging",
        "transaction_staging_vs_fact",
        "transaction_fact_vs_basket",
        "sales_difference",
        "household_difference",
        "basket_difference",
        "status",
    ):
        assert token in sql
