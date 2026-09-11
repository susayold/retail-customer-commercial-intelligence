from pathlib import Path

from src.inventory import EXPECTED_FILES
from src.storage_policy import repository_violations, source_status

ROOT = Path(__file__).resolve().parents[1]


def test_repository_has_no_persisted_data_artifacts():
    assert repository_violations(ROOT) == []


def test_missing_source_status_is_explicit():
    result = source_status(ROOT / "__not_a_drive_source__")
    assert result["complete"] is False
    assert result["missing"] == list(EXPECTED_FILES)


def test_synthetic_fixtures_are_the_only_csv_exception():
    fixtures = ROOT / "tests" / "fixtures"
    assert all(path.suffix == ".csv" for path in fixtures.glob("*.csv"))
    assert repository_violations(ROOT) == []
