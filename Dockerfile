# syntax=docker/dockerfile:1
FROM python:3.11-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend
WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip==25.3 && \
    python -m pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY backend ./backend
COPY policy ./policy
COPY tests ./tests
COPY pyproject.toml ./
RUN PYTHONPATH=/install/lib/python3.11/site-packages:/app/backend python -m pytest -q

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    HOST=0.0.0.0 \
    PORT=8000 \
    AGENTGUARD_AUDIT_PATH=/app/audit/audit.jsonl \
    AGENTGUARD_POLICY_PATH=/app/policy/default.yaml \
    AGENTGUARD_MAX_BODY_SIZE=1048576
WORKDIR /app

COPY --from=build /install /usr/local
COPY backend ./backend
COPY policy ./policy
RUN useradd --create-home --uid 10001 agentguard && \
    mkdir -p /app/audit && \
    chown -R agentguard:agentguard /app
USER agentguard

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT', '8000') + '/health', timeout=3).read()"
CMD ["sh", "-c", "exec python -m uvicorn agentguard.api:app --host \"$HOST\" --port \"$PORT\""]
