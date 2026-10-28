"""In-process broker for local development and tests."""

import asyncio
from collections import defaultdict

from base.services.broker import AbstractBroker, Handler
from base.services.common.meta import SingletonABC
from base.services.logging.console import ConsoleLoggerService
from contracts.events import Event


class InMemoryBroker(AbstractBroker, metaclass=SingletonABC):
    def __init__(self) -> None:
        self._handlers: dict[str, list[tuple[str, Handler]]] = defaultdict(list)
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None
        self._seen: set[str] = set()
        self._logger = ConsoleLoggerService()

    async def _apublish(self, event: Event) -> None:
        await self._queue.put(event)

    async def _asubscribe(self, topic: str, group: str, handler: Handler) -> None:
        self._handlers[topic].append((group, handler))

    async def _astart(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._consume())

    async def _astop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _consume(self) -> None:
        while True:
            event = await self._queue.get()
            for group, handler in self._handlers.get(event.topic, []):
                key = f"{group}:{event.meta.event_id}"
                if key in self._seen:
                    continue
                self._seen.add(key)
                try:
                    await handler(event)
                except Exception:
                    self._logger.exception(
                        f"Handler failed for {event.topic} in group {group}"
                    )
            self._queue.task_done()

    async def adrain(self) -> None:
        """Wait until every queued event has been handled. For tests."""
        await self._queue.join()
