import csv
from pathlib import Path

from src.profile_sources import profile_sources


ROOT = Path(__file__).resolve().parents[1]


def test_profile_writes_separate_cardinality_artifact(tmp_path):
    artifact_root = tmp_path / "artifacts"
    profile_sources(ROOT / "tests" / "fixtures", artifact_root)

    output = artifact_root / "04_qa_reports" / "source_cardinality.csv"
    with output.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert reader.fieldnames == [
        "source_name",
        "source_filename",
        "column_name",
        "row_count",
        "distinct_count",
        "cardinality_ratio",
    ]
    assert rows
    assert any(
        row["source_name"] == "transaction_data"
        and row["column_name"] == "BASKET_ID"
        for row in rows
    )
