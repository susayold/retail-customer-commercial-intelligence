"""Compare SQL and BI metric exports with explicit tolerances."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def load(path: Path) -> dict[str, float]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row["metric"]: float(row["value"]) for row in csv.DictReader(handle)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sql", type=Path, required=True)
    parser.add_argument("--bi", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tolerance", type=float, default=1e-6)
    args = parser.parse_args()

    sql = load(args.sql)
    bi = load(args.bi)
    metrics = sorted(set(sql) | set(bi))
    failures = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["metric", "sql_value", "powerbi_value", "difference", "tolerance", "status"],
        )
        writer.writeheader()
        for metric in metrics:
            sql_value = sql.get(metric, math.nan)
            bi_value = bi.get(metric, math.nan)
            difference = abs(sql_value - bi_value) if math.isfinite(sql_value) and math.isfinite(bi_value) else math.nan
            status = "pass" if math.isfinite(difference) and difference <= args.tolerance else "fail"
            failures += status == "fail"
            writer.writerow({
                "metric": metric,
                "sql_value": sql_value,
                "powerbi_value": bi_value,
                "difference": difference,
                "tolerance": args.tolerance,
                "status": status,
            })
    if failures:
        raise SystemExit(f"Reconciliation failed for {failures} metric(s); inspect {args.output}")


if __name__ == "__main__":
    main()
