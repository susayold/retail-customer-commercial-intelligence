import csv
from pathlib import Path

from src.enforce_quality_gate import evaluate_quality_gate


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def seed_quality_outputs(qa_root: Path, grain_violation: int = 0) -> None:
    qa_root.mkdir(parents=True, exist_ok=True)
    write_csv(
        qa_root / "qa_key_audit.csv",
        ["model", "duplicate_rows"],
        [{"model": "product", "duplicate_rows": 0}],
    )
    write_csv(
        qa_root / "qa_grain_audit.csv",
        ["audit_name", "violating_baskets"],
        [{"audit_name": "basket_day_consistency", "violating_baskets": grain_violation}],
    )
    write_csv(
        qa_root / "qa_reference_coverage.csv",
        ["audit_name", "violating_rows"],
        [{"audit_name": "transaction_product_unmatched", "violating_rows": 0}],
    )
    write_csv(
        qa_root / "qa_layer_reconciliation.csv",
        ["audit_name", "status"],
        [{"audit_name": "transaction_raw_vs_staging", "status": "pass"}],
    )
    write_csv(
        qa_root / "qa_transaction_anomalies.csv",
        ["audit_name", "violating_rows"],
        [{"audit_name": "quantity_outlier", "violating_rows": 3}],
    )
    write_csv(
        qa_root / "qa_brand_domain.csv",
        ["brand_type", "product_count", "transaction_rows", "panel_net_spend", "is_expected_domain", "status"],
        [
            {"brand_type": "PRIVATE", "product_count": 1, "transaction_rows": 1, "panel_net_spend": 10, "is_expected_domain": "true", "status": "pass"},
            {"brand_type": "NATIONAL", "product_count": 1, "transaction_rows": 1, "panel_net_spend": 10, "is_expected_domain": "true", "status": "pass"},
        ],
    )


def test_quality_gate_blocks_grain_failures_but_keeps_review_warnings(tmp_path):
    qa_root = tmp_path / "04_qa_reports"
    seed_quality_outputs(qa_root, grain_violation=2)

    result = evaluate_quality_gate(qa_root)

    assert result["ready"] is False
    assert result["failures"][0]["reason"] == "basket_grain_inconsistency"
    assert result["warnings"][0]["audit_name"] == "quantity_outlier"


def test_quality_gate_passes_when_blocking_conditions_are_clean(tmp_path):
    qa_root = tmp_path / "04_qa_reports"
    seed_quality_outputs(qa_root)

    result = evaluate_quality_gate(qa_root)

    assert result["ready"] is True
    assert result["failures"] == []
    assert result["warnings"][0]["reason"] == "transaction_anomaly_retained_for_review"


def test_quality_gate_rejects_empty_quality_outputs(tmp_path):
    qa_root = tmp_path / "04_qa_reports"
    qa_root.mkdir(parents=True, exist_ok=True)
    write_csv(qa_root / "qa_key_audit.csv", ["model", "duplicate_rows"], [])
    write_csv(qa_root / "qa_grain_audit.csv", ["audit_name", "violating_baskets"], [])
    write_csv(qa_root / "qa_reference_coverage.csv", ["audit_name", "violating_rows"], [])
    write_csv(qa_root / "qa_layer_reconciliation.csv", ["audit_name", "status"], [])
    write_csv(qa_root / "qa_transaction_anomalies.csv", ["audit_name", "violating_rows"], [])
    write_csv(
        qa_root / "qa_brand_domain.csv",
        ["brand_type", "product_count", "transaction_rows", "panel_net_spend", "is_expected_domain", "status"],
        [],
    )

    result = evaluate_quality_gate(qa_root)

    assert result["ready"] is False
    assert all(item["reason"] == "empty_quality_output" for item in result["failures"])
