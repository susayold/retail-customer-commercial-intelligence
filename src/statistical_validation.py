"""Run business-facing statistical validation against the Drive-backed DuckDB."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import duckdb
import numpy as np
from scipy import stats


def bootstrap_mean_difference(
    left: np.ndarray,
    right: np.ndarray,
    iterations: int = 2000,
    seed: int = 42,
) -> tuple[float, float, float]:
    if len(left) == 0 or len(right) == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    observed = float(left.mean() - right.mean())
    draws = np.empty(iterations)
    for index in range(iterations):
        left_sample = rng.choice(left, size=len(left), replace=True)
        right_sample = rng.choice(right, size=len(right), replace=True)
        draws[index] = left_sample.mean() - right_sample.mean()
    lower, upper = np.quantile(draws, [0.025, 0.975])
    return observed, float(lower), float(upper)


def cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) < 2 or len(right) < 2:
        return float("nan")
    pooled_variance = (
        (len(left) - 1) * left.var(ddof=1)
        + (len(right) - 1) * right.var(ddof=1)
    ) / (len(left) + len(right) - 2)
    if pooled_variance <= 0:
        return 0.0
    return float((left.mean() - right.mean()) / np.sqrt(pooled_variance))


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return (float("nan"), float("nan"))
    proportion = successes / total
    denominator = 1 + z**2 / total
    centre = (proportion + z**2 / (2 * total)) / denominator
    margin = z * np.sqrt(
        proportion * (1 - proportion) / total + z**2 / (4 * total**2)
    ) / denominator
    return float(centre - margin), float(centre + margin)


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    args = parser.parse_args()

    output_dir = args.artifact_root / "04_qa_reports" / "statistics"
    connection = duckdb.connect(str(args.database), read_only=True)
    try:
        basket_rows = connection.execute(
            """
            SELECT basket_net_spend, COALESCE(segment, 'Unknown') AS segment
            FROM mart_basket
            """
        ).fetchall()
        groups: dict[str, np.ndarray] = {}
        for segment in sorted({row[1] for row in basket_rows}):
            groups[segment] = np.array(
                [float(row[0]) for row in basket_rows if row[1] == segment],
                dtype=float,
            )
        basket_stats = []
        for segment, values in groups.items():
            others = np.concatenate(
                [candidate for name, candidate in groups.items() if name != segment]
            ) if len(groups) > 1 else np.array([], dtype=float)
            difference, lower, upper = bootstrap_mean_difference(values, others)
            basket_stats.append({
                "segment": segment,
                "n": len(values),
                "mean_basket_value": float(values.mean()) if len(values) else float("nan"),
                "median_basket_value": float(np.median(values)) if len(values) else float("nan"),
                "mean_vs_other_segments": difference,
                "ci_low": lower,
                "ci_high": upper,
                "effect_size_cohens_d": cohens_d(values, others),
            })
        write_rows(
            output_dir / "stats_basket_by_segment.csv",
            ["segment", "n", "mean_basket_value", "median_basket_value",
             "mean_vs_other_segments", "ci_low", "ci_high", "effect_size_cohens_d"],
            basket_stats,
        )

        promotion_rows = connection.execute(
            """
            SELECT
                promo_state_group,
                panel_sales / NULLIF(product_store_weeks, 0)
            FROM mart_promotion_category_week
            WHERE product_store_weeks > 0
            """
        ).fetchall()
        promotion_groups: dict[str, np.ndarray] = {}
        for state in sorted({row[0] for row in promotion_rows}):
            promotion_groups[state] = np.array(
                [float(row[1]) for row in promotion_rows if row[0] == state],
                dtype=float,
            )
        promotion_values = [values for values in promotion_groups.values() if len(values)]
        if len(promotion_values) >= 2:
            kruskal_stat, kruskal_p = stats.kruskal(*promotion_values)
            total_n = sum(len(values) for values in promotion_values)
            eta_squared = max(
                0.0,
                float((kruskal_stat - len(promotion_values) + 1) / (total_n - len(promotion_values))),
            ) if total_n > len(promotion_values) else float("nan")
        else:
            kruskal_stat, kruskal_p, eta_squared = (float("nan"), float("nan"), float("nan"))
        promotion_stats = [
            {
                "promo_state_group": state,
                "n": len(values),
                "mean_panel_sales_per_product_store_week": float(values.mean()),
                "median_panel_sales_per_product_store_week": float(np.median(values)),
                "kruskal_wallis_stat": float(kruskal_stat),
                "kruskal_wallis_p_value": float(kruskal_p),
                "effect_size_eta_squared": eta_squared,
            }
            for state, values in promotion_groups.items()
        ]
        write_rows(
            output_dir / "stats_promotion_state.csv",
            ["promo_state_group", "n", "mean_panel_sales_per_product_store_week",
             "median_panel_sales_per_product_store_week", "kruskal_wallis_stat",
             "kruskal_wallis_p_value", "effect_size_eta_squared"],
            promotion_stats,
        )

        campaign_rows = connection.execute(
            """
            SELECT campaign_type, CAST(redeemed_coupon_flag AS INTEGER)
            FROM mart_campaign_household
            """
        ).fetchall()
        campaign_stats = []
        for campaign_type in sorted({row[0] for row in campaign_rows}):
            values = [int(row[1]) for row in campaign_rows if row[0] == campaign_type]
            successes = sum(values)
            lower, upper = wilson_interval(successes, len(values))
            campaign_stats.append({
                "campaign_type": campaign_type,
                "n_recipients": len(values),
                "redeemers": successes,
                "redemption_rate": successes / len(values) if values else float("nan"),
                "ci_low": lower,
                "ci_high": upper,
            })
        write_rows(
            output_dir / "stats_campaign_redemption.csv",
            ["campaign_type", "n_recipients", "redeemers", "redemption_rate", "ci_low", "ci_high"],
            campaign_stats,
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
