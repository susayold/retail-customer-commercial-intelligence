from pathlib import Path

import pytest

from src.sql_renderer import render_sql_file
from src.utils.duckdb_client import connect


ROOT = Path(__file__).resolve().parents[1]


def test_decision_alerts_apply_threshold_to_relative_variance():
    connection = connect(":memory:")
    try:
        connection.execute(
            """
            CREATE TABLE mart_panel_weekly (
                week_number INTEGER,
                panel_net_spend DOUBLE,
                active_households DOUBLE,
                trips_per_household DOUBLE,
                spend_per_basket DOUBLE
            )
            """
        )
        connection.executemany(
            "INSERT INTO mart_panel_weekly VALUES (?, ?, ?, ?, ?)",
            [
                (1, 100.0, 100.0, 2.0, 50.0),
                (2, 85.0, 95.0, 1.9, 44.7368421053),
            ],
        )
        sql = render_sql_file(
            ROOT / "sql/06_marts/13_mart_decision_alerts.sql",
            ROOT / "config/analysis_thresholds.yaml",
        )
        connection.execute(sql)

        output_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info('mart_decision_alerts')").fetchall()
        }
        assert {
            "metric",
            "baseline",
            "current",
            "variance",
            "threshold",
            "severity",
            "scope",
        }.issubset(output_columns)
        assert {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT metric FROM mart_decision_alerts"
            ).fetchall()
        } == {
            "panel_net_spend_decline",
            "active_households_decline",
            "trip_frequency_decline",
        }

        row = connection.execute(
            """
            SELECT baseline, current, variance, absolute_variance,
                   relative_variance, threshold, severity
            FROM mart_decision_alerts
            WHERE metric = 'panel_net_spend_decline'
            """
        ).fetchone()
        (
            baseline,
            current,
            variance,
            absolute_variance,
            relative_variance,
            threshold,
            severity,
        ) = row
        assert baseline == pytest.approx(100.0)
        assert current == pytest.approx(85.0)
        assert variance == pytest.approx(-15.0)
        assert absolute_variance == pytest.approx(-15.0)
        assert absolute_variance == pytest.approx(variance)
        assert relative_variance == pytest.approx(-0.15)
        assert float(threshold) == pytest.approx(-0.10)
        assert severity == "high"
    finally:
        connection.close()
