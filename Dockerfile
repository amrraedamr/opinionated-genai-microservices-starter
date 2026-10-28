FROM python:3.14-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.18 /uv /uvx /bin/

ENV UV_PYTHON_DOWNLOADS=0 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY packages/base/pyproject.toml packages/base/pyproject.toml

RUN uv sync \
    --locked \
    --no-dev \
    --no-install-workspace \
    --no-editable

COPY . .

RUN uv sync \
    --locked \
    --no-dev \
    --no-editable


FROM python:3.14-slim-bookworm AS runner

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup --no-create-home appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appgroup /app /app

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD ["python", "health_check.py"]

ENTRYPOINT ["/bin/sh", "run.sh"]
