# Multi-stage build for optimal image size
FROM python:3.12-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy dependency files (poetry.lock is optional - speeds up if present)
COPY pyproject.toml poetry.lock* ./

# Install poetry with export plugin
RUN pip install --no-cache-dir poetry poetry-plugin-export

# Configure poetry to use existing venv and not create new one
ENV POETRY_VENV_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Update lock file if needed (poetry lock is smart - won't recreate if up-to-date)
RUN poetry lock

# Install dependencies using export + pip (more reliable with package-mode=false)
# Export to requirements.txt and install - this works reliably with package-mode=false
RUN poetry export --without-hashes --only main -o requirements.txt && \
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
