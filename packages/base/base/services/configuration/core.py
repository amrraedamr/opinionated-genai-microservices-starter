from pydantic_settings import BaseSettings, SettingsConfigDict

from base.services.common.meta import SingletonSettings


class CoreSettings(BaseSettings, metaclass=SingletonSettings):
    """Settings common to every service."""

    model_config = SettingsConfigDict(
        env_file=(".env.shared", ".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    service_name: str
    """Namespace key for cache keys, pub/sub channels, queues, logs and traces."""

    environment: str = "local"
    log_level: str = "INFO"
