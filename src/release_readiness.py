"""Fail-closed audit for the final Drive-backed retail delivery."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.export_powerbi import POWERBI_OUTPUT_NAMES


REQUIRED_ARTIFACT_FILES = (
    "04_qa_reports/storage_status.json",
    "04_qa_reports/raw_file_inventory.csv",
    "04_qa_reports/schema_validation.csv",
    "04_qa_reports/source_profile_summary.csv",
    "04_qa_reports/source_cardinality.csv",
    "04_qa_reports/qa_run_log.csv",
    "04_qa_reports/qa_quality_gate.json",
    "04_qa_reports/qa_layer_reconciliation.csv",
    "04_qa_reports/powerbi_reconciliation.csv",
    "04_qa_reports/uat_results.csv",
    "04_qa_reports/root_cause_cases.csv",
    "04_qa_reports/executive_decisions.csv",
    "04_qa_reports/pipeline_orchestration.log",
    "04_qa_reports/statistics/stats_basket_by_segment.csv",
    "04_qa_reports/statistics/stats_promotion_state.csv",
    "04_qa_reports/statistics/stats_campaign_redemption.csv",
    "04_qa_reports/statistics/statistics_run_log.csv",
)

REQUIRED_REPOSITORY_FILES = (
    "docs/11_root_cause_cases.md",
    "docs/12_executive_decisions.md",
    "docs/13_limitations.md",
    "docs/14_powerbi_uat.md",
    "powerbi/semantic_model.yaml",
    "powerbi/measures.dax",
)

REQUIRED_POWERBI_EXPORTS = tuple(
    f"{name}.parquet" for name in POWERBI_OUTPUT_NAMES.values()
)


def _check(name: str, ready: bool, reason: str, path: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"name": name, "ready": bool(ready), "reason": reason}
    if path is not None:
        result["path"] = path
    return result


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "missing file"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"invalid JSON: {exc}"
    if not isinstance(value, dict):
        return None, "JSON root must be an object"
    return value, None


def _read_csv(path: Path) -> tuple[list[dict[str, str]] | None, list[str] | None, str | None]:
    if not path.is_file():
        return None, None, "missing file"
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)
    except OSError as exc:
        return None, None, f"cannot read file: {exc}"
    if not fieldnames:
        return None, None, "missing CSV header"
    if not rows:
        return [], fieldnames, "empty CSV output"
    return rows, fieldnames, None


def _csv_contract(
    artifact_root: Path,
    relative_path: str,
    required_columns: set[str],
    *,
    expected_rows: int | None = None,
    minimum_rows: int | None = None,
    require_pass_status: bool = False,
    complete_statuses: set[str] | None = None,
    require_nonblank_columns: set[str] | None = None,
) -> dict[str, Any]:
    path = artifact_root / relative_path
    rows, fieldnames, error = _read_csv(path)
    if error is not None:
        return _check(relative_path, False, error, relative_path)
    assert rows is not None and fieldnames is not None
    missing = sorted(required_columns - set(fieldnames))
    if missing:
        return _check(
            relative_path,
            False,
            f"missing columns: {', '.join(missing)}",
            relative_path,
        )
    if expected_rows is not None and len(rows) != expected_rows:
        return _check(
            relative_path,
            False,
            f"expected {expected_rows} rows, found {len(rows)}",
            relative_path,
        )
    if minimum_rows is not None and len(rows) < minimum_rows:
        return _check(
            relative_path,
            False,
            f"expected at least {minimum_rows} rows, found {len(rows)}",
            relative_path,
        )
    if require_pass_status:
        failures = [
            str(row.get("status", "")).strip()
            for row in rows
            if str(row.get("status", "")).strip().lower() != "pass"
        ]
        if failures:
            return _check(
                relative_path,
                False,
                f"{len(failures)} row(s) are not pass",
                relative_path,
            )
    if complete_statuses is not None:
        incomplete = [
            str(row.get("status", "")).strip()
            for row in rows
            if str(row.get("status", "")).strip().lower() not in complete_statuses
        ]
        if incomplete:
            return _check(
                relative_path,
                False,
                f"{len(incomplete)} row(s) are not complete",
                relative_path,
            )
    if require_nonblank_columns is not None:
        blank_values = sum(
            1
            for row in rows
            for column in require_nonblank_columns
            if not str(row.get(column, "")).strip()
        )
        if blank_values:
            return _check(
                relative_path,
                False,
                f"{blank_values} required evidence value(s) are blank",
                relative_path,
            )
    return _check(relative_path, True, f"{len(rows)} row(s) validated", relative_path)


def evaluate_release_readiness(artifact_root: Path, repo_root: Path) -> dict[str, Any]:
    artifact_root = artifact_root.expanduser().resolve()
    repo_root = repo_root.expanduser().resolve()
    checks: list[dict[str, Any]] = []

    storage_path = artifact_root / "04_qa_reports/storage_status.json"
    storage, storage_error = _read_json(storage_path)
    checks.append(
        _check(
            "storage_policy",
            storage_error is None and storage is not None and storage.get("ready") is True,
            "ready" if storage_error is None and storage is not None and storage.get("ready") is True
            else (storage_error or "storage policy is not ready"),
            str(storage_path),
        )
    )

    quality_path = artifact_root / "04_qa_reports/qa_quality_gate.json"
    quality, quality_error = _read_json(quality_path)
    checks.append(
        _check(
            "blocking_quality_gate",
            quality_error is None and quality is not None and quality.get("ready") is True,
            "ready" if quality_error is None and quality is not None and quality.get("ready") is True
            else (quality_error or "blocking quality gate is not ready"),
            str(quality_path),
        )
    )

    for relative_path in REQUIRED_ARTIFACT_FILES:
        if relative_path.endswith(".json"):
            continue
        path = artifact_root / relative_path
        checks.append(
            _check(
                relative_path,
                path.is_file() and path.stat().st_size > 0 if path.exists() else False,
                "present" if path.is_file() and path.stat().st_size > 0 else "missing or empty",
                relative_path,
            )
        )

    checks.append(
        _csv_contract(
            artifact_root,
            "04_qa_reports/qa_layer_reconciliation.csv",
            {"audit_name", "status"},
            minimum_rows=1,
            require_pass_status=True,
        )
    )
    checks.append(
        _csv_contract(
            artifact_root,
            "04_qa_reports/powerbi_reconciliation.csv",
            {"metric", "sql_value", "powerbi_value", "difference", "tolerance", "status"},
            expected_rows=8,
            require_pass_status=True,
        )
    )
    checks.append(
        _csv_contract(
            artifact_root,
            "04_qa_reports/uat_results.csv",
            {"check_id", "status"},
            expected_rows=12,
            require_pass_status=True,
        )
    )
    checks.append(
        _csv_contract(
            artifact_root,
            "04_qa_reports/root_cause_cases.csv",
            {"case_id", "status", "evidence_uri", "run_id", "limitation"},
            expected_rows=3,
            complete_statuses={"complete", "completed", "pass"},
            require_nonblank_columns={"case_id", "evidence_uri", "run_id", "limitation"},
        )
    )
    checks.append(
        _csv_contract(
            artifact_root,
            "04_qa_reports/executive_decisions.csv",
            {"decision_id", "status", "evidence_uri", "run_id", "limitation"},
            expected_rows=5,
            complete_statuses={"complete", "completed", "pass"},
            require_nonblank_columns={"decision_id", "evidence_uri", "run_id", "limitation"},
        )
    )

    exports_dir = artifact_root / "05_powerbi_exports"
    missing_exports = [
        name
        for name in REQUIRED_POWERBI_EXPORTS
        if not ((exports_dir / name).is_file() or (exports_dir / name.replace(".parquet", ".csv")).is_file())
    ]
    checks.append(
        _check(
            "powerbi_exports",
            not missing_exports,
            "31 exports present" if not missing_exports else f"missing {len(missing_exports)} export(s)",
            str(exports_dir),
        )
    )

    for relative_path in REQUIRED_REPOSITORY_FILES:
        path = repo_root / relative_path
        checks.append(
            _check(
                relative_path,
                path.is_file() and path.stat().st_size > 0 if path.exists() else False,
                "present" if path.is_file() and path.stat().st_size > 0 else "missing or empty",
                relative_path,
            )
        )

    failures = [item for item in checks if not item["ready"]]
    return {
        "ready": not failures,
        "artifact_root": str(artifact_root),
        "repository_root": str(repo_root),
        "required_powerbi_export_count": len(REQUIRED_POWERBI_EXPORTS),
        "checks": checks,
        "failure_count": len(failures),
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    result = evaluate_release_readiness(args.artifact_root, args.repo_root)
    output = (args.output or args.artifact_root / "04_qa_reports/release_readiness.json").expanduser().resolve()
    try:
        output.relative_to(args.artifact_root.expanduser().resolve())
    except ValueError as exc:
        raise SystemExit("--output must be inside artifact-root") from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if not result["ready"]:
        raise SystemExit("Release readiness failed; inspect the Drive audit output")


if __name__ == "__main__":
    main()
