"""The broker contract, exercised against the in-memory implementation."""

import asyncio
from uuid import uuid4

from contracts.events import Event
from contracts.v1 import identity


def make_event(correlation_id=None) -> Event:
    return Event.of(
        identity.USER_REGISTERED,
        {"user_id": str(uuid4()), "email": "a@b.com"},
        producer="identity",
        correlation_id=correlation_id,
    )


class TestPublishSubscribe:
    async def test_a_subscriber_receives_a_published_event(self, broker):
        seen = []

        async def handler(event: Event) -> None:
            seen.append(event)

        await broker.asubscribe(identity.USER_REGISTERED, "g", handler)
        await broker.astart()
        await broker.apublish(make_event())
        await broker.adrain()
        await asyncio.sleep(0)

        assert len(seen) == 1
        assert seen[0].topic == identity.USER_REGISTERED
        await broker.astop()

    async def test_an_unrelated_topic_is_not_delivered(self, broker):
        seen = []

        async def handler(event: Event) -> None:
            seen.append(event)

        await broker.asubscribe("other.topic", "g", handler)
        await broker.astart()
        await broker.apublish(make_event())
        await broker.adrain()

        assert seen == []
        await broker.astop()

    async def test_a_duplicate_event_id_is_delivered_once_per_group(self, broker):
        seen = []

        async def handler(event: Event) -> None:
            seen.append(event)

        await broker.asubscribe(identity.USER_REGISTERED, "g", handler)
        await broker.astart()
        event = make_event()
        await broker.apublish(event)
        await broker.apublish(event)
        await broker.adrain()

        assert len(seen) == 1
        await broker.astop()

    async def test_a_failing_handler_does_not_stop_the_consumer(self, broker):
        seen = []

        async def failing(event: Event) -> None:
            raise RuntimeError("boom")

        async def working(event: Event) -> None:
            seen.append(event)

        await broker.asubscribe(identity.USER_REGISTERED, "a", failing)
        await broker.asubscribe(identity.USER_REGISTERED, "b", working)
        await broker.astart()
        await broker.apublish(make_event())
        await broker.adrain()

        assert len(seen) == 1
        await broker.astop()

    async def test_correlation_id_survives_the_round_trip(self, broker):
        seen = []

        async def handler(event: Event) -> None:
            seen.append(event.meta.correlation_id)

        correlation_id = uuid4()
        await broker.asubscribe(identity.USER_REGISTERED, "g", handler)
        await broker.astart()
        await broker.apublish(make_event(correlation_id))
        await broker.adrain()

        assert seen == [correlation_id]
        await broker.astop()
