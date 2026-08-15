FROM python:3.14-slim-bookworm AS builder

RUN pip install --no-cache-dir poetry==2.1.3

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root --no-directory --without dev --no-interaction --no-ansi

COPY . .

RUN poetry install --without dev --no-interaction --no-ansi


FROM python:3.14-slim-bookworm AS runner

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup --no-create-home appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appgroup /app/.venv ./.venv
COPY --from=builder --chown=appuser:appgroup /app .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD .venv/bin/python health_check.py

ENTRYPOINT ["/bin/sh", "run.sh"]
