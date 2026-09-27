# AcreIQ

### Verifiable Financial Intelligence for 2023 Dubai Real Estate

[![Cloud Run](https://img.shields.io/badge/Cloud%20Run-Live%20API-4285F4?logo=googlecloud\&logoColor=white)](https://acreiq-api-zv7ueef3fq-ww.a.run.app/docs)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python\&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688?logo=fastapi\&logoColor=white)](https://fastapi.tiangolo.com/)
[![DuckDB](https://img.shields.io/badge/DuckDB-Analytical%20Engine-FFF000?logo=duckdb\&logoColor=000)](https://duckdb.org/)
[![GCP](https://img.shields.io/badge/Google%20Cloud-Production-4285F4?logo=googlecloud\&logoColor=white)](https://cloud.google.com/)

**AcreIQ** is an analytical AI engine and production REST API for performing verifiable financial intelligence over official **Dubai Land Department (DLD) real-estate transaction data covering the 2023 calendar year**.

The system is designed around a simple principle:

> **LLMs may explain financial data. They do not get to define the financial truth.**

Rather than relying on Vector RAG to retrieve and synthesize numerical information, AcreIQ executes deterministic SQL aggregation over transaction records using **DuckDB**, resolves natural-language locations against their legal cadastral entities, and subjects generated responses to a programmatic **Auditor Gate** before they are returned.

The result is an AI system where market figures are derived from transaction-level ground truth and can be traced back to the underlying DLD registry records.

---

## Architecture

```text
                           ┌──────────────────────┐
                           │      Client / LLM     │
                           │  Natural-Language     │
                           │       Query           │
                           └──────────┬───────────┘
                                      │
                                      ▼
                           ┌──────────────────────┐
                           │   Cadastral Entity   │
                           │      Resolution      │
                           │                      │
                           │ "Downtown Dubai"     │
                           │         ↓            │
                           │ "burj khalifa"       │
                           └──────────┬───────────┘
                                      │
                                      ▼
                     ┌────────────────────────────────┐
                     │        DuckDB Engine            │
                     │                                │
                     │  In-memory deterministic SQL    │
                     │  ─ Median                       │
                     │  ─ Mean                         │
                     │  ─ Transaction volume           │
                     │  ─ Average price / m²            │
                     │  ─ Source transaction records   │
                     └────────────────┬───────────────┘
                                      │
                                      ▼
                           ┌──────────────────────┐
                           │   Groq / LLaMA 3.3   │
                           │  Primary Synthesizer  │
                           │                      │
                           │  Human-readable      │
                           │  market brief         │
                           └──────────┬───────────┘
                                      │
                                      ▼
                     ┌────────────────────────────────┐
                     │        AUDITOR GATE             │
                     │                                │
                     │  Programmatic verification     │
                     │  against raw DuckDB results    │
                     │                                │
                     │  ✓ Numerical consistency       │
                     │  ✓ Grounding status             │
                     │  ✓ Cadastral consistency        │
                     │  ✓ Registry provenance          │
                     └────────────────┬───────────────┘
                                      │
                         ┌────────────┴────────────┐
                         │                         │
                  VERIFIED RESPONSE          REJECT / CIRCUIT
                         │                         │
                         ▼                         ▼
                Grounded market brief      is_grounded: false
                + verified DLD IDs         + discrepancy log
```

---

## Why AcreIQ?

Financial questions are particularly susceptible to hallucination.

A conventional RAG architecture can retrieve relevant documents but still allow an LLM to:

* Invent transaction values
* Calculate incorrect averages
* Conflate neighboring communities
* Treat colloquial names as legal entities
* Fabricate supporting records
* Produce plausible figures when no underlying transactions exist

AcreIQ separates **computation** from **language generation**.

| Responsibility             | System                         |
| -------------------------- | ------------------------------ |
| Entity resolution          | Deterministic cadastral lookup |
| Numerical computation      | DuckDB SQL                     |
| Transaction selection      | DLD source records             |
| Natural-language synthesis | Groq / LLaMA 3.3               |
| Numerical verification     | Deterministic Auditor Gate     |
| Provenance                 | DLD registry record IDs        |
| Invalid-query handling     | Fast-path circuit breaker      |

The LLM is therefore a **synthesis layer**, not the source of numerical truth.

---

# Core Capabilities

## 1. Deterministic In-Memory Analytics

AcreIQ loads the DLD transaction dataset into container memory and uses DuckDB for analytical execution.

Queries calculate metrics directly from transaction records, including:

* Median transaction price
* Mean transaction price
* Transaction volume
* Average price per square metre
* Underlying transaction records
* Registry identifiers

This avoids asking a generative model to perform financial arithmetic or infer statistics from retrieved text.

---

## 2. Cadastral Entity Resolution

Real-estate users rarely use legal cadastral terminology.

For example:

```text
User Query

    │
    ▼

"Show me the market in Downtown Dubai"

    │
    ▼

Cadastral Resolution

    │
    ▼

"burj khalifa"

    │
    ▼

DLD Transactions
```

AcreIQ resolves colloquial community names to the corresponding legal/master-community cadastral key before analytical execution.

This prevents geographically ambiguous natural-language queries from silently producing incorrect transaction sets.

---

## 3. Dual-Agent Synthesis + Auditor Gate

AcreIQ separates generation from verification.

### Primary Synthesizer

The Groq-hosted LLaMA 3.3 model receives the verified analytical slice and produces a human-readable market brief.

Its role is to:

* Interpret the computed statistics
* Explain market characteristics
* Produce readable financial summaries
* Surface relevant transaction evidence

### Deterministic Auditor Gate

The generated response is then checked programmatically against the authoritative DuckDB execution result.

The Auditor Gate verifies that numerical claims correspond to the underlying analytical slice.

Conceptually:

```text
DuckDB Ground Truth

        │
        ├── median = 2,635,000
        ├── mean   = 3,797,000
        └── avg/m² = 29,292.58

                  │
                  ▼

           Generated Response

                  │
                  ▼

             Auditor Gate

                  │
          ┌───────┴───────┐
          │               │
       MATCH           MISMATCH
          │               │
          ▼               ▼
     Grounded=True    Reject / Flag
```

A response is not considered grounded merely because the LLM produced a plausible answer.

---

## 4. Traceable DLD Provenance

AcreIQ surfaces exact DLD registry record identifiers associated with the analytical result.

Example:

```text
1-102-2023-13201
1-11-2023-7742
...
```

This creates a direct provenance path:

```text
Natural-language query
        ↓
Cadastral entity
        ↓
SQL aggregation
        ↓
Transaction slice
        ↓
DLD registry IDs
        ↓
Generated explanation
```

The system therefore provides an audit trail rather than an opaque generated number.

---

## 5. Adversarial Query Rejection

AcreIQ explicitly handles queries for entities that do not exist in the underlying DLD data.

For example:

```text
"Analyse Winterfell High Street"
```

does not result in the model attempting to fabricate a market.

Instead, the request is terminated through a fast-path circuit breaker:

```json
{
  "is_grounded": false,
  "discrepancies": [
    "NO_RECORDS_FOUND: NO_TOOL_CALL_MADE — no verified DLD transactions to ground against."
  ]
}
```

This is an intentional failure mode.

**No data is preferable to fabricated financial intelligence.**

---

# Production Benchmark

The following results are from evaluation runs against the production deployment using the **2023 DLD transaction dataset**.

| Scenario                   | Cadastral Resolution         | Analytical Output                                                                | Grounded                 |         Latency |
| -------------------------- | ---------------------------- | -------------------------------------------------------------------------------- | ------------------------ | --------------: |
| **Downtown Dubai**         | `burj khalifa`               | 500 records; Median **AED 2.635M**; Avg **AED 3.797M**; Avg **AED 29,292.58/m²** | `true` — 0 discrepancies |     ~13.6s cold |
| **Palm Jumeirah**          | `palm jumeirah`              | 500 records; Median **AED 3.425M**; Avg **AED 6.868M**; Avg **AED 27,956.18/m²** | `true`                   |      ~5.9s warm |
| **Winterfell High Street** | No verified cadastral entity | No transaction ground truth                                                      | `false`                  | ~1.8s fast-path |

### Observed Financial Signal

The Palm Jumeirah benchmark demonstrates why reporting multiple statistics matters.

```text
Median:     AED 3.425M
Mean:       AED 6.868M
```

The large difference between the median and mean reflects the influence of high-value transactions, consistent with the project's observed **luxury-villa skew**.

AcreIQ therefore exposes both statistics rather than collapsing the market into a single generated "average price."

### Verified Provenance

Successful queries return DLD registry IDs, including examples such as:

```text
1-102-2023-13201
1-11-2023-7742
...
```

---

# Production API

**Live Swagger / OpenAPI documentation:**

https://acreiq-api-zv7ueef3fq-ww.a.run.app/docs

Primary endpoint:

```text
POST /v1/chat
```

### Example: Grounded Query

```bash
curl -X POST \
  "https://acreiq-api-zv7ueef3fq-ww.a.run.app/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyse the real estate market in Downtown Dubai"
  }'
```

A successful response is grounded against the resolved DLD cadastral entity and includes deterministic analytical values and transaction provenance.

Representative analytical output:

```text
Cadastral: burj khalifa
Records analysed: 500
Median price: AED 2.635M
Average price: AED 3.797M
Average price/m²: AED 29,292.58
Grounded: true
Discrepancies: 0
```

### Example: Adversarial Probe

```bash
curl -X POST \
  "https://acreiq-api-zv7ueef3fq-ww.a.run.app/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyse property prices on Winterfell High Street"
  }'
```

Expected grounding behavior:

```json
{
  "is_grounded": false,
  "discrepancies": [
    "NO_RECORDS_FOUND: NO_TOOL_CALL_MADE — no verified DLD transactions to ground against."
  ]
}
```

The system rejects the query instead of generating unsupported financial figures.

---

# REST Request Lifecycle

A typical production request follows this sequence:

```text
POST /v1/chat
      │
      ▼
FastAPI validation
      │
      ▼
Cadastral entity resolution
      │
      ▼
DuckDB analytical query
      │
      ├── Transaction count
      ├── Median
      ├── Mean
      ├── Average price/m²
      └── DLD registry IDs
      │
      ▼
Groq / LLaMA 3.3 synthesis
      │
      ▼
Auditor Gate
      │
      ├── Numerical verification
      ├── Grounding verification
      └── Provenance verification
      │
      ▼
Verified API response
```

For unsupported entities:

```text
POST /v1/chat
      │
      ▼
Cadastral resolution
      │
      ▼
No verified records
      │
      ▼
Fast-Path Circuit Breaker
      │
      ▼
is_grounded: false
```

---

# Cloud Architecture

AcreIQ is deployed serverlessly on **Google Cloud Run** in:

```text
me-central1
```

The deployment is designed for low idle cost while retaining bounded production capacity.

```text
                         Google Cloud

                              │
                              ▼

                    ┌──────────────────┐
                    │    Cloud Run     │
                    │    me-central1   │
                    └────────┬─────────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
                  ▼                     ▼
           AcreIQ Container       Secret Manager
                  │                     │
                  │                GROQ_API_KEY
                  │
                  ▼
             DuckDB RAM
                  │
                  ▼
           DLD Transactions
```

### Runtime Configuration

| Configuration       |                       Value |
| ------------------- | --------------------------: |
| Region              |               `me-central1` |
| Minimum instances   |                         `0` |
| Maximum instances   |                         `5` |
| Request timeout     |                       `60s` |
| Container execution |                    Non-root |
| Secrets             | Google Cloud Secret Manager |
| LLM provider        |                        Groq |
| Analytical engine   |                      DuckDB |

### Scale-to-Zero

Cloud Run is configured with:

```text
--min-instances=0
```

This provides **$0 idle compute cost** when no instances are running.

The trade-off is cold-start latency: the first request can take approximately **10–13 seconds**, primarily due to loading the analytical dataset into container memory.

Warm requests typically execute in approximately **2–5 seconds**, depending on query and synthesis workload.

---

# Security

The production container follows several baseline security practices:

* Runs as a **non-root user**
* Uses multi-stage Docker builds
* Keeps API credentials outside the image
* Injects `GROQ_API_KEY` dynamically through **Google Cloud Secret Manager**
* Limits Cloud Run concurrency through bounded instance configuration
* Uses strict Pydantic request/response schemas

Secrets should never be committed to the repository or baked into Docker layers.

---

# Data Architecture

AcreIQ operates over approximately **600 MB of raw Dubai Land Department transaction data covering the 2023 calendar year**.

The dataset contains transaction-level records including property characteristics, cadastral information, transaction procedures, transaction values, and related real-estate attributes.

```text
DLD Open Transaction Data
        │
        ▼
2023 Transaction Dataset (~600 MB)
        │
        ▼
Container Memory
        │
        ▼
DuckDB
        │
        ├── Entity filtering
        ├── Aggregation
        ├── Statistical computation
        └── Provenance extraction
```

DuckDB provides an embedded analytical database without requiring a separate database service for the transactional analytical workload.

This keeps the architecture lightweight while allowing SQL-based analytical operations over the complete in-memory dataset.

---

# Data Scope & Limitations

The current AcreIQ deployment uses a **Dubai Land Department open transaction dataset covering the 2023 calendar year**.

Accordingly:

* All analytical results are based on **2023 transactions only**.
* Reported transaction volumes represent records available in the 2023 dataset, not total historical DLD activity.
* Median, mean, and price/m² statistics describe the **2023 observed transaction sample**.
* The current system does not provide year-over-year market trends or a continuous historical time series.
* Results should not be interpreted as representing current **2026** market conditions.
* Queries concerning post-2023 conditions are outside the temporal coverage of the underlying dataset.

The dataset is sourced from **Dubai Land Department open transaction data** and is published under the [Dubai Pulse Open Data Licence](https://www.dubaipulse.gov.ae/docs/DDE%20_%20DRAFT_Open_Data_Licence_LONG_Form_English_3.pdf).

### Dataset Coverage

| Attribute         | Coverage                        |
| ----------------- | ------------------------------- |
| Source            | Dubai Land Department           |
| Dataset type      | Real-estate transaction records |
| Geographic scope  | Dubai, UAE                      |
| Temporal scope    | **2023 calendar year**          |
| Raw dataset size  | ~600 MB                         |
| Analytical engine | DuckDB                          |
| Storage model     | In-memory                       |

---

# Repository Structure

```text
.
├── src/
│   ├── agents.py              # Dual-agent synthesis & grounding logic
│   ├── api.py                 # FastAPI REST endpoints
│   ├── config.py              # Environment settings
│   ├── db.py                  # DuckDB connection & query execution
│   ├── mcp_server.py          # Model Context Protocol / tool server
│   ├── schemas.py             # Strict Pydantic I/O models
│   └── tools.py               # Cadastral lookup & data extraction
│
├── tests/
│   ├── eval_runner.py         # Evaluation test runner
│   └── golden_eval_set.json   # Test fixtures & edge cases
│
├── Dockerfile                 # Multi-stage non-root container
├── cloudbuild.yaml            # GCP Cloud Build CI/CD specification
└── requirements.txt
```

---

# Local Development

## Prerequisites

* Python 3.11+
* Docker
* Access to the **2023 DLD transaction dataset**
* Groq API key for LLM synthesis

---

## Option 1 — Python Virtual Environment

Clone the repository:

```bash
git clone <repository-url>
cd AcreIQ
```

Create and activate a virtual environment:

### macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### Windows

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment variables:

```bash
export GROQ_API_KEY="your-api-key"
```

Start the API:

```bash
uvicorn src.api:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

---

## Option 2 — Docker

Build the production image:

```bash
docker build -t acreiq .
```

Run the container:

```bash
docker run \
  -p 8000:8000 \
  -e GROQ_API_KEY="your-api-key" \
  acreiq
```

Access the API:

```text
http://localhost:8000/docs
```

The Dockerfile uses a multi-stage build and executes the application as a non-root user.

---

# Evaluation

The repository contains a dedicated evaluation harness:

```text
tests/
├── eval_runner.py
└── golden_eval_set.json
```

The evaluation set covers both normal analytical queries and adversarial conditions.

Key evaluation dimensions include:

1. Cadastral resolution
2. Transaction retrieval
3. Numerical correctness
4. Grounding status
5. Provenance extraction
6. Adversarial rejection
7. Fast-path behavior

The important distinction is that **LLM fluency is not treated as evaluation success**.

A successful test requires the generated financial intelligence to remain consistent with the deterministic analytical ground truth.

---

# Design Principles

### 1. Compute Before You Generate

Financial statistics are calculated by DuckDB rather than inferred by the language model.

### 2. Resolve Entities Before Querying

Natural-language geography is mapped to legal cadastral identifiers before transaction aggregation.

### 3. Verify After Generation

The generated response passes through a deterministic Auditor Gate before being considered grounded.

### 4. Preserve Provenance

Analytical claims retain references to underlying DLD registry records.

### 5. Fail Closed

When there is no verified source data, AcreIQ does not manufacture an answer.

### 6. Respect Data Scope

Analytical claims are bounded by the temporal and geographic coverage of the underlying dataset.

### 7. Optimize for Production Constraints

The architecture deliberately balances:

* Analytical correctness
* LLM flexibility
* Cold-start latency
* Infrastructure cost
* Container security
* Operational simplicity

---

# Technology Stack

| Layer               | Technology                                    |
| ------------------- | --------------------------------------------- |
| API                 | FastAPI                                       |
| Language            | Python 3.11+                                  |
| Analytical Database | DuckDB                                        |
| LLM                 | Groq / LLaMA 3.3                              |
| Data Validation     | Pydantic                                      |
| Tool Interface      | MCP                                           |
| Containerization    | Docker                                        |
| Runtime             | Google Cloud Run                              |
| CI/CD               | Google Cloud Build                            |
| Secrets             | Google Cloud Secret Manager                   |
| Source Data         | Dubai Land Department — **2023 transactions** |

---

# Production Characteristics

```text
                AcreIQ Reliability Model

       ┌─────────────────────────────────────┐
       │     2023 DLD Transaction Ground Truth │
       └──────────────────┬──────────────────┘
                          │
                          ▼
                   Deterministic SQL
                          │
                          ▼
                   Analytical Results
                          │
                          ▼
                    LLM Synthesis
                          │
                          ▼
                    Auditor Gate
                          │
             ┌────────────┴────────────┐
             │                         │
           PASS                       FAIL
             │                         │
             ▼                         ▼
      Verified response         Explicit rejection
      + provenance              + discrepancy log
```

The architecture intentionally places the language model **between deterministic computation and deterministic verification**.

That separation is the core mechanism AcreIQ uses to reduce financial hallucination while retaining the usability of natural-language AI interfaces.

---

# Live Deployment

**Swagger / OpenAPI:**

https://acreiq-api-zv7ueef3fq-ww.a.run.app/docs

**Primary API route:**

```text
POST /v1/chat
```

**Deployment region:**

```text
Google Cloud — me-central1
```

---

## Project Status

AcreIQ is deployed as a production serverless REST API with automated Cloud Build deployment, deterministic DuckDB analytics, LLM synthesis, provenance extraction, and an Auditor Gate for numerical grounding.

The current benchmark demonstrates the intended operating model:

```text
Valid 2023 financial query
        → deterministic analysis
        → LLM explanation
        → programmatic verification
        → grounded response

Unsupported query
        → no verified records
        → circuit breaker
        → grounded: false
```

**The system treats financial ground truth as an invariant, not a generation target.**
