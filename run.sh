#!/bin/sh

set -e

# Which service this image runs. One parameterised entrypoint for every
# service; `docker/service.Dockerfile` makes this a build arg in phase 4.
SERVICE="${SERVICE:-chat_api}"
VENV_BIN="${VENV_BIN:-/app/.venv/bin}"

cd "services/$SERVICE"

if [ -n "$RUN_MIGRATIONS" ]; then
    echo "Running migrations for $SERVICE..."
    "$VENV_BIN/alembic" upgrade head
fi

export API_HOST=0.0.0.0
export API_PORT=8000

# Run from the service directory so its own `.env` (and the shared
# `../../.env.shared`) resolve the way pydantic-settings expects.
echo "Starting $SERVICE"
exec "$VENV_BIN/serve"
