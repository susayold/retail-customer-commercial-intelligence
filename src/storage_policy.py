"""Verify source completeness and the Drive-only storage boundary before a run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .inventory import EXPECTED_FILES

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
    root = _resolved(data_root)
    present = [name for name in EXPECTED_FILES if (root / name).is_file()]
    missing = [name for name in EXPECTED_FILES if name not in present]
    return {
        "data_root": str(root),
        "expected_files": list(EXPECTED_FILES),
        "present": present,
        "missing": missing,
        "complete": not missing,
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
        if path.name in EXPECTED_FILES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
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
    if drive is None:
        violations.append("drive_root_not_declared")
    else:
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
    failures = list(source["missing"])
    failures.extend(f"missing_artifact_folder:{item}" for item in artifact_missing)
    failures.extend(violations)
    return {
        "ready": not failures,
        "drive_root": str(drive) if drive is not None else None,
        "drive_root_declared": drive is not None,
        "source": source,
        "artifact_root": str(artifacts),
        "required_artifact_folders": list(ARTIFACT_FOLDERS),
        "missing_artifact_folders": artifact_missing,
        "repository_violations": violations,
        "failures": failures,
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
        if result["drive_root_declared"] and not any(
            item in result["failures"]
            for item in (
                "data_root_outside_declared_drive_root",
                "artifact_root_outside_declared_drive_root",
            )
        ):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered + "\n", encoding="utf-8")
    if not result["ready"]:
        raise SystemExit("Storage policy failed; inspect the reported Drive paths")


if __name__ == "__main__":
    main()
