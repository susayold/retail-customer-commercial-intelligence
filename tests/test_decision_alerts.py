from pathlib import Path

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
        sql = (
            ROOT / "sql/06_marts/13_mart_decision_alerts.sql"
        ).read_text(encoding="utf-8")
        connection.execute(sql)

        row = connection.execute(
            """
            SELECT baseline, current, absolute_variance,
                   relative_variance, threshold, severity
            FROM mart_decision_alerts
            WHERE metric = 'panel_net_spend_decline'
            """
        ).fetchone()
        assert row == (100.0, 85.0, -15.0, -0.15, -0.10, "high")
    finally:
        connection.close()
