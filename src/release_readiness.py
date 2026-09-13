"""Fail-closed audit for the final Drive-backed retail delivery."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import yaml

from src.export_powerbi import POWERBI_OUTPUT_NAMES
from src.inventory import EXPECTED_FILES
from src.storage_paths import require_drive_path


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

REQUIRED_DATA_READY_FIELDS = (
    "status",
    "source_gate",
    "curated_gate",
    "warehouse_gate",
    "marts_gate",
    "blocking_issues",
)

REQUIRED_DATA_RUN_MANIFEST_FIELDS = (
    "source_manifest_sha",
    "source_ready_verified_at",
    "repo_commit_sha",
    "pipeline_run_id",
    "raw_files",
    "parquet_files",
    "database_path",
    "qa_outputs",
    "started_at",
    "completed_at",
    "status",
)

REQUIRED_UAT_CHECK_IDS = tuple(f"UAT-{index:02d}" for index in range(1, 13))

INVENTORY_REQUIRED_COLUMNS = {
    "file_name",
    "file_size_bytes",
    "row_count",
    "column_count",
    "column_names_hash",
    "content_sha256",
    "load_status",
}
SCHEMA_REQUIRED_COLUMNS = {
    "source_name",
    "file_name",
    "status",
    "observed_column_count",
}


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

REQUIRED_POWERBI_MEASURES = (
    "Panel Net Spend",
    "Active Panel Households",
    "Total Recorded Discount",
    "Trips per Active Household",
    "Spend per Active Household",
    "Spend per Basket",
    "Private Label Share",
    "Coupon Basket Rate",
    "Category Household Penetration",
    "Campaign Redemption Rate",
)

REQUIRED_RECONCILIATION_METRICS = (
    "Panel Net Spend",
    "Baskets",
    "Active Panel Households",
    "Spend per Basket",
    "Private Label Share",
    "Campaign Recipients",
    "Campaign Redeemers",
    "Redemption Rate",
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
    require_blank_columns: set[str] | None = None,
    unique_columns: set[str] | None = None,
    exact_values: dict[str, set[str]] | None = None,
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
    if unique_columns is not None:
        for column in unique_columns:
            seen: set[str] = set()
            duplicates: set[str] = set()
            for row in rows:
                value = str(row.get(column, "")).strip()
                if value in seen:
                    duplicates.add(value)
                seen.add(value)
            if duplicates:
                return _check(
                    relative_path,
                    False,
                    f"duplicate value(s) in {column}: {', '.join(sorted(duplicates))}",
                    relative_path,
                )
    if exact_values is not None:
        for column, expected in exact_values.items():
            actual = {str(row.get(column, "")).strip() for row in rows}
            missing = sorted(expected - actual)
            unexpected = sorted(actual - expected)
            if missing or unexpected:
                parts = []
                if missing:
                    parts.append(f"missing {column}: {', '.join(missing)}")
                if unexpected:
                    parts.append(f"unexpected {column}: {', '.join(unexpected)}")
                return _check(relative_path, False, "; ".join(parts), relative_path)
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
    if require_blank_columns is not None:
        nonblank_values = sum(
            1
            for row in rows
            for column in require_blank_columns
            if str(row.get(column, "")).strip()
        )
        if nonblank_values:
            return _check(
                relative_path,
                False,
                f"{nonblank_values} fields expected to be blank are populated",
                relative_path,
            )
    return _check(relative_path, True, f"{len(rows)} row(s) validated", relative_path)


def _powerbi_semantic_check(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "powerbi/semantic_model.yaml"
    if not path.is_file():
        return _check("powerbi_semantic_model", False, "missing file", str(path))
    try:
        contract = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        return _check("powerbi_semantic_model", False, f"invalid YAML: {exc}", str(path))
    if not isinstance(contract, dict):
        return _check("powerbi_semantic_model", False, "YAML root must be an object", str(path))

    expected_tables = {
        output_name
        for table_name, output_name in POWERBI_OUTPUT_NAMES.items()
        if not table_name.startswith("export_")
    }
    tables = contract.get("tables") or []
    actual_tables = {
        item.get("name")
        for item in tables
        if isinstance(item, dict) and item.get("name")
    }
    relationships = contract.get("relationships") or []
    pages = contract.get("pages") or []
    errors: list[str] = []
    if contract.get("storage_policy") != "Drive-only":
        errors.append("storage_policy must be Drive-only")
    if contract.get("source_folder") != "05_powerbi_exports":
        errors.append("source_folder must be 05_powerbi_exports")
    if contract.get("raw_source_allowed") is not False:
        errors.append("raw_source_allowed must be false")
    if len(tables) != len(expected_tables) or actual_tables != expected_tables:
        errors.append(f"expected exactly {len(expected_tables)} curated tables")
    if len(pages) != 6:
        errors.append("expected exactly 6 pages")
    if any(
        not isinstance(item, dict) or item.get("cross_filter") != "single"
        for item in relationships
    ):
        errors.append("relationships must use single cross-filter direction")
    return _check(
        "powerbi_semantic_model",
        not errors,
        "; ".join(errors) if errors else f"{len(tables)} curated tables and 6 pages validated",
        str(path),
    )


def _powerbi_measures_check(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "powerbi/measures.dax"
    if not path.is_file():
        return _check("powerbi_measures", False, "missing file", str(path))
    try:
        dax = path.read_text(encoding="utf-8")
    except OSError as exc:
        return _check("powerbi_measures", False, f"cannot read file: {exc}", str(path))
    missing = [name for name in REQUIRED_POWERBI_MEASURES if name not in dax]
    return _check(
        "powerbi_measures",
        not missing,
        "required governed measures present"
        if not missing
        else f"missing measures: {', '.join(missing)}",
        str(path),
    )


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

    data_ready_path = artifact_root / "06_source_docs/data_ready.json"
    data_ready, data_ready_error = _read_json(data_ready_path)
    data_ready_ok = (
        data_ready_error is None
        and data_ready is not None
        and all(data_ready.get(field) not in (None, "", []) for field in REQUIRED_DATA_READY_FIELDS)
        and data_ready.get("status") == "DATA_READY"
        and data_ready.get("source_gate") == "PASS"
        and data_ready.get("curated_gate") == "PASS"
        and data_ready.get("warehouse_gate") == "PASS"
        and data_ready.get("marts_gate") == "PASS"
        and data_ready.get("blocking_issues") == 0
    )
    checks.append(
        _check(
            "data_ready_marker",
            data_ready_ok,
            "DATA_READY with all four gates PASS"
            if data_ready_ok
            else (data_ready_error or "data_ready.json is missing required PASS fields"),
            str(data_ready_path),
        )
    )

    manifest_path = artifact_root / "06_source_docs/data_run_manifest.json"
    data_run_manifest, manifest_error = _read_json(manifest_path)
    manifest_ok = (
        manifest_error is None
        and data_run_manifest is not None
        and all(data_run_manifest.get(field) not in (None, "", []) for field in REQUIRED_DATA_RUN_MANIFEST_FIELDS)
        and data_run_manifest.get("status") == "SUCCESS"
        and len(data_run_manifest.get("raw_files", [])) == len(EXPECTED_FILES)
        and len(data_run_manifest.get("parquet_files", [])) == len(EXPECTED_FILES)
    )
    checks.append(
        _check(
            "data_run_manifest",
            manifest_ok,
            "required run manifest fields present"
            if manifest_ok
            else (manifest_error or "data_run_manifest.json is missing required fields"),
            str(manifest_path),
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
            "04_qa_reports/raw_file_inventory.csv",
            INVENTORY_REQUIRED_COLUMNS,
            expected_rows=len(EXPECTED_FILES),
            require_nonblank_columns=INVENTORY_REQUIRED_COLUMNS,
            unique_columns={"file_name"},
            exact_values={"file_name": set(EXPECTED_FILES), "load_status": {"ok"}},
        )
    )
    checks.append(
        _csv_contract(
            artifact_root,
            "04_qa_reports/schema_validation.csv",
            SCHEMA_REQUIRED_COLUMNS,
            expected_rows=len(EXPECTED_FILES),
            complete_statuses={"ok"},
            require_nonblank_columns=SCHEMA_REQUIRED_COLUMNS,
            unique_columns={"file_name", "source_name"},
            exact_values={"file_name": set(EXPECTED_FILES), "status": {"ok"}},
        )
    )

    checks.append(
        _csv_contract(
            artifact_root,
            "04_qa_reports/source_profile_summary.csv",
            {"source_name", "source_filename", "row_count", "column_count"},
            expected_rows=len(EXPECTED_FILES),
            require_nonblank_columns={"source_name", "source_filename", "row_count", "column_count"},
            unique_columns={"source_name", "source_filename"},
            exact_values={"source_filename": set(EXPECTED_FILES)},
        )
    )
    checks.append(
        _csv_contract(
            artifact_root,
            "04_qa_reports/source_cardinality.csv",
            {"source_name", "source_filename", "column_name", "row_count", "distinct_count"},
            minimum_rows=len(EXPECTED_FILES),
            require_nonblank_columns={"source_name", "source_filename", "column_name", "row_count", "distinct_count"},
            exact_values={"source_filename": set(EXPECTED_FILES)},
        )
    )
    checks.append(
        _csv_contract(
            artifact_root,
            "04_qa_reports/qa_run_log.csv",
            {"run_id", "timestamp", "file", "rows_read", "rows_written", "duration_seconds", "errors"},
            minimum_rows=1,
            require_nonblank_columns={"run_id", "timestamp", "file", "rows_read", "rows_written", "duration_seconds"},
            require_blank_columns={"errors"},
        )
    )
    checks.append(
        _csv_contract(
            artifact_root,
            "04_qa_reports/powerbi_reconciliation.csv",
            {"metric", "sql_value", "powerbi_value", "difference", "tolerance", "status"},
            expected_rows=len(REQUIRED_RECONCILIATION_METRICS),
            require_pass_status=True,
            unique_columns={"metric"},
            exact_values={"metric": set(REQUIRED_RECONCILIATION_METRICS)},
        )
    )

    checks.append(
        _csv_contract(
            artifact_root,
            "04_qa_reports/statistics/stats_basket_by_segment.csv",
            {"segment", "n", "mean_basket_value", "ci_low", "ci_high"},
            minimum_rows=1,
        )
    )
    checks.append(
        _csv_contract(
            artifact_root,
            "04_qa_reports/statistics/stats_promotion_state.csv",
            {"promo_state_group", "n", "mean_panel_sales_per_product_store_week", "kruskal_wallis_p_value"},
            minimum_rows=1,
        )
    )
    checks.append(
        _csv_contract(
            artifact_root,
            "04_qa_reports/statistics/stats_campaign_redemption.csv",
            {"campaign_type", "n_recipients", "redeemers", "redemption_rate", "ci_low", "ci_high"},
            minimum_rows=1,
        )
    )
    checks.append(
        _csv_contract(
            artifact_root,
            "04_qa_reports/statistics/statistics_run_log.csv",
            {"run_id", "started_at_utc", "finished_at_utc", "status", "database", "output_files", "duration_seconds", "error"},
            expected_rows=1,
            complete_statuses={"success"},
            require_nonblank_columns={"run_id", "started_at_utc", "finished_at_utc", "database", "output_files"},
            require_blank_columns={"error"},
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
            expected_rows=len(REQUIRED_UAT_CHECK_IDS),
            require_pass_status=True,
            require_nonblank_columns={"check_id"},
            unique_columns={"check_id"},
            exact_values={"check_id": set(REQUIRED_UAT_CHECK_IDS)},
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

    checks.append(_powerbi_semantic_check(repo_root))
    checks.append(_powerbi_measures_check(repo_root))

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
    parser.add_argument("--drive-root", type=Path, required=True)
    args = parser.parse_args()

    artifact_root = require_drive_path(args.artifact_root, args.drive_root, "--artifact-root")
    result = evaluate_release_readiness(artifact_root, args.repo_root)
    output = (args.output or artifact_root / "04_qa_reports/release_readiness.json").expanduser().resolve()
    try:
        output.relative_to(artifact_root)
    except ValueError as exc:
        raise SystemExit("--output must be inside artifact-root") from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if not result["ready"]:
        raise SystemExit("Release readiness failed; inspect the Drive audit output")


if __name__ == "__main__":
    main()
