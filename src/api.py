"""
src/api.py

FastAPI application layer for AcreIQ.

Exposes:
  - POST /v1/chat   : run a user query through the analyst -> auditor pipeline
  - GET  /healthz    : liveness/readiness probe for Cloud Run

Run locally:
    uvicorn src.api:app --reload --port 8080

Run in production (Cloud Run sets $PORT):
    uvicorn src.api:app --host 0.0.0.0 --port $PORT
"""

import logging
import time
import uuid
from typing import List, Optional, Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.agents import AcreIQWorkflow
from src.schemas import (
    AnalystDraft,
    VerificationReport,
    MarketSignal,
    PeriodDelta,
    AuditCheckItem,
)

# --------------------------------------------------------------------------
# Structured logging
# --------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
           '"logger": "%(name)s", "message": %(message)r}',
)
logger = logging.getLogger("acreiq.api")

# --------------------------------------------------------------------------
# App + workflow singleton
# --------------------------------------------------------------------------
app = FastAPI(
    title="AcreIQ API",
    description="Grounded Dubai real-estate market analysis over DLD transaction data.",
    version="1.0.0",
)

# Enable CORS for React frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

workflow = AcreIQWorkflow()


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User's market question.")


class ChatResponse(BaseModel):
    request_id: str
    is_grounded: bool
    final_output: str
    discrepancies: List[str]
    source_trace_ids: List[str]
    latency_ms: int
    timeseries: Optional[List[Dict[str, Any]]] = None
    market_signals: Optional[List[MarketSignal]] = None
    delta: Optional[PeriodDelta] = None
    audit_checks: Optional[List[AuditCheckItem]] = None
    suggested_prompts: Optional[List[str]] = None
    is_comparison: bool = False
    area1_label: Optional[str] = None
    area2_label: Optional[str] = None


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.get("/healthz", status_code=status.HTTP_200_OK)
def healthz():
    return {"status": "ok"}


@app.post("/v1/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    logger.info(f"request_id={request_id} received query={payload.query!r}")

    try:
        report = workflow.execute(payload.query)
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.error(f"request_id={request_id} failed after {latency_ms}ms: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream model/tool error: {exc}",
        )

    latency_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        f"request_id={request_id} grounded={report.is_grounded} latency_ms={latency_ms}"
    )

    return ChatResponse(
        request_id=request_id,
        is_grounded=report.is_grounded,
        final_output=report.final_output,
        discrepancies=report.discrepancies,
        source_trace_ids=report.source_trace_ids,
        latency_ms=latency_ms,
        timeseries=report.timeseries,
        market_signals=report.market_signals,
        delta=report.delta,
        audit_checks=report.audit_checks,
        suggested_prompts=report.suggested_prompts,
        is_comparison=report.is_comparison,
        area1_label=report.area1_label,
        area2_label=report.area2_label,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = str(uuid.uuid4())
    logger.error(f"request_id={request_id} unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"request_id": request_id, "error": str(exc)},
    )