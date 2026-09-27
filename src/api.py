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
from typing import List

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.agents import AcreIQWorkflow

# --------------------------------------------------------------------------
# Structured logging
# --------------------------------------------------------------------------
# Cloud Run / Cloud Logging parses JSON-formatted stdout logs automatically,
# so we keep the format simple and machine-readable rather than "pretty".
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
           '"logger": "%(name)s", "message": %(message)r}',
)
logger = logging.getLogger("acreiq.api")

# --------------------------------------------------------------------------
# App + workflow singleton
# --------------------------------------------------------------------------
# AcreIQWorkflow / DatabaseEngine are constructed once per container instance,
# not per-request -- the DuckDB connection / BigQuery client are reused across
# requests, matching how Cloud Run keeps warm instances alive between calls.
app = FastAPI(
    title="AcreIQ API",
    description="Grounded Dubai real-estate market analysis over DLD transaction data.",
    version="1.0.0",
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


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.get("/healthz", status_code=status.HTTP_200_OK)
def healthz():
    """
    Liveness/readiness probe.

    Cloud Run uses this to decide when a container is ready to receive
    traffic and whether to restart it. Keep this cheap and dependency-free
    on the hot path -- do NOT run a DB query here, or a slow/down database
    will take the whole container out of rotation.
    """
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
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catch-all so an unexpected error returns clean JSON instead of a raw
    traceback -- important once this is public-facing on Cloud Run.
    """
    request_id = str(uuid.uuid4())
    logger.error(f"request_id={request_id} unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"request_id": request_id, "error": "internal_server_error"},
    )