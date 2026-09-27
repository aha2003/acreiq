# src/tools.py
from typing import Optional, Dict
from pydantic import BaseModel, Field
from src.db import db_engine

# Map common investor/commercial names to official DLD cadastral names
COMMUNITY_ALIASES: Dict[str, str] = {
    "dubai marina": "marsa dubai",
    "downtown dubai": "burj khalifa",
    "downtown": "burj khalifa",
    "jumeirah village circle": "al barsha south fourth",
    "jvc": "al barsha south fourth",
    "jumeirah lakes towers": "al thanyah fifth",
    "jumeirah lake towers": "al thanyah fifth", 
    "jlt": "al thanyah fifth",
    "business bay": "business bay",
    "palm jumeirah": "palm jumeirah",
    "international city": "al warsan first",
}

class MarketQueryInput(BaseModel):
    area_name: str = Field(..., description="Area name in English (e.g. 'Dubai Marina', 'Business Bay', 'Marsa Dubai')")
    trans_group: Optional[str] = Field(default="Sales", description="Transaction type, e.g., 'Sales', 'Mortgages'")
    limit_records: Optional[int] = Field(default=500, description="Max records to sample for analysis")

def get_area_metrics(area_name: str, trans_group: str = "Sales") -> dict:
    """
    Computes pricing metrics and returns ground-truth registered transaction records 
    from the Dubai Land Department dataset for verification.
    """
    cleaned_input = area_name.strip().lower()
    # Normalize colloquial market name to registry name if alias exists
    target_area = COMMUNITY_ALIASES.get(cleaned_input, cleaned_input)

    sql = """
        WITH cleaned_transactions AS (
            SELECT 
                transaction_id,
                instance_date,
                area_name_en,
                trans_group_en,
                TRY_CAST(REPLACE(CAST(actual_worth AS VARCHAR), ',', '') AS DOUBLE) AS actual_worth,
                TRY_CAST(REPLACE(CAST(procedure_area AS VARCHAR), ',', '') AS DOUBLE) AS procedure_area,
                TRY_CAST(REPLACE(CAST(meter_sale_price AS VARCHAR), ',', '') AS DOUBLE) AS meter_sale_price
            FROM transactions
        )
        SELECT 
            transaction_id,
            instance_date,
            area_name_en,
            actual_worth,
            procedure_area,
            meter_sale_price
        FROM cleaned_transactions
        WHERE LOWER(area_name_en) = LOWER($area_name)
          AND LOWER(trans_group_en) = LOWER($trans_group)
          AND actual_worth IS NOT NULL
          AND actual_worth > 0
        ORDER BY instance_date DESC
        LIMIT 500;
    """
    
    df = db_engine.execute_query(sql, {"area_name": target_area, "trans_group": trans_group})

    if df.empty:
        return {
            "status": "NOT_FOUND",
            "searched_area": target_area,
            "message": f"No registered {trans_group} transactions found for area '{target_area}'."
        }

    total_count = len(df)
    avg_price = float(df["actual_worth"].mean())
    median_price = float(df["actual_worth"].median())
    avg_sqm_price = float(df["meter_sale_price"].dropna().mean()) if not df["meter_sale_price"].dropna().empty else 0.0

    return {
        "status": "SUCCESS",
        "cadastral_area": target_area,
        "input_area": area_name,
        "transaction_count": total_count,
        "summary_metrics": {
            "avg_price_aed": round(avg_price, 2),
            "median_price_aed": round(median_price, 2),
            "avg_sqm_price_aed": round(avg_sqm_price, 2)
        },
        "audit_trail": {
            "trace_sample_ids": df["transaction_id"].astype(str).head(5).tolist(),
            "latest_transaction_date": str(df["instance_date"].iloc[0])
        }
    }