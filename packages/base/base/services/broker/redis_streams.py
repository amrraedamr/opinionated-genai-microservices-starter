"""Redis Streams broker.

Consumer groups give at-least-once delivery with acknowledgement, so a handler
that raises leaves the message pending for redelivery rather than losing it.
"""

import asyncio
import json

from base.services.broker import AbstractBroker, Handler
from base.services.cache.protocol import SupportsCacheConfig
from base.services.common.meta import SingletonABC
from base.services.configuration import get_settings
from base.services.logging.console import ConsoleLoggerService
from base.tools.errors import MissingExtraError
from contracts.events import Event

try:
    from redis.asyncio import Redis
    from redis.exceptions import ResponseError
except ModuleNotFoundError as exc:  # pragma: no cover
    raise MissingExtraError("redis", "redis", feature="RedisStreamsBroker") from exc


class RedisStreamsBroker(AbstractBroker, metaclass=SingletonABC):
    def __init__(self, config: SupportsCacheConfig | None = None) -> None:
        self._config = config or get_settings()
        self._redis: Redis | None = None
        self._subscriptions: list[tuple[str, str, Handler]] = []
        self._tasks: list[asyncio.Task[None]] = []
        self._logger = ConsoleLoggerService()
        self._consumer = f"{get_settings().service_name}-{id(self)}"

    @property
    def client(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(
                getattr(self._config, "redis_url", "redis://localhost:6379/0"),
                decode_responses=True,
            )
        return self._redis

    async def _apublish(self, event: Event) -> None:
        await self.client.xadd(event.topic, {"event": event.model_dump_json()})

    async def _asubscribe(self, topic: str, group: str, handler: Handler) -> None:
        self._subscriptions.append((topic, group, handler))

    async def _astart(self) -> None:
        for topic, group, handler in self._subscriptions:
            try:
                await self.client.xgroup_create(topic, group, id="0", mkstream=True)
            except ResponseError as exc:
                if "BUSYGROUP" not in str(exc):
                    raise
            self._tasks.append(asyncio.create_task(self._consume(topic, group, handler)))

    async def _astop(self) -> None:
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

    async def _consume(self, topic: str, group: str, handler: Handler) -> None:
        while True:
            entries = await self.client.xreadgroup(
                group, self._consumer, {topic: ">"}, count=16, block=2000
            )
            for _stream, messages in entries or []:
                for message_id, fields in messages:
                    try:
                        event = Event.model_validate(json.loads(fields["event"]))
                        await handler(event)
                        await self.client.xack(topic, group, message_id)
                    except Exception:
                        # Left unacknowledged so it is redelivered.
                        self._logger.exception(
                            f"Handler failed for {topic} in group {group}"
                        )
