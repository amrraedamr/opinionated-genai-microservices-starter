#!/bin/sh

set -e

SERVICE="${SERVICE:-chat-api}"

if [ -n "$RUN_MIGRATIONS" ]; then
    echo "Running migrations for $SERVICE..."
    (cd "services/$SERVICE" && /app/.venv/bin/alembic upgrade head)
fi

export API_HOST=0.0.0.0
export API_PORT=8000

echo "Starting $SERVICE"
exec .venv/bin/serve
