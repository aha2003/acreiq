"""
src/db.py

Vectorized DuckDB Analytical OLAP Engine for AcreIQ.
Ingests official DLD transactions and executes deterministic aggregations.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import duckdb

logger = logging.getLogger("acreiq.db")


class DatabaseEngine:
    def __init__(self, csv_path: Optional[str] = None):
        self.csv_path = csv_path or os.getenv("CSV_PATH", "data/dld_transactions.csv")
        self.con = duckdb.connect(database=":memory:")
        self._initialize_schema()

    def _initialize_schema(self):
        """
        Loads the CSV and maps the exact headers into clean, typed columns.
        """
        logger.info(f"Loading and indexing DLD dataset from {self.csv_path}...")
        
        self.con.execute(f"""
            CREATE TABLE dld_transactions AS
            SELECT
                TRY_CAST("TRANSACTION_NUMBER" AS VARCHAR) AS transaction_id,
                TRY_CAST("INSTANCE_DATE" AS TIMESTAMP) AS instance_timestamp,
                CAST(TRY_CAST("INSTANCE_DATE" AS TIMESTAMP) AS DATE) AS instance_date,
                TRIM(COALESCE("GROUP_EN", '')) AS trans_group_en,
                TRIM(COALESCE("PROCEDURE_EN", '')) AS procedure_en,
                CASE 
                    WHEN "IS_OFFPLAN_EN" ILIKE '%off%plan%' THEN 'Off-Plan'
                    ELSE 'Ready'
                END AS reg_type_en,
                TRIM(COALESCE("IS_FREE_HOLD_EN", '')) AS is_free_hold,
                TRIM(COALESCE("USAGE_EN", '')) AS usage_en,
                TRIM(COALESCE("AREA_EN", '')) AS area_name_en,
                TRIM(COALESCE("PROP_TYPE_EN", '')) AS prop_type_en,
                TRIM(COALESCE("PROP_SB_TYPE_EN", '')) AS prop_sub_type_en,
                TRY_CAST("TRANS_VALUE" AS DOUBLE) AS actual_worth,
                TRY_CAST("PROCEDURE_AREA" AS DOUBLE) AS procedure_area,
                TRY_CAST("ACTUAL_AREA" AS DOUBLE) AS actual_area,
                TRIM(COALESCE("ROOMS_EN", '')) AS rooms_en,
                TRY_CAST("PARKING" AS INT) AS parking,
                TRIM(COALESCE("NEAREST_METRO_EN", '')) AS nearest_metro_en,
                TRIM(COALESCE("NEAREST_MALL_EN", '')) AS nearest_mall_en,
                TRIM(COALESCE("NEAREST_LANDMARK_EN", '')) AS nearest_landmark_en,
                TRIM(COALESCE("MASTER_PROJECT_EN", '')) AS master_project_en,
                TRIM(COALESCE("PROJECT_EN", '')) AS project_en,
                ROUND(TRY_CAST("TRANS_VALUE" AS DOUBLE) / NULLIF(TRY_CAST("ACTUAL_AREA" AS DOUBLE), 0), 2) AS meter_sale_price
            FROM read_csv_auto('{self.csv_path}', ignore_errors=true);
        """)

        self.con.execute("CREATE OR REPLACE VIEW transactions AS SELECT * FROM dld_transactions;")

        # Fast memory indexing for query filters and timeseries binning
        self.con.execute("CREATE INDEX idx_area ON dld_transactions(area_name_en);")
        self.con.execute("CREATE INDEX idx_date ON dld_transactions(instance_date);")

        row_count = self.con.execute("SELECT COUNT(*) FROM dld_transactions").fetchone()[0]
        max_date = self.con.execute("SELECT MAX(instance_date) FROM dld_transactions").fetchone()[0]
        min_date = self.con.execute("SELECT MIN(instance_date) FROM dld_transactions").fetchone()[0]
        logger.info(f"Ingested {row_count} DLD transactions. Window: {min_date} -> {max_date}")

    def get_max_date(self):
        """Anchors all relative filters (3M, 6M, 1Y) to the dataset's ceiling."""
        res = self.con.execute("SELECT MAX(instance_date) FROM dld_transactions").fetchone()
        return res[0] if res and res[0] else None
    
    def execute_query(self, sql: str, params: Optional[List[Any]] = None):
        if params is not None:
            return self.con.execute(sql, params).fetchdf()
        return self.con.execute(sql).fetchdf()

    def query_cadastral_metrics(
        self,
        area_pattern: str,
        duration: Optional[str] = "ALL",
        rooms: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes primary OLAP aggregation with statistical distributions,
        anchored duration filtering, and segmented market dynamics.
        """
        max_date = self.get_max_date()
        date_filter = ""
        
        # Anchors relative windows strictly to dataset's latest transaction date
        if max_date and duration and duration.upper() != "ALL":
            dur = duration.upper()
            if "3M" in dur:
                date_filter = f"AND instance_date >= (DATE '{max_date}' - INTERVAL 3 MONTH)"
            elif "6M" in dur:
                date_filter = f"AND instance_date >= (DATE '{max_date}' - INTERVAL 6 MONTH)"
            elif "1Y" in dur or "12M" in dur:
                date_filter = f"AND instance_date >= (DATE '{max_date}' - INTERVAL 1 YEAR)"

        room_filter = f"AND rooms_en ILIKE '%{rooms}%'" if rooms else ""

        # 1. High-level KPIs
        summary_query = f"""
            SELECT 
                COUNT(*) AS total_transactions,
                ROUND(MEDIAN(actual_worth), 2) AS median_price,
                ROUND(AVG(actual_worth), 2) AS avg_price,
                ROUND(AVG(meter_sale_price), 2) AS avg_price_sqm,
                ROUND(MIN(actual_worth), 2) AS min_price,
                ROUND(MAX(actual_worth), 2) AS max_price
            FROM dld_transactions
            WHERE area_name_en ILIKE '%{area_pattern}%'
              {date_filter} {room_filter};
        """
        summary = self.con.execute(summary_query).fetchdf().to_dict(orient="records")[0]

        if summary["total_transactions"] == 0:
            return {"total_transactions": 0}

        # 2. Ready vs. Off-Plan Breakdown
        segmentation_query = f"""
            SELECT 
                reg_type_en,
                COUNT(*) AS count,
                ROUND(AVG(actual_worth), 2) AS avg_price,
                ROUND(AVG(meter_sale_price), 2) AS avg_price_sqm
            FROM dld_transactions
            WHERE area_name_en ILIKE '%{area_pattern}%'
              {date_filter} {room_filter}
            GROUP BY reg_type_en;
        """
        segmentation = self.con.execute(segmentation_query).fetchdf().to_dict(orient="records")

        # 3. Bedroom Distribution & Pricing Spreads
        bedroom_query = f"""
            SELECT 
                rooms_en,
                COUNT(*) AS deals,
                ROUND(MEDIAN(actual_worth), 2) AS median_price,
                ROUND(AVG(meter_sale_price), 2) AS avg_price_sqm
            FROM dld_transactions
            WHERE area_name_en ILIKE '%{area_pattern}%'
              AND rooms_en != ''
              {date_filter}
            GROUP BY rooms_en
            ORDER BY deals DESC
            LIMIT 5;
        """
        bedroom_stats = self.con.execute(bedroom_query).fetchdf().to_dict(orient="records")

        # 4. Infrastructure & Transit Premiums
        transit_query = f"""
            SELECT 
                nearest_metro_en,
                COUNT(*) AS transactions,
                ROUND(AVG(meter_sale_price), 2) AS avg_sqm
            FROM dld_transactions
            WHERE area_name_en ILIKE '%{area_pattern}%'
              AND nearest_metro_en != ''
              {date_filter}
            GROUP BY nearest_metro_en
            ORDER BY transactions DESC
            LIMIT 3;
        """
        transit_stats = self.con.execute(transit_query).fetchdf().to_dict(orient="records")

        # 5. Dual-Axis Timeseries (Monthly buckets)
        timeseries_query = f"""
            SELECT 
                STRFTIME(DATE_TRUNC('month', instance_date), '%Y-%m') AS period,
                COUNT(*) AS total_volume,
                ROUND(AVG(CASE WHEN reg_type_en = 'Ready' THEN meter_sale_price END), 2) AS ready_price_sqm,
                ROUND(AVG(CASE WHEN reg_type_en = 'Off-Plan' THEN meter_sale_price END), 2) AS offplan_price_sqm,
                ROUND(AVG(meter_sale_price), 2) AS overall_price_sqm
            FROM dld_transactions
            WHERE area_name_en ILIKE '%{area_pattern}%'
              {date_filter}
            GROUP BY 1
            ORDER BY 1 ASC;
        """
        timeseries = self.con.execute(timeseries_query).fetchdf().to_dict(orient="records")

        # 6. Sample provenance IDs for deterministic auditing
        trace_ids = self.con.execute(f"""
            SELECT transaction_id FROM dld_transactions 
            WHERE area_name_en ILIKE '%{area_pattern}%' {date_filter}
            LIMIT 5
        """).fetchdf()["transaction_id"].dropna().tolist()

        return {
            **summary,
            "segmentation": segmentation,
            "bedroom_stats": bedroom_stats,
            "transit_stats": transit_stats,
            "timeseries": timeseries,
            "source_trace_ids": trace_ids
        }
    def compute_market_signals(self, area_pattern: str, duration: str = "6M") -> Dict[str, Any]:
        """
        Computes deterministic deltas and rule-based market signals 
        directly over vectorized DuckDB timeseries.
        """
        metrics = self.query_cadastral_metrics(area_pattern=area_pattern, duration=duration)
        timeseries = metrics.get("timeseries", [])
        
        if len(timeseries) < 2:
            return {
                "signals": [],
                "delta": None,
                "timeseries": timeseries
            }

        first_period = timeseries[0]
        last_period = timeseries[-1]

        # Calculate MoM and Period Deltas
        vol_change_pct = round(((last_period["total_volume"] - first_period["total_volume"]) / max(first_period["total_volume"], 1)) * 100, 1)
        price_change_pct = 0.0
        if first_period.get("overall_price_sqm") and last_period.get("overall_price_sqm"):
            price_change_pct = round(((last_period["overall_price_sqm"] - first_period["overall_price_sqm"]) / first_period["overall_price_sqm"]) * 100, 1)

        delta = {
            "start_period": first_period["period"],
            "end_period": last_period["period"],
            "volume_change_pct": vol_change_pct,
            "price_sqm_change_pct": price_change_pct,
            "start_price_sqm": first_period.get("overall_price_sqm"),
            "end_price_sqm": last_period.get("overall_price_sqm"),
        }

        # Rule-Based Anomaly Detection (Market Signals)
        signals = []
        max_vol_point = max(timeseries, key=lambda x: x["total_volume"])
        if max_vol_point["total_volume"] >= (first_period["total_volume"] * 1.5):
            signals.append({
                "type": "HIGH_ACTIVITY",
                "severity": "positive",
                "title": f"Volume Spike Detected ({max_vol_point['total_volume']} Deals)",
                "period": max_vol_point["period"],
                "description": f"Transaction volume peaked significantly in {max_vol_point['period']}, outpacing early-period baseline.",
                "drilldown_prompt": f"Why did transaction volume spike to {max_vol_point['total_volume']} deals in {max_vol_point['period']} for {area_pattern}?"
            })

        # Check for Off-Plan Premium Divergence
        for p in timeseries:
            offplan = p.get("offplan_price_sqm")
            ready = p.get("ready_price_sqm")
            if offplan and ready and ready > 0:
                spread = ((offplan - ready) / ready) * 100
                if spread >= 15.0:
                    signals.append({
                        "type": "OFFPLAN_PREMIUM",
                        "severity": "neutral",
                        "title": f"Elevated Off-Plan Premium ({round(spread, 1)}%)",
                        "period": p["period"],
                        "description": f"Off-plan development commanded a notable price/m² premium over ready inventory in {p['period']}.",
                        "drilldown_prompt": f"Explain the {round(spread, 1)}% off-plan premium over ready units in {area_pattern} during {p['period']}."
                    })
                    break

        return {
            "signals": signals,
            "delta": delta,
            "summary_metrics": {
                "total_transactions": metrics.get("total_transactions"),
                "median_price": metrics.get("median_price"),
                "avg_price": metrics.get("avg_price"),
                "avg_price_sqm": metrics.get("avg_price_sqm"),
            },
            "timeseries": timeseries,
            "source_trace_ids": metrics.get("source_trace_ids", [])
        }
    
db_engine = DatabaseEngine()