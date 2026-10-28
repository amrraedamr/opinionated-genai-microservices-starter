"""Broker contract for asynchronous messaging between services."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import final

from contracts.events import Event

Handler = Callable[[Event], Awaitable[None]]


class AbstractBroker(ABC):
    """Publish and subscribe, independent of the transport underneath.

    Delivery is at-least-once, so a handler must be idempotent and dedupe on
    `event.meta.event_id`. Topics are namespaced per service by the caller.
    """

    @abstractmethod
    async def _apublish(self, event: Event) -> None:
        """Publish one event to its topic."""

    @final
    async def apublish(self, event: Event) -> None:
        await self._apublish(event)

    @abstractmethod
    async def _asubscribe(self, topic: str, group: str, handler: Handler) -> None:
        """Register a handler for a topic within a consumer group."""

    @final
    async def asubscribe(self, topic: str, group: str, handler: Handler) -> None:
        await self._asubscribe(topic, group, handler)

    @abstractmethod
    async def _astart(self) -> None:
        """Begin consuming for every registered subscription."""

    @final
    async def astart(self) -> None:
        await self._astart()

    @abstractmethod
    async def _astop(self) -> None:
        """Stop consuming and release the transport."""

    @final
    async def astop(self) -> None:
        await self._astop()
