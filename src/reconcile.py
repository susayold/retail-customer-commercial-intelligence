"""Compare SQL and BI metric exports with explicit tolerances."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

VALUE_COLUMNS = ("value", "sql_value", "powerbi_value")


def load(path: Path) -> dict[str, float]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        value_column = next((name for name in VALUE_COLUMNS if name in fieldnames), None)
        if value_column is None or "metric" not in fieldnames:
            raise ValueError(
                f"{path} must contain metric and one of {', '.join(VALUE_COLUMNS)}"
            )
        values: dict[str, float] = {}
        for row in reader:
            metric = row.get("metric")
            if not metric:
                raise ValueError(f"{path} contains a row without metric")
            if metric in values:
                raise ValueError(f"{path} contains duplicate metric: {metric}")
            raw_value = row.get(value_column)
            values[metric] = math.nan if raw_value in (None, "") else float(raw_value)
        return values


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
