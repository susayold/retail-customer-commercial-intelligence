import shutil
import sys
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


def test_curated_parquet_carries_lineage_metadata(tmp_path, monkeypatch):
    from src.build_parquet import main
    from src.inventory import EXPECTED_FILES

    drive_root = tmp_path / "drive"
    raw_root = drive_root / "01_raw_source"
    output_root = drive_root / "02_curated_parquet"
    raw_root.mkdir(parents=True)
    for file_name in EXPECTED_FILES:
        shutil.copy(ROOT / "tests" / "fixtures" / file_name, raw_root / file_name)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_parquet",
            "--input",
            str(raw_root),
            "--output",
            str(output_root),
            "--drive-root",
            str(drive_root),
            "--pipeline-run-id",
            "run-test-lineage",
        ],
    )
    main()

    import duckdb

    connection = duckdb.connect(":memory:")
    try:
        columns = {
            row[0]
            for row in connection.execute(
                "DESCRIBE SELECT * FROM read_parquet(?)",
                [str(output_root / "transaction_data.parquet")],
            ).fetchall()
        }
        assert {"source_file", "ingestion_timestamp", "pipeline_run_id", "schema_version"} <= columns
        assert connection.execute(
            "SELECT DISTINCT pipeline_run_id FROM read_parquet(?)",
            [str(output_root / "transaction_data.parquet")],
        ).fetchone()[0] == "run-test-lineage"
    finally:
        connection.close()


def test_warehouse_output_helper_lists_multi_statement_outputs():
    sql = """
    CREATE TABLE first_output AS SELECT 1 AS value;
    CREATE OR REPLACE TABLE second_output AS SELECT 2 AS value;
    """
    assert output_table_names(sql) == ["first_output", "second_output"]
