"""The worker consumes what other services publish."""

from uuid import uuid4

from contracts.events import Event
from contracts.v1 import chat, identity


class TestConsumption:
    async def test_it_handles_a_user_registered_event(self, broker):
        from ingestion_worker import handlers, worker

        await worker.arun(broker)
        before = handlers.processed_count()
        await broker.apublish(
            Event.of(
                identity.USER_REGISTERED,
                {"user_id": str(uuid4()), "email": "new@example.com"},
                producer="identity",
                correlation_id=uuid4(),
            )
        )
        await broker.adrain()
        assert handlers.processed_count() == before + 1
        await broker.astop()

    async def test_it_handles_a_conversation_created_event(self, broker):
        from ingestion_worker import handlers, worker

        await worker.arun(broker)
        before = handlers.processed_count()
        await broker.apublish(
            Event.of(
                chat.CONVERSATION_CREATED,
                {"conversation_id": str(uuid4()), "user_id": str(uuid4())},
                producer="chat_api",
                correlation_id=uuid4(),
            )
        )
        await broker.adrain()
        assert handlers.processed_count() == before + 1
        await broker.astop()

    async def test_a_redelivered_event_is_handled_once(self, broker):
        from ingestion_worker import handlers, worker

        await worker.arun(broker)
        event = Event.of(
            identity.USER_REGISTERED,
            {"user_id": str(uuid4()), "email": "dupe@example.com"},
            producer="identity",
        )
        before = handlers.processed_count()
        await broker.apublish(event)
        await broker.adrain()
        await broker.apublish(event)
        await broker.adrain()
        assert handlers.processed_count() == before + 1
        await broker.astop()
