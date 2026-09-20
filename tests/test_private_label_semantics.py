from pathlib import Path

from src.enforce_quality_gate import evaluate_quality_gate
from src.semantic_qa import normalize_brand, private_label_status
from src.sql_renderer import render_sql_file
from src.utils.duckdb_client import connect, register_raw_views


ROOT = Path(__file__).resolve().parents[1]


def test_brand_normalization_production_case():
    sql = render_sql_file(
        ROOT / "sql/02_staging/02_stg_product.sql",
        ROOT / "config/analysis_thresholds.yaml",
    )
    assert "UPPER(TRIM(CAST(BRAND AS VARCHAR))) AS brand_type" in sql
    assert normalize_brand("Private") == "PRIVATE"
    assert normalize_brand("National") == "NATIONAL"


def test_brand_normalization_case_insensitive():
    assert [normalize_brand(value) for value in ("Private", "PRIVATE", " private")] == ["PRIVATE"] * 3
    assert [normalize_brand(value) for value in ("National", "NATIONAL", " national ")] == ["NATIONAL"] * 3


def test_brand_normalization_trims_whitespace():
    assert normalize_brand("  Private  ") == "PRIVATE"
    assert normalize_brand("  national\t") == "NATIONAL"
    assert normalize_brand(None) is None


def test_private_label_spend_detected_and_share_is_nonzero():
    assert private_label_status(0.25, 0.25, 0.25) == "pass"
    assert private_label_status(0.25, 0.0, 0.25) == "fail"
    assert private_label_status(0.0, 0.0, 0.0) == "fail"


def test_private_label_raw_to_mart_and_segmentation_regression():
    connection = connect(":memory:")
    try:
        register_raw_views(connection, ROOT / "tests/fixtures")
        model_paths = sorted(
            path
            for path in (ROOT / "sql").rglob("*.sql")
            if "07_quality" not in path.parts and "09_exports" not in path.parts
        )
        for path in model_paths:
            connection.execute(render_sql_file(path, ROOT / "config/analysis_thresholds.yaml"))
        private_spend, private_share = connection.execute(
            "SELECT SUM(private_label_spend), SUM(private_label_spend) / SUM(panel_net_spend) FROM mart_panel_weekly"
        ).fetchone()
        candidates, final_loyal = connection.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE private_label_share >= 0.60),
                COUNT(*) FILTER (WHERE private_label_share >= 0.60 AND segment = 'Private-Label Loyal')
            FROM mart_customer_segment
            """
        ).fetchone()
        assert float(private_spend) > 0
        assert float(private_share) > 0
        assert int(candidates) > 0
        assert int(final_loyal) <= int(candidates)
    finally:
        connection.close()


def _write_csv(path: Path, header: list[str], rows: list[dict[str, object]]) -> None:
    import csv

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _seed_semantic_gate(qa_root: Path, raw: float, warehouse: float, export: float) -> None:
    _write_csv(qa_root / "qa_key_audit.csv", ["model", "duplicate_rows"], [{"model": "synthetic", "duplicate_rows": 0}])
    _write_csv(qa_root / "qa_grain_audit.csv", ["audit_name", "violating_baskets"], [{"audit_name": "synthetic", "violating_baskets": 0}])
    _write_csv(qa_root / "qa_reference_coverage.csv", ["audit_name", "violating_rows"], [{"audit_name": "synthetic", "violating_rows": 0}])
    _write_csv(qa_root / "qa_layer_reconciliation.csv", ["audit_name", "status"], [{"audit_name": "synthetic", "status": "pass"}])
    _write_csv(qa_root / "qa_transaction_anomalies.csv", ["audit_name", "violating_rows"], [{"audit_name": "quantity_outlier", "violating_rows": 0}])
    _write_csv(
        qa_root / "qa_brand_domain.csv",
        ["brand_type", "product_count", "transaction_rows", "panel_net_spend", "is_expected_domain", "status"],
        [
            {"brand_type": "PRIVATE", "product_count": 1, "transaction_rows": 1, "panel_net_spend": 10, "is_expected_domain": "true", "status": "pass"},
            {"brand_type": "NATIONAL", "product_count": 1, "transaction_rows": 1, "panel_net_spend": 10, "is_expected_domain": "true", "status": "pass"},
        ],
    )
    _write_csv(
        qa_root / "qa_private_label_reconciliation.csv",
        ["metric", "raw_semantic_value", "warehouse_value", "export_value", "warehouse_delta", "export_delta", "tolerance", "status"],
        [{"metric": "Private Label Share", "raw_semantic_value": raw, "warehouse_value": warehouse, "export_value": export, "warehouse_delta": abs(raw - warehouse), "export_delta": abs(raw - export), "tolerance": 1e-9, "status": private_label_status(raw, warehouse, export)}],
    )
    _write_csv(
        qa_root / "qa_segment_integrity.csv",
        ["check_name", "expected_value", "actual_value", "status"],
        [{"check_name": "segment_rows", "expected_value": 2500, "actual_value": 2500, "status": "pass"}],
    )


def test_private_label_raw_to_mart_reconciliation_passes(tmp_path):
    qa_root = tmp_path / "04_qa_reports"
    qa_root.mkdir()
    _seed_semantic_gate(qa_root, 0.25, 0.25, 0.25)
    result = evaluate_quality_gate(qa_root, require_semantic=True)
    assert result["ready"] is True
    assert result["semantic_ready"] is True


def test_private_label_raw_to_mart_reconciliation_blocks_derived_zero(tmp_path):
    qa_root = tmp_path / "04_qa_reports"
    qa_root.mkdir()
    _seed_semantic_gate(qa_root, 0.25, 0.0, 0.25)
    result = evaluate_quality_gate(qa_root, require_semantic=True)
    assert result["ready"] is False
    assert any(item["reason"] == "private_label_semantic_mismatch" for item in result["failures"])


def test_segment_precedence_is_not_a_private_label_failure():
    sql = render_sql_file(
        ROOT / "sql/06_marts/04_mart_customer_segment.sql",
        ROOT / "config/analysis_thresholds.yaml",
    )
    assert sql.index("High-Value Declining") < sql.index("Private-Label Loyal")
    assert "private_label_share >= 0.6" in sql
