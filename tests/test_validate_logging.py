import time

from src.validate import RUN_LOG_FIELDS, log_record


def test_validate_log_record_contains_row_counts_and_duration():
    record = log_record(
        "run-test",
        "qa_source_reconciliation.csv",
        rows_read=3,
        rows_written=3,
        started_at=time.perf_counter(),
    )

    assert set(record) == set(RUN_LOG_FIELDS)
    assert record["run_id"] == "run-test"
    assert record["file"] == "qa_source_reconciliation.csv"
    assert record["rows_read"] == 3
    assert record["rows_written"] == 3
    assert float(record["duration_seconds"]) >= 0
    assert record["errors"] == ""
