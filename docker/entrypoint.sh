#!/usr/bin/env sh
set -e

if [ "${USE_PINGGY:-false}" = "true" ]; then
    python bin/get_webhook_url.py
fi

exec python -m uvicorn apps.bot.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8080}" \
    --no-access-log \
    --log-level warning
