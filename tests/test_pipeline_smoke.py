from pathlib import Path

from src.utils.duckdb_client import connect, register_raw_views

ROOT = Path(__file__).resolve().parents[1]


def test_full_sql_chain_runs_on_synthetic_fixture():
    connection = connect(":memory:")
    try:
        register_raw_views(connection, ROOT / "tests/fixtures")
        sql_root = ROOT / "sql"
        model_paths = sorted(
            path
            for path in sql_root.rglob("*.sql")
            if "07_quality" not in path.parts and "09_exports" not in path.parts
        )
        qa_paths = sorted((sql_root / "07_quality").glob("*.sql"))
        for sql_path in model_paths + qa_paths:
            connection.execute(sql_path.read_text(encoding="utf-8"))
        assert connection.execute("SELECT COUNT(*) FROM mart_panel_weekly").fetchone()[0] > 0
        assert connection.execute("SELECT COUNT(*) FROM mart_campaign_summary").fetchone()[0] > 0
        assert connection.execute("SELECT COUNT(*) FROM qa_grain_audit").fetchone()[0] == 3
    finally:
        connection.close()