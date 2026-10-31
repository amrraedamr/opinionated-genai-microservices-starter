"""Test helpers for standing a service up against a throwaway database."""

import os
import pathlib
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager


def write_keypair(directory: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """Generate an RSA keypair for signing and verifying tokens in tests."""
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


@contextmanager
def service_environment(
    service_name: str,
    service_root: pathlib.Path,
    extra_environment: dict[str, str] | None = None,
) -> Iterator[pathlib.Path]:
    """Point a service at a migrated throwaway SQLite database and a fresh keypair.

    Yields the private key path so a test can sign tokens the service accepts.
    The environment is set process-wide, so one service per interpreter.
    """
    with tempfile.TemporaryDirectory() as tmp:
        directory = pathlib.Path(tmp)
        private, public = write_keypair(directory)

        os.environ.update(
            {
                "SERVICE_NAME": service_name,
                "ENVIRONMENT": "local",
                "SQL_BACKEND": "sqlite",
                "SQLITE_DB_PATH": str(directory / "test.db"),
                "AUTH_PRIVATE_KEY_PATH": str(private),
                "AUTH_PUBLIC_KEY_PATH": str(public),
                **(extra_environment or {}),
            }
        )

        subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=service_root,
            check=True,
            capture_output=True,
            env=os.environ.copy(),
        )
        yield private
