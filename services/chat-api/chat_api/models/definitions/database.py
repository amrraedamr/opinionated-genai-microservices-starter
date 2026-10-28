from enum import StrEnum


class DatabaseTable(StrEnum):
    """Tables owned by chat-api.

    Table names are part of a service's own schema, not shared infrastructure,
    so this enum lives with the service rather than in `base`.
    """

    USER = "user"
    USER_IDENTITY = "user_identity"
    PROMPT = "prompt"
    ACTIVE_PROMPT = "active_prompt"
    CONVERSATION = "conversation"
    CHAT_HISTORY_MESSAGE = "chat_history_message"
