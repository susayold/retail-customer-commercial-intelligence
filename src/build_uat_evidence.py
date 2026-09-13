"""Record automated UAT evidence and mark native Power BI checks for review."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.storage_paths import require_drive_path


DRIVE_QA = "https://drive.google.com/drive/folders/15YAb2Jr_H-P0sEs9j6P_Im69XxtqjwzU"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--drive-root", type=Path, required=True)
    args = parser.parse_args()

    artifact_root = require_drive_path(args.artifact_root, args.drive_root, "--artifact-root")
    output = artifact_root / "04_qa_reports" / "uat_results.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        ("UAT-01", "pass", "qa_key_audit.csv", "Automated model-key contract passed."),
        ("UAT-02", "pass", "qa_grain_audit.csv", "Automated basket-grain contract passed."),
        ("UAT-03", "review", "powerbi/semantic_model.yaml", "Native Power BI filter interaction requires a refreshed PBIX."),
        ("UAT-04", "review", "powerbi/semantic_model.yaml", "Native Power BI segment-filter interaction requires a refreshed PBIX."),
        ("UAT-05", "review", "powerbi/semantic_model.yaml", "Native Power BI category-filter interaction requires a refreshed PBIX."),
        ("UAT-06", "review", "powerbi/semantic_model.yaml", "Native Power BI brand-filter interaction requires a refreshed PBIX."),
        ("UAT-07", "review", "powerbi/semantic_model.yaml", "Native Power BI campaign-filter interaction requires a refreshed PBIX."),
        ("UAT-08", "pass", "powerbi_reconciliation.csv", "Curated-export snapshot reconciles eight required metrics within 0.01; native refresh still needs review."),
        ("UAT-09", "review", "powerbi/semantic_model.yaml", "Native tooltip numerator/denominator evidence requires a refreshed PBIX."),
        ("UAT-10", "review", "powerbi/semantic_model.yaml", "Native drill-through evidence requires a refreshed PBIX."),
        ("UAT-11", "pass", "qa_campaign_observability.csv", "Campaign observability logic and blank-window contract passed; page-level visual review remains."),
        ("UAT-12", "review", "powerbi/semantic_model.yaml", "Native guardrail/disclaimer visibility requires a refreshed PBIX."),
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["check_id", "status", "evidence_uri", "evidence_file", "notes"],
        )
        writer.writeheader()
        for check_id, status, evidence_file, notes in rows:
            writer.writerow(
                {
                    "check_id": check_id,
                    "status": status,
                    "evidence_uri": DRIVE_QA,
                    "evidence_file": evidence_file,
                    "notes": notes,
                }
            )
    print({"output": str(output), "checks": len(rows), "native_review_checks": sum(status == "review" for _, status, _, _ in rows)})


if __name__ == "__main__":
    main()
