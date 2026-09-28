# src/tools.py
from typing import Optional, Dict, List, Any
import pandas as pd
from pydantic import BaseModel, Field
from src.db import db_engine

COMMUNITY_ALIASES: Dict[str, str] = {
    "dubai marina": "marsa dubai",
    "downtown dubai": "burj khalifa",
    "downtown": "burj khalifa",
    "business bay": "business bay",
    "palm jumeirah": "palm jumeirah",
    "jumeirah village circle": "al barsha south fourth",
    "jvc": "al barsha south fourth",
    "jumeirah lakes towers": "al thanyah fifth",
    "jumeirah lake towers": "al thanyah fifth", 
    "jlt": "al thanyah fifth",
    "nad al sheba": "nad al shiba",
    "nad al sheba 1": "nad al shiba first",
    "nad al sheba 2": "nad al shiba second",
    "nad al sheba 3": "nad al shiba third",
    "nad al sheba 4": "nad al shiba fourth",
    "wadi al safaa": "wadi al safa",
    "international city": "al warsan first",
    "difc": "trade center second",
}

class MarketQueryInput(BaseModel):
    area_name: str = Field(..., description="Area name in English (e.g. 'Dubai Marina', 'Business Bay')")
    trans_group: Optional[str] = Field(default="Sales", description="Transaction type, e.g., 'Sales', 'Mortgages'")
    reg_type: Optional[str] = Field(default=None, description="Property status filter: 'Ready', 'Off-Plan', or None")
    start_date: Optional[str] = Field(default=None, description="ISO format start date YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="ISO format end date YYYY-MM-DD")
    limit_records: Optional[int] = Field(default=5000, description="Max records to sample")

def get_area_metrics(
    area_name: str, 
    trans_group: str = "Sales",
    reg_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> dict:
    cleaned_input = area_name.strip().lower()
    target_area = COMMUNITY_ALIASES.get(cleaned_input, cleaned_input)
    prefix_pattern = f"{target_area} %"

    # Map colloquial segment names to DLD registry patterns
    reg_type_filter = None
    if reg_type:
        rt = reg_type.strip().lower()
        if "off" in rt:
            reg_type_filter = "%off%"
        elif "ready" in rt or "exist" in rt:
            reg_type_filter = "%exist%"

    sql = """
        SELECT 
            transaction_id,
            instance_date,
            area_name_en,
            trans_group_en,
            reg_type_en,
            actual_worth,
            procedure_area,
            meter_sale_price
        FROM transactions
        WHERE (
            area_name_en = $area_name
            OR area_name_en LIKE $prefix_pattern
        )
          AND trans_group_en = LOWER($trans_group)
          AND actual_worth IS NOT NULL
          AND actual_worth > 0
          AND ($reg_type_filter IS NULL OR LOWER(reg_type_en) LIKE $reg_type_filter)
          AND ($start_date IS NULL OR instance_date >= TRY_CAST($start_date AS DATE))
          AND ($end_date IS NULL OR instance_date <= TRY_CAST($end_date AS DATE))
        ORDER BY instance_date DESC
        LIMIT 5000;
    """
    
    params = {
        "area_name": target_area,
        "prefix_pattern": prefix_pattern,
        "trans_group": trans_group,
        "reg_type_filter": reg_type_filter,
        "start_date": start_date,
        "end_date": end_date
    }
    
    df = db_engine.execute_query(sql, params)

    if df.empty:
        return {
            "status": "NOT_FOUND",
            "searched_area": target_area,
            "message": f"No registered {trans_group} transactions found matching criteria."
        }

    total_count = len(df)
    avg_price = float(df["actual_worth"].mean())
    median_price = float(df["actual_worth"].median())
    avg_sqm_price = float(df["meter_sale_price"].dropna().mean()) if not df["meter_sale_price"].dropna().empty else 0.0

    timeseries: List[Dict[str, Any]] = []
    try:
        temp_df = df.copy()
        temp_df["parsed_date"] = pd.to_datetime(temp_df["instance_date"], errors="coerce")
        temp_df = temp_df.dropna(subset=["parsed_date"])
        
        if not temp_df.empty:
            temp_df["month_year"] = temp_df["parsed_date"].dt.strftime("%Y-%m")
            
            grouped = temp_df.groupby("month_year")
            for month, group in grouped:
                # DLD classifies off-plan as 'Off-Plan Properties' and ready as 'Existing Properties'
                offplan_deals = group[group["reg_type_en"].str.lower().str.contains("off", na=False)]
                ready_deals = group[~group["reg_type_en"].str.lower().str.contains("off", na=False)]
                
                ready_avg_sqm = round(float(ready_deals["meter_sale_price"].dropna().mean()), 2) if not ready_deals["meter_sale_price"].dropna().empty else None
                offplan_avg_sqm = round(float(offplan_deals["meter_sale_price"].dropna().mean()), 2) if not offplan_deals["meter_sale_price"].dropna().empty else None

                timeseries.append({
                    "month_year": str(month),
                    "volume": int(len(group)),
                    "monthly_avg_price": round(float(group["actual_worth"].mean()), 2),
                    "monthly_median_price": round(float(group["actual_worth"].median()), 2),
                    "monthly_avg_sqm": round(float(group["meter_sale_price"].dropna().mean()), 2) if not group["meter_sale_price"].dropna().empty else 0.0,
                    "ready_avg_sqm": ready_avg_sqm,
                    "offplan_avg_sqm": offplan_avg_sqm
                })
            timeseries.sort(key=lambda x: x["month_year"])
    except Exception as e:
        print(f"[WARN] Failed to compute timeseries: {e}")
        timeseries = []

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
        "timeseries": timeseries,
        "audit_trail": {
            "trace_sample_ids": df["transaction_id"].astype(str).head(5).tolist(),
            "latest_transaction_date": str(df["instance_date"].iloc[0])
        }
    }