from __future__ import annotations

import json
from pathlib import Path

from src.source_acquisition import acquire_source
from src.source_manifest import EXPECTED_SOURCE_FILES
from src.verify_source_ready import verify_source_ready

from test_source_acquisition import _zip


def test_verify_source_ready_passes_after_drive_promotion(tmp_path: Path):
    drive = tmp_path / "drive"
    drive.mkdir()
    acquire_source("manual", drive, _zip(drive / "source.zip"))
    result = verify_source_ready(drive / "01_raw_source", drive / "06_source_docs")
    assert result["status"] == "READY"
    assert result["failures"] == []


def test_verify_source_ready_detects_tampered_raw_file(tmp_path: Path):
    drive = tmp_path / "drive"
    drive.mkdir()
    acquire_source("manual", drive, _zip(drive / "source.zip"))
    target = drive / "01_raw_source" / EXPECTED_SOURCE_FILES[0]
    target.write_bytes(target.read_bytes() + b"tampered")
    result = verify_source_ready(drive / "01_raw_source", drive / "06_source_docs")
    assert result["status"] == "NOT_READY"
    assert any(item.startswith("checksum_mismatch:") for item in result["failures"])


def test_verify_source_ready_requires_marker_and_checksums(tmp_path: Path):
    drive = tmp_path / "drive"
    drive.mkdir()
    raw = drive / "01_raw_source"
    docs = drive / "06_source_docs"
    raw.mkdir()
    docs.mkdir()
    for file_name in EXPECTED_SOURCE_FILES:
        (raw / file_name).write_text("column\nvalue\n", encoding="utf-8")
    result = verify_source_ready(raw, docs)
    assert result["status"] == "NOT_READY"
    assert "source_ready_marker_missing" in result["failures"]
    assert "source_checksums_missing" in result["failures"]
