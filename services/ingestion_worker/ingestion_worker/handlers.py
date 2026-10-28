"""What this worker does with the events it consumes."""

from base.services.logging.console import ConsoleLoggerService
from contracts.events import Event

logger = ConsoleLoggerService()

# At-least-once delivery means a handler will see duplicates.
_processed: set[str] = set()


async def ahandle_user_registered(event: Event) -> None:
    """Project a newly registered user into this service's own read model."""
    key = str(event.meta.event_id)
    if key in _processed:
        return
    _processed.add(key)
    logger.info(
        f"user registered: {event.payload.get('email')} "
        f"(correlation={event.meta.correlation_id})"
    )


async def ahandle_conversation_created(event: Event) -> None:
    key = str(event.meta.event_id)
    if key in _processed:
        return
    _processed.add(key)
    logger.info(
        f"conversation created: {event.payload.get('conversation_id')} "
        f"(correlation={event.meta.correlation_id})"
    )


def processed_count() -> int:
    return len(_processed)
