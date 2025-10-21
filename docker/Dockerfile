# Multi-stage build for optimal image size
FROM python:3.12-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi

# Production stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY apps/ ./apps/
COPY bin/ ./bin/
COPY webapp/ ./webapp/
COPY run.py ./

# Make scripts executable
RUN chmod +x bin/get_webhook_url.py

# Create necessary directories
RUN mkdir -p data logs

# Change ownership to app user
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Set environment variable to indicate Docker mode
ENV DOCKER_CONTAINER=1

# Run application
CMD ["sh", "-c", "if [ \"$USE_CLOUDFLARED\" = \"true\" ]; then python bin/get_webhook_url.py && python -m uvicorn apps.bot.main:app --host 0.0.0.0 --port 8080 --no-access-log --log-level warning; else python -m uvicorn apps.bot.main:app --host 0.0.0.0 --port 8080 --no-access-log --log-level warning; fi"]
