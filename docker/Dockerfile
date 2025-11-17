# Multi-stage build for optimal image size
FROM python:3.12-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry poetry-plugin-export && \
    poetry export -f requirements.txt --without-hashes --output requirements.txt && \
    pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

# Production stage
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Copy venv with dependencies
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY apps/ ./apps/
COPY bin/ ./bin/
COPY webapp/ ./webapp/
COPY run.py ./
COPY docker/entrypoint.sh /entrypoint.sh

# Make scripts executable
RUN chmod +x /entrypoint.sh bin/get_webhook_url.py

# Change ownership to app user
RUN chown -R app:app /app
USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys,urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=5).read()"

ENV DOCKER_CONTAINER=1

ENTRYPOINT ["/entrypoint.sh"]
