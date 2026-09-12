from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest
import yaml

from src.source_acquisition import (
    AcquisitionError,
    acquire_source,
    discover_expected_files,
    safe_extract_zip,
)
from src.source_manifest import EXPECTED_SOURCE_FILES


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = yaml.safe_load((ROOT / "config/source_contracts.yaml").read_text(encoding="utf-8"))["sources"]


def _csv_bytes(file_name: str, row: bool = True) -> bytes:
    source_name = file_name.removesuffix(".csv")
    columns = CONTRACTS[source_name]["required_columns"]
    line = ",".join(columns) + "\n"
    if row:
        line += ",".join("1" for _ in columns) + "\n"
    return line.encode("utf-8")


def _zip(path: Path, *, missing: str | None = None, extra: bool = False, duplicate: bool = False, zero: str | None = None) -> Path:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_name in EXPECTED_SOURCE_FILES:
            if file_name == missing:
                continue
            payload = b"" if file_name == zero else _csv_bytes(file_name)
            archive.writestr("package/" + file_name, payload)
        if extra:
            archive.writestr("package/unexpected.csv", b"a\n1\n")
        if duplicate:
            archive.writestr("other/transaction_data.csv", _csv_bytes("transaction_data.csv"))
    return path


def test_valid_eight_file_package_promotes_and_second_run_is_no_op(tmp_path: Path):
    drive = tmp_path / "drive"
    drive.mkdir()
    archive = _zip(drive / "source.zip")
    result = acquire_source("manual", drive, archive)
    assert result["status"] == "READY"
    assert result["outcome"] == "PROMOTED"
    raw = drive / "01_raw_source"
    assert sorted(path.name for path in raw.iterdir()) == sorted(EXPECTED_SOURCE_FILES)
    second = acquire_source("manual", drive, archive)
    assert second["outcome"] == "NO_OP"
    marker = json.loads((drive / "06_source_docs/source_ready.json").read_text())
    assert marker["verified_file_count"] == 8


@pytest.mark.parametrize(
    "kwargs",
    [
        {"missing": "coupon.csv"},
        {"zero": "product.csv"},
        {"extra": True},
        {"duplicate": True},
    ],
)
def test_invalid_exact_source_packages_fail_without_raw_promotion(tmp_path: Path, kwargs: dict):
    drive = tmp_path / "drive"
    drive.mkdir()
    archive = _zip(drive / "source.zip", **kwargs)
    with pytest.raises(AcquisitionError):
        acquire_source("manual", drive, archive)
    raw = drive / "01_raw_source"
    assert not raw.exists() or not list(raw.iterdir())


def test_existing_different_complete_raw_is_not_overwritten(tmp_path: Path):
    drive = tmp_path / "drive"
    drive.mkdir()
    archive = _zip(drive / "source.zip")
    acquire_source("manual", drive, archive)
    before = (drive / "01_raw_source/transaction_data.csv").read_bytes()
    changed = _zip(drive / "changed.zip")
    # A valid candidate with a different checksum must fail closed.
    with zipfile.ZipFile(changed, "a", zipfile.ZIP_DEFLATED) as archive_handle:
        archive_handle.writestr("package/transaction_data.csv", _csv_bytes("transaction_data.csv") + b"2\n")
    with pytest.raises(AcquisitionError):
        acquire_source("manual", drive, changed)
    assert (drive / "01_raw_source/transaction_data.csv").read_bytes() == before


def test_corrupt_zip_fails(tmp_path: Path):
    drive = tmp_path / "drive"
    drive.mkdir()
    archive = drive / "corrupt.zip"
    archive.write_bytes(b"not a zip")
    with pytest.raises(AcquisitionError):
        acquire_source("manual", drive, archive)


def test_zip_slip_is_rejected(tmp_path: Path):
    archive = tmp_path / "slip.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("../escape.csv", "x\n1\n")
    with pytest.raises(AcquisitionError, match="Unsafe ZIP"):
        safe_extract_zip(archive, tmp_path / "extracted")


def test_discovery_requires_each_expected_file_exactly_once(tmp_path: Path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested/transaction_data.csv").write_bytes(b"x")
    with pytest.raises(AcquisitionError, match="missing"):
        discover_expected_files(tmp_path)


def test_raw_input_must_be_under_declared_drive(tmp_path: Path):
    drive = tmp_path / "drive"
    drive.mkdir()
    outside = tmp_path / "outside.zip"
    outside.write_bytes(b"")
    with pytest.raises(SystemExit, match="underneath"):
        acquire_source("manual", drive, outside)
