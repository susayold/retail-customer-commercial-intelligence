PYTHON ?= python

test:
	$(PYTHON) -m pytest -q

inventory:
	$(PYTHON) -m src.inventory --input "$$RETAIL_DATA_ROOT" --output "$$RETAIL_ARTIFACT_ROOT/04_qa_reports/raw_file_inventory.csv"

parquet:
	$(PYTHON) -m src.build_parquet --input "$$RETAIL_DATA_ROOT" --output "$$RETAIL_ARTIFACT_ROOT/02_curated_parquet"

warehouse:
	$(PYTHON) -m src.build_warehouse --data-root "$$RETAIL_DATA_ROOT" --artifact-root "$$RETAIL_ARTIFACT_ROOT"

validate:
	$(PYTHON) -m src.validate --data-root "$$RETAIL_DATA_ROOT" --artifact-root "$$RETAIL_ARTIFACT_ROOT"
