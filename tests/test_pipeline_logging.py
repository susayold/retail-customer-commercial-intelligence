from pathlib import Path

from src.build_parquet import count_csv_rows
from src.build_warehouse import output_table_name, referenced_relations

ROOT = Path(__file__).resolve().parents[1]


def test_parquet_row_counter_excludes_header(tmp_path):
    path = tmp_path / "source.csv"
    path.write_text("id,value\n1,a\n2,b\n", encoding="utf-8")
    assert count_csv_rows(path) == 2


def test_warehouse_output_and_input_helpers():
    sql = """
    CREATE OR REPLACE TABLE mart_example AS
    SELECT * FROM raw_transaction_data
    JOIN dim_product USING (product_id)
    """
    assert output_table_name(sql) == "mart_example"
    assert referenced_relations(sql, {"raw_transaction_data", "dim_product"}) == {
        "raw_transaction_data",
        "dim_product",
    }
