import csv
import json
from pathlib import Path

from src.export_powerbi import POWERBI_OUTPUT_NAMES
from src.inventory import EXPECTED_FILES
from src.write_data_readiness import write_data_readiness


def write_status_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["status"])
        writer.writeheader()
        writer.writerow({"status": "pass"})


def test_write_data_readiness_emits_manifest_and_marker(tmp_path):
    artifact_root = tmp_path / "artifacts"
    repo_root = tmp_path / "repo"
    docs_root = artifact_root / "06_source_docs"
    qa_root = artifact_root / "04_qa_reports"
    docs_root.mkdir(parents=True)
    qa_root.mkdir(parents=True)
    (artifact_root / "01_raw_source").mkdir(parents=True)
    (artifact_root / "02_curated_parquet").mkdir(parents=True)
    (artifact_root / "03_duckdb_and_marts").mkdir(parents=True)
    (artifact_root / "05_powerbi_exports").mkdir(parents=True)
    repo_root.mkdir()

    (docs_root / "source_ready.json").write_text(
        json.dumps({"status": "READY", "checksum_status": "PASS", "acquired_at": "2026-09-13T00:00:00+00:00"}),
        encoding="utf-8",
    )
    (docs_root / "acquisition_manifest.json").write_text("{}", encoding="utf-8")
    (qa_root / "qa_quality_gate.json").write_text(json.dumps({"ready": True, "warnings": []}), encoding="utf-8")
    (qa_root / "governed_asset_audit.json").write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    for name in ("qa_source_reconciliation.csv", "qa_layer_reconciliation.csv", "qa_key_audit.csv", "qa_grain_audit.csv"):
        write_status_csv(qa_root / name)

    for source_name in EXPECTED_FILES:
        (artifact_root / "01_raw_source" / source_name).write_bytes(b"synthetic")
        (artifact_root / "02_curated_parquet" / f"{Path(source_name).stem}.parquet").write_bytes(b"synthetic")
    (artifact_root / "03_duckdb_and_marts" / "retail_intelligence.duckdb").write_bytes(b"synthetic")
    for export_name in POWERBI_OUTPUT_NAMES.values():
        (artifact_root / "05_powerbi_exports" / f"{export_name}.parquet").write_bytes(b"synthetic")

    result = write_data_readiness(
        artifact_root=artifact_root,
        repo_root=repo_root,
        pipeline_run_id="run-test",
        started_at="2026-09-13T00:00:00+00:00",
        completed_at="2026-09-13T00:01:00+00:00",
    )

    assert result["data_ready"]["status"] == "DATA_READY"
    assert result["data_ready"]["blocking_issues"] == 0
    manifest = json.loads((docs_root / "data_run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "SUCCESS"
    assert len(manifest["raw_files"]) == len(EXPECTED_FILES)
    assert len(manifest["parquet_files"]) == len(EXPECTED_FILES)
