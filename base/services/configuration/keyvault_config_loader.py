import asyncio
import os
from collections.abc import AsyncIterator
from configparser import ConfigParser
from typing import AsyncGenerator

from azure.keyvault.secrets import SecretProperties

from base.models.definitions.cache import CacheChannels
from base.services.cache.memory import InMemoryCacheService
from base.services.common.meta import Singleton
from base.services.keyvault.azure_keyvault import AzureKeyVaultService


class KeyvaultConfigLoader(metaclass=Singleton):
    def __init__(self):
        self._parser: ConfigParser = ConfigParser()
        self._cache_service: InMemoryCacheService = InMemoryCacheService()
        self._keyvault_provider: AzureKeyVaultService = AzureKeyVaultService()

        self._parser.read("config/config.keyvault.ini")

        if "keyvault" not in self._parser:
            raise ValueError(
                "Config section 'keyvault' is missing in config/config.keyvault.ini"
            )

        self.loading_keyvault_config: bool = False

    async def initialize(self):
        """
        Must be called ONCE at app startup!
        Subscribes to pubsub for distributed reload events.
        Initializes loading of KeyVault secrets.
        """

        self.reload_pubsub = self._cache_service.subscribe(
            CacheChannels.KEYVAULT_RELOAD.value
        )
        self._pubsub_reload_task = asyncio.create_task(
            self.listen_for_reload_events(self.reload_pubsub)  # type: ignore
        )
        await self.load_keyvault_config()

    async def shutdown(self):
        """
        Must be called ONCE at app shutdown!
        Cancels all tasks and pubsub listeners.
        """
        if self._pubsub_reload_task:
            self._pubsub_reload_task.cancel()

    async def listen_for_reload_events(self, pubsub: AsyncGenerator[str, None]):
        async for _ in pubsub:
            print("Received KeyVault reload event. Reloading secrets...")
            await self.load_keyvault_config()
            # Sleep for a short duration to prevent rapid reloads
            print("KeyVault secrets reloaded.")
            await asyncio.sleep(0.1)

    async def load_keyvault_config(self):
        if self.loading_keyvault_config:
            return
        self.loading_keyvault_config = True
        try:
            await self._fetch_prefixed_secrets(f"{self.get('system_keyvault_tag')}-")
        finally:
            self.loading_keyvault_config = False

    async def _fetch_prefixed_secrets(self, prefix: str):
        assert self._parser is not None, "Configuration parser is not initialized."

        secrets: AsyncIterator[SecretProperties] = (
            self._keyvault_provider.alist_secrets()
        )
        try:
            secret_names: list[str] = [
                secret.name
                async for secret in secrets
                if secret.name and secret.name.startswith(prefix)
            ]
            secrets_with_values = await self._fetch_secrets(secret_names)
            for secret_name, secret_value in secrets_with_values.items():
                normalized_key = self._normalize_key(secret_name)
                print(normalized_key)
                if secret_value is not None:
                    self._parser["keyvault"][normalized_key] = secret_value
                    print(f"Loaded secret: {normalized_key} -> {secret_value}")
                else:
                    print(f"Warning: Secret '{secret_name}' not found in KeyVault")
        except Exception as e:
            print(
                f"KeyVault Authentication failed. Loading from config/config.ini. Error: {e}"
            )
            raise

    async def _fetch_secrets(self, secret_names: list[str]) -> dict[str, str | None]:
        return await self._keyvault_provider.aget_secrets(secret_names)

    @staticmethod
    def _normalize_key(key: str) -> str:
        key = key.replace("-", "_")
        if key.startswith("appconfig_"):
            key = key.replace("appconfig_", "")
        return key

    @staticmethod
    def _denormalize_key(key: str) -> str:
        if not key.startswith("appconfig_"):
            key = f"appconfig_{key}"
        key = key.replace("_", "-")
        return key

    def get(self, key: str, default: str = "") -> str:
        value = self._parser["keyvault"].get(key, None)
        if value and value.startswith("ENV:"):
            value = os.getenv(value[4:])
        if value is not None:
            return value
        print(
            f"Key '{key}' not found in configuration or environment variables"
            f"Configuration key '{key}' loaded with value: '{default}'"
        )
        return default
