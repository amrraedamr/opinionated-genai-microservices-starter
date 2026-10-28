"""ingestion_worker settings: `CoreSettings` plus the mixins this service uses."""

from pydantic_settings import SettingsConfigDict

from base.services.configuration.core import CoreSettings
from base.services.configuration.mixins import RedisSettingsMixin


class IngestionWorkerSettings(
    CoreSettings,
    RedisSettingsMixin,
):
    model_config = SettingsConfigDict(
        env_file=("../../.env.shared", ".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    service_name: str = "ingestion_worker"
    broker: str = "memory"
    consumer_group: str = "ingestion_worker"


settings = IngestionWorkerSettings()


if __name__ == "__main__":  # pragma: no cover
    # Validation entrypoint for CI and container preStart probes.
    print(f"ingestion_worker settings OK (environment={settings.environment!r})")
