"""Enforce blocking data-quality stop conditions before analysis and BI exports."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REQUIRED_QA_FILES = (
    "qa_key_audit.csv",
    "qa_grain_audit.csv",
    "qa_reference_coverage.csv",
    "qa_layer_reconciliation.csv",
    "qa_transaction_anomalies.csv",
)
BLOCKING_TRANSACTION_ANOMALIES = {
    "missing_product",
    "missing_household",
    "missing_basket",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_number(value: str | None) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


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
        rows = read_rows(path)

        if file_name == "qa_key_audit.csv":
            for row in rows:
                if as_number(row.get("duplicate_rows")) > 0:
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
                if as_number(row.get("violating_baskets")) > 0:
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
                if as_number(row.get("violating_rows")) > 0:
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
    args = parser.parse_args()

    qa_root = args.artifact_root / "04_qa_reports"
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
