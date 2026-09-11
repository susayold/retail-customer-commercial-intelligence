from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_governed_metrics_have_formula_and_grain():
    metrics = yaml.safe_load((ROOT / "config/metric_definitions.yaml").read_text())["metrics"]
    assert len(metrics) >= 10
    assert all(item.get("formula") and item.get("grain") for item in metrics.values())