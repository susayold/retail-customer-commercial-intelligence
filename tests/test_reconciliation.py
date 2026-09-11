from src.reconcile import load


def test_reconciliation_loader_reads_metric_values(tmp_path):
    sql = tmp_path / "sql.csv"
    bi = tmp_path / "bi.csv"
    sql.write_text("metric,value\nPanel Net Spend,100\n")
    bi.write_text("metric,value\nPanel Net Spend,100\n")
    assert load(sql) == load(bi)


def test_reconciliation_loader_accepts_powerbi_export_headers(tmp_path):
    exported = tmp_path / "export.csv"
    exported.write_text("metric,sql_value\nPanel Net Spend,100\n")
    assert load(exported) == {"Panel Net Spend": 100.0}


def test_reconciliation_loader_rejects_duplicate_metrics(tmp_path):
    duplicate = tmp_path / "duplicate.csv"
    duplicate.write_text("metric,value\nBaskets,1\nBaskets,2\n")
    try:
        load(duplicate)
    except ValueError as exc:
        assert "duplicate metric" in str(exc)
    else:
        raise AssertionError("duplicate metric should be rejected")
