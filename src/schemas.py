"""
src/schemas.py

Pydantic models for AcreIQ analyst drafts, deterministic verification reports,
time series datapoints, automated market signals, and audit checks.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TimeSeriesPoint(BaseModel):
    month_year: Optional[str] = None
    period: Optional[str] = None
    volume: Optional[int] = None
    total_volume: Optional[int] = None
    monthly_avg_sqm: Optional[float] = None
    overall_price_sqm: Optional[float] = None
    ready_avg_sqm: Optional[float] = None
    ready_price_sqm: Optional[float] = None
    offplan_avg_sqm: Optional[float] = None
    offplan_price_sqm: Optional[float] = None


class MarketSignal(BaseModel):
    type: str
    severity: str
    title: str
    period: str
    description: str
    drilldown_prompt: str


class PeriodDelta(BaseModel):
    start_period: str
    end_period: str
    volume_change_pct: float
    price_sqm_change_pct: float
    start_price_sqm: Optional[float] = None
    end_price_sqm: Optional[float] = None


class AuditCheckItem(BaseModel):
    name: str
    passed: bool
    detail: str


class AnalystDraft(BaseModel):
    area_analyzed: str
    cadastral_name: str
    transaction_count: int
    avg_price_aed: float
    median_price_aed: float
    avg_sqm_price_aed: float
    market_summary: str
    sample_transaction_ids: List[str] = Field(default_factory=list)


class VerificationReport(BaseModel):
    is_grounded: bool
    final_output: str
    discrepancies: List[str] = Field(default_factory=list)
    source_trace_ids: List[str] = Field(default_factory=list)
    timeseries: Optional[List[Dict[str, Any]]] = None
    market_signals: Optional[List[MarketSignal]] = None
    delta: Optional[PeriodDelta] = None
    audit_checks: Optional[List[AuditCheckItem]] = None
    suggested_prompts: Optional[List[str]] = Field(default_factory=list)
    is_comparison: bool = False
    area1_label: Optional[str] = None
    area2_label: Optional[str] = None


