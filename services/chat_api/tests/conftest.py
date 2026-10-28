"""Shared fixtures for chat_api tests."""

from __future__ import annotations

import os
import pathlib
import subprocess
import tempfile
from collections.abc import Iterator

import pytest

SERVICE_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _write_keypair(directory: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    private = directory / "private.pem"
    public = directory / "public.pem"
    subprocess.run(
        ["openssl", "genrsa", "-out", str(private), "2048"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["openssl", "rsa", "-in", str(private), "-pubout", "-out", str(public)],
        check=True,
        capture_output=True,
    )
    return private, public


@pytest.fixture(scope="session")
def app_environment() -> Iterator[None]:
    """A migrated SQLite database and a signing keypair, for the session."""
    with tempfile.TemporaryDirectory() as tmp:
        directory = pathlib.Path(tmp)
        private, public = _write_keypair(directory)
        database = directory / "test.db"

        os.environ.update(
            {
                "SERVICE_NAME": "chat_api",
                "ENVIRONMENT": "local",
                "SQL_BACKEND": "sqlite",
                "SQLITE_DB_PATH": str(database),
                "AUTH_PRIVATE_KEY_PATH": str(private),
                "AUTH_PUBLIC_KEY_PATH": str(public),
                "OPENAI_LLM_API_KEY": "sk-test",
                "OPENAI_API_KEY": "sk-test",
            }
        )

        subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=SERVICE_ROOT,
            check=True,
            capture_output=True,
            env=os.environ.copy(),
        )
        yield


@pytest.fixture(scope="session")
def client(app_environment: None):
    from fastapi.testclient import TestClient

    from chat_api.app import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def api_prefix() -> str:
    from chat_api.settings import settings

    return settings.api_prefix
