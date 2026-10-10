# src/tools.py
from typing import Optional, Dict, List, Any
import pandas as pd
from pydantic import BaseModel, Field
from src.db import db_engine

COMMUNITY_ALIASES: Dict[str, str] = {
    # Popular Marketing Names -> Exact Database Match
    "dubai marina": "DUBAI MARINA",
    "marsa dubai": "DUBAI MARINA",
    "downtown dubai": "BURJ KHALIFA",
    "downtown": "BURJ KHALIFA",
    "burj khalifa": "BURJ KHALIFA",
    "business bay": "BUSINESS BAY",
    "palm jumeirah": "PALM JUMEIRAH", 
    "furjan": "AL FURJAN",
    "al furjan": "AL FURJAN",
    "jumeirah village circle": "JUMEIRAH VILLAGE CIRCLE",
    "jvc": "JUMEIRAH VILLAGE CIRCLE",
    "jumeirah village triangle": "JUMEIRAH VILLAGE TRIANGLE",
    "jvt": "JUMEIRAH VILLAGE TRIANGLE",
    "jumeirah lakes towers": "JUMEIRAH LAKES TOWERS",
    "jumeirah lake towers": "JUMEIRAH LAKES TOWERS",
    "jlt": "JUMEIRAH LAKES TOWERS",
    "arjan": "ARJAN",
    "dubai sports city": "DUBAI SPORTS CITY",
    "motor city": "MOTOR CITY",
    "dubai production city": "DUBAI PRODUCTION CITY",
    "dubai studio city": "DUBAI STUDIO CITY",
    "silicon oasis": "SILICON OASIS",
    "dubai south": "DUBAI SOUTH",
    "international city": "INTERNATIONAL CITY PH 1",
    "difc": "TRADE CENTER SECOND", 
}

class MarketQueryInput(BaseModel):
    area_name: str = Field(..., description="Area name in English (e.g. 'Dubai Marina', 'Business Bay')")
    trans_group: Optional[str] = Field(default="Sales", description="Transaction type, e.g., 'Sales', 'Mortgages'")
    reg_type: Optional[str] = Field(default=None, description="Property status filter: 'Ready', 'Off-Plan', or None")
    start_date: Optional[str] = Field(default=None, description="ISO format start date YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="ISO format end date YYYY-MM-DD")
    limit_records: Optional[int] = Field(default=None, description="Max records to sample. Set to None to process all matching records.")

def get_area_metrics(
    area_name: str, 
    trans_group: str = "Sales",
    reg_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> dict:
    cleaned_input = area_name.strip().lower()
    target_area = COMMUNITY_ALIASES.get(cleaned_input, cleaned_input)
    area_filter_pattern = f"%{target_area}%"

    # Map colloquial segment names to DLD registry patterns
    reg_type_filter = None
    if reg_type:
        rt = reg_type.strip().lower()
        if "off" in rt:
            reg_type_filter = "%off%"
        elif "ready" in rt or "exist" in rt:
            reg_type_filter = "%ready%"

    # Robust query supporting both dld_transactions and transactions view
    sql = """
        SELECT 
            transaction_id,
            instance_date,
            area_name_en,
            trans_group_en,
            reg_type_en,
            actual_worth,
            actual_area,
            meter_sale_price
        FROM dld_transactions
        WHERE LOWER(area_name_en) LIKE LOWER(?)
          AND LOWER(trans_group_en) LIKE LOWER(?)
          AND actual_worth IS NOT NULL
          AND actual_worth > 0
          AND (? IS NULL OR LOWER(reg_type_en) LIKE ?)
          AND (? IS NULL OR instance_date >= TRY_CAST(? AS DATE))
          AND (? IS NULL OR instance_date <= TRY_CAST(? AS DATE))
        ORDER BY instance_date DESC
        LIMIT 5000;
    """
    
    trans_group_pattern = f"%{trans_group.strip()}%"
    params = [
        area_filter_pattern,
        trans_group_pattern,
        reg_type_filter,
        reg_type_filter,
        start_date,
        start_date,
        end_date,
        end_date
    ]
    
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

def compare_areas_metrics(
    primary_area: str,
    secondary_area: str,
    trans_group: str = "Sales",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> dict:
    """Retrieves and aligns metrics for two communities side-by-side."""
    area1_res = get_area_metrics(primary_area, trans_group=trans_group, start_date=start_date, end_date=end_date)
    area2_res = get_area_metrics(secondary_area, trans_group=trans_group, start_date=start_date, end_date=end_date)

    if area1_res.get("status") != "SUCCESS" or area2_res.get("status") != "SUCCESS":
        return {
            "status": "PARTIAL_OR_FAILED",
            "area1": area1_res,
            "area2": area2_res
        }

    # Align periods into unified timeseries points
    ts1 = {item["month_year"]: item for item in area1_res.get("timeseries", [])}
    ts2 = {item["month_year"]: item for item in area2_res.get("timeseries", [])}

    all_periods = sorted(list(set(ts1.keys()) | set(ts2.keys())))
    merged_timeseries = []

    for period in all_periods:
        p1 = ts1.get(period, {})
        p2 = ts2.get(period, {})
        merged_timeseries.append({
            "month_year": period,
            "area1_name": area1_res.get("input_area", primary_area),
            "area2_name": area2_res.get("input_area", secondary_area),
            "area1_avg_sqm": p1.get("monthly_avg_sqm"),
            "area2_avg_sqm": p2.get("monthly_avg_sqm"),
            "area1_volume": p1.get("volume", 0),
            "area2_volume": p2.get("volume", 0),
        })

    a1_metrics = dict(area1_res.get("summary_metrics") or {})
    a1_metrics["transaction_count"] = area1_res.get("transaction_count", 0)

    a2_metrics = dict(area2_res.get("summary_metrics") or {})
    a2_metrics["transaction_count"] = area2_res.get("transaction_count", 0)

    return {
        "status": "SUCCESS",
        "is_comparison": True,
        "primary_area": area1_res.get("input_area", primary_area),
        "secondary_area": area2_res.get("input_area", secondary_area),
        "area1_metrics": a1_metrics,
        "area2_metrics": a2_metrics,
        "timeseries": merged_timeseries,
        "audit_trail": {
            "trace_sample_ids": (
                area1_res.get("audit_trail", {}).get("trace_sample_ids", [])[:3] +
                area2_res.get("audit_trail", {}).get("trace_sample_ids", [])[:3]
            )
        }
    }