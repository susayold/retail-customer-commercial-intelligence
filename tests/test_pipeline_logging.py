from pathlib import Path

from src.build_parquet import count_csv_rows
from src.build_warehouse import output_table_name, output_table_names, referenced_relations

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



def test_parquet_row_counter_reads_written_file(tmp_path):
    import duckdb

    path = tmp_path / "sample.parquet"
    connection = duckdb.connect(":memory:")
    try:
        connection.execute(
            "COPY (SELECT * FROM range(3) AS t(value)) TO ? (FORMAT PARQUET)",
            [path.as_posix()],
        )
        from src.build_parquet import count_parquet_rows

        assert count_parquet_rows(connection, path) == 3
    finally:
        connection.close()


def test_warehouse_output_helper_lists_multi_statement_outputs():
    sql = """
    CREATE TABLE first_output AS SELECT 1 AS value;
    CREATE OR REPLACE TABLE second_output AS SELECT 2 AS value;
    """
    assert output_table_names(sql) == ["first_output", "second_output"]
