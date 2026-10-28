"""Composition root for ingestion_worker.

No HTTP surface: this service consumes from the broker and nothing else.
"""

import asyncio

from base.services.configuration import configure
from ingestion_worker.settings import settings

configure(settings)

from base.services.broker import AbstractBroker  # noqa: E402
from base.services.logging.console import ConsoleLoggerService  # noqa: E402
from contracts.v1 import chat, identity  # noqa: E402
from ingestion_worker import handlers  # noqa: E402

logger = ConsoleLoggerService()


def build_broker() -> AbstractBroker:
    if settings.broker == "redis":
        from base.services.broker.redis_streams import RedisStreamsBroker

        return RedisStreamsBroker()
    from base.services.broker.memory import InMemoryBroker

    return InMemoryBroker()


async def arun(broker: AbstractBroker | None = None) -> AbstractBroker:
    """Subscribe every handler and begin consuming."""
    broker = broker or build_broker()
    group = settings.consumer_group
    await broker.asubscribe(identity.USER_REGISTERED, group, handlers.ahandle_user_registered)
    await broker.asubscribe(chat.CONVERSATION_CREATED, group, handlers.ahandle_conversation_created)
    await broker.astart()
    logger.info(f"{settings.service_name} consuming as group {group}")
    return broker


def start() -> None:
    async def _main() -> None:
        broker = await arun()
        try:
            await asyncio.Event().wait()
        finally:
            await broker.astop()

    asyncio.run(_main())
