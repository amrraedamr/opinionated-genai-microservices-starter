"""chat-api's settings: `CoreSettings` plus only the mixins it actually uses.

Inheriting one god-class would give this service OAuth-for-every-provider, Mongo,
Cosmos, Qdrant and Azure Search fields it never reads — and would make it
impossible to *require* a field here without requiring it everywhere.
"""

from pydantic_settings import SettingsConfigDict

from base.services.configuration.core import CoreSettings
from base.services.configuration.mixins import (
    IdpResourceServerMixin,
    LLMSettingsMixin,
    OAuthSettingsMixin,
    PostgresSettingsMixin,
    PromptSettingsMixin,
    RedisSettingsMixin,
    ServerSettingsMixin,
    SQLSettingsMixin,
    TokenIssuingMixin,
)


class ChatApiSettings(
    CoreSettings,
    ServerSettingsMixin,
    SQLSettingsMixin,
    PostgresSettingsMixin,
    RedisSettingsMixin,
    LLMSettingsMixin,
    # chat-api still issues tokens and owns users. Phase 5 moves that to the
    # identity service, at which point this drops to TokenVerificationMixin.
    TokenIssuingMixin,
    OAuthSettingsMixin,
    IdpResourceServerMixin,
    PromptSettingsMixin,
):
    model_config = SettingsConfigDict(
        # Later files win; real process environment beats every file.
        env_file=("../../.env.shared", ".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    service_name: str = "chat-api"
    api_prefix: str = "/api/7r"

    cors_origins: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = ChatApiSettings()


if __name__ == "__main__":  # pragma: no cover
    # `uv run --package chat-api python -m chat_api.settings` — fail loudly in
    # CI or a container preStart probe rather than on the first request.
    print(f"chat-api settings OK (service_name={settings.service_name!r}, environment={settings.environment!r})")
