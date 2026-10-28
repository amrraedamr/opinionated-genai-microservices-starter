from enum import StrEnum


class DatabaseTable(StrEnum):
    """Tables owned by chat_api."""

    USER = "user"
    USER_IDENTITY = "user_identity"
    PROMPT = "prompt"
    ACTIVE_PROMPT = "active_prompt"
    CONVERSATION = "conversation"
    CHAT_HISTORY_MESSAGE = "chat_history_message"
