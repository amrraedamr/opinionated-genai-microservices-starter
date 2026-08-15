#!/bin/sh

set -e

if [ -n "$RUN_MIGRATIONS" ]; then
    echo "Running migrations..."
    .venv/bin/alembic upgrade head
fi

export API_HOST=0.0.0.0
export API_PORT=8000

echo "Starting the Opinionated GenAI Starter API"
exec .venv/bin/api
