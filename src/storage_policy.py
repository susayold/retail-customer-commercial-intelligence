"""Verify the Drive-only storage boundary separately from source readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.source_manifest import EXPECTED_SOURCE_FILES
from src.storage_paths import require_drive_path

ARTIFACT_FOLDERS = (
    "01_raw_source",
    "02_curated_parquet",
    "03_duckdb_and_marts",
    "04_qa_reports",
    "05_powerbi_exports",
    "06_source_docs",
)
FORBIDDEN_SUFFIXES = {
    ".csv",
    ".parquet",
    ".duckdb",
    ".db",
    ".sqlite",
    ".pbix",
    ".pbit",
    ".xlsx",
    ".xls",
    ".pdf",
}


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve()


def _inside(child: Path, parent: Path) -> bool:
    try:
        _resolved(child).relative_to(_resolved(parent))
        return True
    except ValueError:
        return False


def source_status(data_root: Path) -> dict[str, object]:
    """Describe raw completeness; this does not replace checksum verification."""
    root = _resolved(data_root)
    if not root.is_dir():
        return {
            "data_root": str(root),
            "expected_files": list(EXPECTED_SOURCE_FILES),
            "present": [],
            "missing": list(EXPECTED_SOURCE_FILES),
            "extras": [],
            "complete": False,
        }
    files = [path for path in root.rglob("*") if path.is_file()]
    relative = [str(path.relative_to(root)) for path in files]
    present = [name for name in EXPECTED_SOURCE_FILES if (root / name).is_file()]
    extras = sorted(item for item in relative if item not in EXPECTED_SOURCE_FILES)
    missing = [name for name in EXPECTED_SOURCE_FILES if name not in present]
    return {
        "data_root": str(root),
        "expected_files": list(EXPECTED_SOURCE_FILES),
        "present": present,
        "missing": missing,
        "extras": extras,
        "complete": not missing and not extras and len(relative) == len(EXPECTED_SOURCE_FILES),
    }


def repository_violations(repo_root: Path) -> list[str]:
    root = _resolved(repo_root)
    violations: list[str] = []
    if not root.exists():
        return [str(root)]
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        fixture_csv = (
            len(relative.parts) >= 3
            and relative.parts[0] == "tests"
            and relative.parts[1] == "fixtures"
            and path.suffix.lower() == ".csv"
        )
        if fixture_csv:
            continue
        if path.name in EXPECTED_SOURCE_FILES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            violations.append(str(relative))
    return sorted(violations)


def storage_status(
    data_root: Path,
    artifact_root: Path,
    repo_root: Path,
    drive_root: Path | None = None,
) -> dict[str, object]:
    data = _resolved(data_root)
    artifacts = _resolved(artifact_root)
    repo = _resolved(repo_root)
    drive = _resolved(drive_root) if drive_root is not None else None
    artifact_missing = [
        folder for folder in ARTIFACT_FOLDERS if not (artifacts / folder).is_dir()
    ]
    violations: list[str] = []
    drive_root_available = drive is not None and drive.is_dir()
    if drive is None:
        violations.append("drive_root_not_declared")
    else:
        if not drive_root_available:
            violations.append("drive_root_missing_or_not_directory")
        if not _inside(data, drive):
            violations.append("data_root_outside_declared_drive_root")
        if not _inside(artifacts, drive):
            violations.append("artifact_root_outside_declared_drive_root")
    if _inside(data, repo):
        violations.append("data_root_inside_repository")
    if _inside(artifacts, repo):
        violations.append("artifact_root_inside_repository")
    violations.extend(f"repository_artifact:{item}" for item in repository_violations(repo))
    source = source_status(data)
    boundary_failures = list(violations)
    boundary_failures.extend(f"missing_artifact_folder:{item}" for item in artifact_missing)
    docs = artifacts / "06_source_docs"
    marker_path = docs / "source_ready.json"
    marker_status = None
    if marker_path.is_file():
        try:
            marker_status = json.loads(marker_path.read_text(encoding="utf-8")).get("status")
        except (OSError, json.JSONDecodeError):
            marker_status = "INVALID"
    source_ready = bool(source["complete"] and marker_status == "READY")
    return {
        # storage_boundary_ready means paths/folders are safe; it intentionally
        # remains true while the project waits for the licensed raw package.
        "ready": not boundary_failures,
        "storage_boundary_ready": not boundary_failures,
        "source_ready": source_ready,
        "drive_root": str(drive) if drive is not None else None,
        "drive_root_declared": drive is not None,
        "drive_root_available": drive_root_available,
        "source": source,
        "source_ready_marker_status": marker_status,
        "artifact_root": str(artifacts),
        "required_artifact_folders": list(ARTIFACT_FOLDERS),
        "missing_artifact_folders": artifact_missing,
        "repository_violations": violations,
        "failures": boundary_failures,
        "source_failures": (
            list(source["missing"]) + list(source["extras"])
            if not source["complete"] else []
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--drive-root", type=Path, default=None)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    result = storage_status(
        args.data_root,
        args.artifact_root,
        args.repo_root,
        args.drive_root,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered)
    if args.output is not None:
        output = _resolved(args.output)
        if not _inside(output, _resolved(args.artifact_root)):
            raise SystemExit("Storage policy failed: --output must be inside artifact-root")
        repository_artifact_failure = any(
            item.startswith("repository_artifact:")
            for item in result["failures"]
        )
        if result["storage_boundary_ready"] and not repository_artifact_failure:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered + "\n", encoding="utf-8")
    if not result["storage_boundary_ready"]:
        raise SystemExit("Storage boundary failed; inspect the reported Drive paths")


if __name__ == "__main__":
    main()
