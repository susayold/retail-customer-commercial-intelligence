from pathlib import Path

import pytest

from src.inventory import EXPECTED_FILES, inspect_csv
from src.storage_policy import repository_violations, source_status, storage_status
from src.storage_paths import require_drive_path

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



def test_inventory_records_content_checksum(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("id,value\n1,a\n", encoding="utf-8")
    result = inspect_csv(source)
    assert len(result["content_sha256"]) == 64
    assert result["content_sha256"] != result["column_names_hash"]



def test_inventory_reports_planning_row_count_delta(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("id,value\n1,a\n", encoding="utf-8")
    result = inspect_csv(source, expected_row_count=1)
    assert result["expected_row_count"] == 1
    assert result["row_count_delta"] == 0
    assert result["planning_expectation_status"] == "match"

def test_storage_status_requires_explicit_drive_root(tmp_path):
    result = storage_status(
        tmp_path / "raw",
        tmp_path / "artifacts",
        ROOT,
    )

    assert result["ready"] is False
    assert result["drive_root_declared"] is False
    assert "drive_root_not_declared" in result["failures"]


def test_storage_status_rejects_roots_outside_declared_drive_root(tmp_path):
    drive_root = tmp_path / "drive"
    result = storage_status(
        tmp_path / "raw",
        tmp_path / "artifacts",
        ROOT,
        drive_root,
    )

    assert result["ready"] is False
    assert "data_root_outside_declared_drive_root" in result["failures"]
    assert "artifact_root_outside_declared_drive_root" in result["failures"]


def test_storage_status_rejects_unmounted_drive_root(tmp_path):
    drive_root = tmp_path / "not-mounted"
    result = storage_status(
        drive_root / "raw",
        drive_root / "artifacts",
        ROOT,
        drive_root,
    )

    assert result["drive_root_available"] is False
    assert "drive_root_missing_or_not_directory" in result["failures"]


def test_standalone_stage_paths_require_a_real_drive_root(tmp_path):
    with pytest.raises(SystemExit, match="--drive-root"):
        require_drive_path(tmp_path / "output", None, "--output")

    drive_root = tmp_path / "drive"
    drive_root.mkdir()
    with pytest.raises(SystemExit, match="underneath"):
        require_drive_path(tmp_path / "outside", drive_root, "--output")

    target = drive_root / "artifacts"
    assert require_drive_path(target, drive_root, "--output") == target.resolve()
