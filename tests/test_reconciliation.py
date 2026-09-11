from src.reconcile import load


def test_reconciliation_loader_reads_metric_values(tmp_path):
    sql = tmp_path / "sql.csv"
    bi = tmp_path / "bi.csv"
    sql.write_text("metric,value\nPanel Net Spend,100\n")
    bi.write_text("metric,value\nPanel Net Spend,100\n")
    assert load(sql) == load(bi)
