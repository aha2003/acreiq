# src/db.py
import os
import duckdb
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("APP_ENV", "local").strip().lower()
# Strip any stray single or double quotes from the env var
raw_csv = os.getenv("CSV_PATH", "data/dld_transactions.csv")
CSV_PATH = raw_csv.strip().strip("'").strip('"')
GCP_PROJECT = os.getenv("GCP_PROJECT", "").strip().strip("'").strip('"')

class DatabaseEngine:
    def __init__(self):
        self.env = ENV
        self.duck_conn = None
        self.bq_client = None

        if self.env == "prod" and GCP_PROJECT:
            try:
                from google.cloud import bigquery
                self.bq_client = bigquery.Client(project=GCP_PROJECT)
            except Exception as e:
                print(f"[WARN] Failed to initialize BigQuery: {e}. Falling back to DuckDB.")
                self._init_duckdb()
        else:
            self._init_duckdb()

    def _init_duckdb(self):
        self.duck_conn = duckdb.connect(database=":memory:")
        abs_csv = os.path.abspath(CSV_PATH)
        if os.path.exists(abs_csv):
            self.duck_conn.execute("""
                CREATE TABLE transactions AS 
                SELECT 
                    transaction_id,
                    TRY_CAST(instance_date AS DATE) AS instance_date,
                    LOWER(TRIM(area_name_en)) AS area_name_en,
                    LOWER(TRIM(trans_group_en)) AS trans_group_en,
                    TRIM(reg_type_en) AS reg_type_en,
                    TRY_CAST(REPLACE(CAST(actual_worth AS VARCHAR), ',', '') AS DOUBLE) AS actual_worth,
                    TRY_CAST(REPLACE(CAST(procedure_area AS VARCHAR), ',', '') AS DOUBLE) AS procedure_area,
                    TRY_CAST(REPLACE(CAST(meter_sale_price AS VARCHAR), ',', '') AS DOUBLE) AS meter_sale_price
                FROM read_csv_auto(?);
            """, [abs_csv])
            
            self.duck_conn.execute("CREATE INDEX idx_area_trans ON transactions (area_name_en, trans_group_en);")
            print(f"[INFO] Ingested and indexed DLD dataset with reg_type_en from {abs_csv}")
        else:
            print(f"[ERROR] CSV not found at {abs_csv}")

    def execute_query(self, query: str, params: dict):
        if self.duck_conn is not None:
            return self.duck_conn.execute(query, params).fetchdf()
        else:
            from google.cloud import bigquery
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(k, "STRING" if isinstance(v, str) else "INT64", v)
                    for k, v in params.items()
                ]
            )
            return self.bq_client.query(query, job_config=job_config).to_dataframe()

db_engine = DatabaseEngine()