"""Enforce blocking data-quality stop conditions before analysis and BI exports."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from src.storage_paths import require_drive_path


REQUIRED_QA_FILES = (
    "qa_key_audit.csv",
    "qa_grain_audit.csv",
    "qa_reference_coverage.csv",
    "qa_layer_reconciliation.csv",
    "qa_transaction_anomalies.csv",
)
REQUIRED_QA_COLUMNS = {
    "qa_key_audit.csv": {"model", "duplicate_rows"},
    "qa_grain_audit.csv": {"audit_name", "violating_baskets"},
    "qa_reference_coverage.csv": {"audit_name", "violating_rows"},
    "qa_layer_reconciliation.csv": {"audit_name", "status"},
    "qa_transaction_anomalies.csv": {"audit_name", "violating_rows"},
}
BLOCKING_TRANSACTION_ANOMALIES = {
    "missing_product",
    "missing_household",
    "missing_basket",
}


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def as_number(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def evaluate_quality_gate(qa_root: Path) -> dict[str, object]:
    failures: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    checked_files: list[str] = []

    for file_name in REQUIRED_QA_FILES:
        path = qa_root / file_name
        if not path.exists():
            failures.append(
                {
                    "file": file_name,
                    "reason": "missing_quality_output",
                }
            )
            continue
        checked_files.append(file_name)
        fieldnames, rows = read_rows(path)
        missing_columns = sorted(REQUIRED_QA_COLUMNS[file_name] - set(fieldnames))
        if missing_columns:
            failures.append(
                {
                    "file": file_name,
                    "reason": "missing_quality_columns",
                    "columns": "|".join(missing_columns),
                }
            )
            continue
        if not rows:
            failures.append(
                {
                    "file": file_name,
                    "reason": "empty_quality_output",
                }
            )
            continue

        if file_name == "qa_key_audit.csv":
            for row in rows:
                value = as_number(row.get("duplicate_rows"))
                if value is None:
                    failures.append(
                        {
                            "file": file_name,
                            "audit_name": row.get("model", ""),
                            "reason": "invalid_quality_number",
                            "value": row.get("duplicate_rows", ""),
                        }
                    )
                elif value > 0:
                    failures.append(
                        {
                            "file": file_name,
                            "audit_name": row.get("model", ""),
                            "reason": "duplicate_key_rows",
                            "value": row.get("duplicate_rows", ""),
                        }
                    )
        elif file_name == "qa_grain_audit.csv":
            for row in rows:
                value = as_number(row.get("violating_baskets"))
                if value is None:
                    failures.append(
                        {
                            "file": file_name,
                            "audit_name": row.get("audit_name", ""),
                            "reason": "invalid_quality_number",
                            "value": row.get("violating_baskets", ""),
                        }
                    )
                elif value > 0:
                    failures.append(
                        {
                            "file": file_name,
                            "audit_name": row.get("audit_name", ""),
                            "reason": "basket_grain_inconsistency",
                            "value": row.get("violating_baskets", ""),
                        }
                    )
        elif file_name == "qa_reference_coverage.csv":
            for row in rows:
                value = as_number(row.get("violating_rows"))
                if value is None:
                    failures.append(
                        {
                            "file": file_name,
                            "audit_name": row.get("audit_name", ""),
                            "reason": "invalid_quality_number",
                            "value": row.get("violating_rows", ""),
                        }
                    )
                elif value > 0:
                    failures.append(
                        {
                            "file": file_name,
                            "audit_name": row.get("audit_name", ""),
                            "reason": "unmatched_reference",
                            "value": row.get("violating_rows", ""),
                        }
                    )
        elif file_name == "qa_layer_reconciliation.csv":
            for row in rows:
                if row.get("status", "").strip().lower() != "pass":
                    failures.append(
                        {
                            "file": file_name,
                            "audit_name": row.get("audit_name", ""),
                            "reason": "layer_reconciliation_review",
                            "status": row.get("status", ""),
                        }
                    )
        elif file_name == "qa_transaction_anomalies.csv":
            for row in rows:
                value = as_number(row.get("violating_rows"))
                if value is None:
                    failures.append(
                        {
                            "file": file_name,
                            "audit_name": row.get("audit_name", ""),
                            "reason": "invalid_quality_number",
                            "value": row.get("violating_rows", ""),
                        }
                    )
                    continue
                if value <= 0:
                    continue
                audit_name = row.get("audit_name", "")
                item = {
                    "file": file_name,
                    "audit_name": audit_name,
                    "value": row.get("violating_rows", ""),
                    "reason": "transaction_anomaly_retained_for_review",
                }
                if audit_name in BLOCKING_TRANSACTION_ANOMALIES:
                    failures.append(item)
                else:
                    warnings.append(item)

    return {
        "ready": not failures,
        "checked_files": checked_files,
        "failures": failures,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--drive-root", type=Path, required=True)
    args = parser.parse_args()

    artifact_root = require_drive_path(args.artifact_root, args.drive_root, "--artifact-root")
    qa_root = artifact_root / "04_qa_reports"
    result = evaluate_quality_gate(qa_root)
    output_path = qa_root / "qa_quality_gate.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(output_path), **result}, ensure_ascii=False))
    if not result["ready"]:
        raise SystemExit(
            "Quality gate failed; inspect 04_qa_reports/qa_quality_gate.json"
        )


if __name__ == "__main__":
    main()
