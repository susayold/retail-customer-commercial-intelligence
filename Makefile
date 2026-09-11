PYTHON ?= python

test:
	$(PYTHON) -m pytest -q

schema:
	$(PYTHON) -m src.schema_contracts --input "$$RETAIL_DATA_ROOT" --contracts config/source_contracts.yaml --output "$$RETAIL_ARTIFACT_ROOT/04_qa_reports/schema_validation.csv"

inventory:
	$(PYTHON) -m src.inventory --input "$$RETAIL_DATA_ROOT" --output "$$RETAIL_ARTIFACT_ROOT/04_qa_reports/raw_file_inventory.csv"

profile:
	$(PYTHON) -m src.profile_sources --data-root "$$RETAIL_DATA_ROOT" --artifact-root "$$RETAIL_ARTIFACT_ROOT"

parquet:
	$(PYTHON) -m src.build_parquet --input "$$RETAIL_DATA_ROOT" --output "$$RETAIL_ARTIFACT_ROOT/02_curated_parquet"

warehouse:
	$(PYTHON) -m src.build_warehouse --data-root "$$RETAIL_DATA_ROOT" --artifact-root "$$RETAIL_ARTIFACT_ROOT"

segment:
	$(PYTHON) -m src.segment_customers --database "$$RETAIL_ARTIFACT_ROOT/03_duckdb_and_marts/retail_intelligence.duckdb"

validate:
	$(PYTHON) -m src.validate --data-root "$$RETAIL_DATA_ROOT" --artifact-root "$$RETAIL_ARTIFACT_ROOT"

stats:
	$(PYTHON) -m src.statistical_validation --database "$$RETAIL_ARTIFACT_ROOT/03_duckdb_and_marts/retail_intelligence.duckdb" --artifact-root "$$RETAIL_ARTIFACT_ROOT"

powerbi:
	$(PYTHON) -m src.export_powerbi --artifact-root "$$RETAIL_ARTIFACT_ROOT" --format parquet

all: schema inventory profile parquet warehouse segment validate stats powerbi test
