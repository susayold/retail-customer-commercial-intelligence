PYTHON ?= python

test:
	$(PYTHON) -m pytest -q

storage:
	$(PYTHON) -m src.storage_policy --data-root "$$RETAIL_DATA_ROOT" --artifact-root "$$RETAIL_ARTIFACT_ROOT" --drive-root "$$RETAIL_DRIVE_ROOT" --repo-root "." --output "$$RETAIL_ARTIFACT_ROOT/04_qa_reports/storage_status.json"

acquire-official:
	$(PYTHON) -m src.acquire_source --provider official --drive-root "$$RETAIL_DRIVE_ROOT"

acquire-kaggle:
	$(PYTHON) -m src.acquire_source --provider kaggle --drive-root "$$RETAIL_DRIVE_ROOT"

acquire-manual:
	$(PYTHON) -m src.acquire_source --provider manual --input "$$RETAIL_ACQUISITION_INPUT" --drive-root "$$RETAIL_DRIVE_ROOT"

verify-source:
	$(PYTHON) -m src.verify_source_ready --drive-root "$$RETAIL_DRIVE_ROOT"

schema:
	$(PYTHON) -m src.schema_contracts --input "$$RETAIL_DATA_ROOT" --contracts config/source_contracts.yaml --output "$$RETAIL_ARTIFACT_ROOT/04_qa_reports/schema_validation.csv" --drive-root "$$RETAIL_DRIVE_ROOT"

inventory:
	$(PYTHON) -m src.inventory --input "$$RETAIL_DATA_ROOT" --output "$$RETAIL_ARTIFACT_ROOT/04_qa_reports/raw_file_inventory.csv" --drive-root "$$RETAIL_DRIVE_ROOT"

profile:
	$(PYTHON) -m src.profile_sources --data-root "$$RETAIL_DATA_ROOT" --artifact-root "$$RETAIL_ARTIFACT_ROOT" --drive-root "$$RETAIL_DRIVE_ROOT"

parquet:
	$(PYTHON) -m src.build_parquet --input "$$RETAIL_DATA_ROOT" --output "$$RETAIL_ARTIFACT_ROOT/02_curated_parquet" --drive-root "$$RETAIL_DRIVE_ROOT"

warehouse:
	$(PYTHON) -m src.build_warehouse --data-root "$$RETAIL_DATA_ROOT" --artifact-root "$$RETAIL_ARTIFACT_ROOT" --drive-root "$$RETAIL_DRIVE_ROOT"

segment:
	$(PYTHON) -m src.segment_customers --database "$$RETAIL_ARTIFACT_ROOT/03_duckdb_and_marts/retail_intelligence.duckdb" --drive-root "$$RETAIL_DRIVE_ROOT"

validate:
	$(PYTHON) -m src.validate --data-root "$$RETAIL_DATA_ROOT" --artifact-root "$$RETAIL_ARTIFACT_ROOT" --drive-root "$$RETAIL_DRIVE_ROOT"

quality-gate:
	$(PYTHON) -m src.enforce_quality_gate --artifact-root "$$RETAIL_ARTIFACT_ROOT" --drive-root "$$RETAIL_DRIVE_ROOT"

stats:
	$(PYTHON) -m src.statistical_validation --database "$$RETAIL_ARTIFACT_ROOT/03_duckdb_and_marts/retail_intelligence.duckdb" --artifact-root "$$RETAIL_ARTIFACT_ROOT" --drive-root "$$RETAIL_DRIVE_ROOT"

metric-totals:
	$(PYTHON) -m src.build_metric_totals --artifact-root "$$RETAIL_ARTIFACT_ROOT" --drive-root "$$RETAIL_DRIVE_ROOT"

semantic-qa:
	$(PYTHON) -m src.semantic_qa --data-root "$$RETAIL_DATA_ROOT" --artifact-root "$$RETAIL_ARTIFACT_ROOT" --thresholds config/analysis_thresholds.yaml --pipeline-run-id "$$RETAIL_PIPELINE_RUN_ID" --drive-root "$$RETAIL_DRIVE_ROOT"

real-evidence:
	$(PYTHON) -m src.build_real_evidence --artifact-root "$$RETAIL_ARTIFACT_ROOT" --drive-root "$$RETAIL_DRIVE_ROOT"

uat-contract:
	$(PYTHON) -m src.build_uat_evidence --artifact-root "$$RETAIL_ARTIFACT_ROOT" --drive-root "$$RETAIL_DRIVE_ROOT"

data-ready:
	$(PYTHON) -m src.write_data_readiness --artifact-root "$$RETAIL_ARTIFACT_ROOT" --drive-root "$$RETAIL_DRIVE_ROOT" --repo-root "." --pipeline-run-id "$$RETAIL_PIPELINE_RUN_ID" --started-at "$$RETAIL_PIPELINE_STARTED_AT"

da-no-native-powerbi:
	$(PYTHON) -m src.run_da_no_native_powerbi --data-root "$$RETAIL_DATA_ROOT" --artifact-root "$$RETAIL_ARTIFACT_ROOT" --drive-root "$$RETAIL_DRIVE_ROOT" --repo-root "."

powerbi:
	$(PYTHON) -m src.export_powerbi --artifact-root "$$RETAIL_ARTIFACT_ROOT" --format parquet --drive-root "$$RETAIL_DRIVE_ROOT"

reconcile:
	$(PYTHON) -m src.reconcile --sql "$$RETAIL_SQL_RECONCILIATION" --bi "$$RETAIL_BI_RECONCILIATION" --output "$$RETAIL_ARTIFACT_ROOT/04_qa_reports/powerbi_reconciliation.csv" --drive-root "$$RETAIL_DRIVE_ROOT"

release-audit:
	$(PYTHON) -m src.release_readiness --artifact-root "$$RETAIL_ARTIFACT_ROOT" --repo-root "." --drive-root "$$RETAIL_DRIVE_ROOT"

run:
	$(PYTHON) -m src.run_pipeline --data-root "$$RETAIL_DATA_ROOT" --artifact-root "$$RETAIL_ARTIFACT_ROOT" --drive-root "$$RETAIL_DRIVE_ROOT" --repo-root "." --with-tests

all: run
