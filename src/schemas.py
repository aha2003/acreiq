# src/schemas.py
from typing import List, Optional
from pydantic import BaseModel, Field

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