# Multi-stage build for optimal image size
FROM python:3.12-slim-bookworm AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
# --no-install-project: we only want dependencies, app code is copied later or mounted
# --no-dev: production only
RUN uv sync --frozen --no-install-project --no-dev || uv sync --no-install-project --no-dev

# Production stage
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY apps/ ./apps/
COPY bin/ ./bin/
COPY webapp/ ./webapp/
COPY run.py ./
COPY docker/entrypoint.sh /entrypoint.sh

# Fix BOM, line endings, and make scripts executable
RUN sed -i '1s/^\xEF\xBB\xBF//' /entrypoint.sh && \
    sed -i 's/\r$//' /entrypoint.sh && \
    chmod +x /entrypoint.sh bin/get_webhook_url.py

# Change ownership to app user
RUN chown -R app:app /app /entrypoint.sh
USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys,urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=5).read()"

ENV DOCKER_CONTAINER=1

ENTRYPOINT ["/entrypoint.sh"]
