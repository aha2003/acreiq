# ----------------------------------------------------------------------------
# AcreIQ - production Dockerfile
# Multi-stage build: build deps in a throwaway stage, ship a lean runtime.
# ----------------------------------------------------------------------------

# ---- Stage 1: builder --------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps needed only to build wheels (e.g. for duckdb / bigquery deps),
# not needed at runtime -- kept out of the final image.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 --retries 5 --prefix=/install -r requirements.txt

# ---- Stage 2: runtime ---------------------------------------------------------
FROM python:3.11-slim AS runtime

# Cloud Run injects PORT at runtime; the default here is only for local
# `docker run`.
ENV PORT=8080 \
    WORKERS=2 \
    APP_ENV=cloud \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy only the installed packages from the builder stage -- no compilers,
# no build headers, no pip cache end up in the final image.
COPY --from=builder /install /usr/local

COPY src/ ./src/

# Only needed for local/dev fallback mode (APP_ENV=local). In production
# (APP_ENV=cloud) the app talks to BigQuery via the service account attached
# to the Cloud Run revision -- no key file is baked into the image, and the
# CSV below is not shipped either. See db.py: DatabaseEngine only touches
# CSV_PATH when APP_ENV=local. Uncomment only if you intentionally want a
# CSV-backed image (e.g. a demo build).
COPY data/ ./data/

# Run as a non-privileged user -- never run the container as root.
RUN groupadd -r acreiq && useradd -r -g acreiq acreiq \
    && chown -R acreiq:acreiq /app
USER acreiq

EXPOSE 8080

# Cloud Run performs its own HTTP health check against /healthz; this
# HEALTHCHECK instruction is for non-Cloud-Run runtimes (local docker
# compose, other orchestrators) that respect it.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",8080)}/healthz')" || exit 1

# JSON-array form wrapping sh -c: this satisfies Docker's signal-handling
# recommendation (exec replaces the shell as PID 1, so SIGTERM forwards
# correctly for graceful shutdown) while still letting $PORT / $WORKERS
# expand at container start -- Cloud Run sets PORT dynamically per
# revision, so it cannot be baked in at build time.
CMD ["sh", "-c", "exec uvicorn src.api:app --host 0.0.0.0 --port ${PORT} --workers ${WORKERS}"]