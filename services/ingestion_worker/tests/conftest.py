"""Fixtures for ingestion_worker tests."""

import os

import pytest

from base.testing import broker  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def worker_environment() -> None:
    os.environ.update({"SERVICE_NAME": "ingestion_worker", "ENVIRONMENT": "local"})
