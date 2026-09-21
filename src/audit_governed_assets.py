"""Audit the governed P0 assets after the DuckDB model has been built.

This stage checks relation existence, row counts and the promotion-universe
interpretation, then writes a machine-readable audit under Drive. It never
copies raw data.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from src.storage_paths import require_drive_path
from src.utils.duckdb_client import connect


REQUIRED_RELATIONS = (
    "dim_category",
    "dim_segment",
    "mart_store_weekly",
    "mart_category_household_weekly",
    "analysis_campaign_denominators",
    "analysis_promotion_universe_audit",
    "analysis_root_cause_lmdi",
    "analysis_category_materiality",
    "analysis_category_lmdi",
    "analysis_segment_stability",
    "analysis_first_observed_cohort",
    "analysis_demographic_summary",
    "analysis_executive_decisions",
)


def audit(database: Path, artifact_root: Path, run_id: str) -> dict[str, object]:
    qa_root = artifact_root / "04_qa_reports"
    qa_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    connection = connect(database, read_only=True)
    try:
        for relation in REQUIRED_RELATIONS:
            try:
                count = int(connection.execute(f"SELECT COUNT(*) FROM {relation}").fetchone()[0])
                status = "PASS" if count > 0 else "REVIEW"
                error = ""
            except Exception as exc:  # noqa: BLE001 - persisted as QA evidence
                count = 0
                status = "FAIL"
                error = f"{type(exc).__name__}: {exc}"
            rows.append({"run_id": run_id, "asset": relation, "relation": relation, "row_count": count, "status": status, "error": error})

        promotion = connection.execute(
            "SELECT none_state_status, total_rows, interpretation_boundary "
            "FROM analysis_promotion_universe_audit"
        ).fetchone()
        if promotion is not None:
            rows.append({
                "run_id": run_id,
                "asset": "promotion_universe_interpretation",
                "relation": "analysis_promotion_universe_audit",
                "row_count": int(promotion[1] or 0),
                "status": "PASS",
                "error": f"{promotion[0]}: {promotion[2]}",
            })
    finally:
        connection.close()

    output = qa_root / "governed_asset_audit.csv"
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["run_id", "asset", "relation", "row_count", "status", "error"])
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "run_id": run_id,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "required_assets": list(REQUIRED_RELATIONS),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows if row["asset"] in REQUIRED_RELATIONS) else "FAIL",
        "output": str(output),
    }
    (qa_root / "governed_asset_audit.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--drive-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    database = require_drive_path(args.database, args.drive_root, "--database")
    artifact_root = require_drive_path(args.artifact_root, args.drive_root, "--artifact-root")
    result = audit(database, artifact_root, args.run_id)
    print(json.dumps(result, ensure_ascii=False))
    if result["status"] != "PASS":
        raise SystemExit("Governed asset audit failed; inspect 04_qa_reports/governed_asset_audit.csv")


if __name__ == "__main__":
    main()
