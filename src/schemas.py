# src/schemas.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TimeSeriesPoint(BaseModel):
    month_year: str = Field(description="Year and month in YYYY-MM format")
    volume: int = Field(description="Number of transactions in this month")
    monthly_avg_price: float = Field(description="Mean transaction value in AED")
    monthly_median_price: float = Field(description="Median transaction value in AED")
    monthly_avg_sqm: float = Field(description="Average price per square meter in AED")

class AnalystDraft(BaseModel):
    area_analyzed: str = Field(description="The area name analyzed")
    cadastral_name: str = Field(description="Official DLD cadastral name")
    transaction_count: int = Field(description="Number of transactions reviewed")
    avg_price_aed: float = Field(description="Stated average sale price in AED")
    median_price_aed: float = Field(description="Stated median sale price in AED")
    avg_sqm_price_aed: float = Field(description="Stated price per square meter in AED")
    market_summary: str = Field(description="Natural language summary of market conditions")
    sample_transaction_ids: List[str] = Field(description="Sample transaction IDs cited from the query tool")

class VerificationReport(BaseModel):
    is_grounded: bool = Field(description="True if all claims and numbers match source records")
    discrepancies: List[str] = Field(default_factory=list, description="Any detected hallucinations or mismatches")
    final_output: str = Field(description="The verified report delivered to the end user")
    source_trace_ids: List[str] = Field(description="Confirmed DLD registry transaction IDs")
    timeseries: Optional[List[TimeSeriesPoint]] = Field(
        default=None, 
        description="Aggregated monthly volume and price metrics for charting"
    )