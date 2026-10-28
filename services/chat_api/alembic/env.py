import asyncio
from logging.config import fileConfig
from typing import Any

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy_utils.types.uuid import UUIDType

# Import each table so it registers on ChatBase.metadata. Add a line per table.
import chat_api.models.orm.chat_history_message  # noqa: F401, E402
import chat_api.models.orm.conversation  # noqa: F401, E402
import chat_api.models.orm.prompt  # noqa: F401, E402
from alembic import context
from base.clients.sql.client import SQLClient
from base.models.definitions.database import SQLBackend
from base.services.configuration import configure
from chat_api.models.orm import ChatBase
from chat_api.settings import settings

configure(settings)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = ChatBase.metadata


def _get_client() -> SQLClient:
    backend = SQLBackend(settings.sql_backend)
    return SQLClient(backend, settings, _key=backend.value)


def _get_async_url() -> str:
    client = _get_client()
    return client._get_database_url(client._backend.async_driver)


def _get_sync_url() -> str:
    client = _get_client()
    return client._get_database_url(client._backend.sync_driver)


def _compare_type(
    _ctx: Any,
    _inspected_column: Any,
    _metadata_column: Any,
    _inspected_type: Any,
    metadata_type: Any,
) -> bool | None:
    """Skip false-positive type diffs for custom types like UUIDType on SQLite."""
    if isinstance(metadata_type, UUIDType):
        return False
    return None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection needed)."""
    context.configure(
        url=_get_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        compare_type=_compare_type,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
        compare_type=_compare_type,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations."""
    connectable = create_async_engine(
        _get_async_url(),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
