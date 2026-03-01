import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from azure.keyvault.secrets import SecretClient, SecretProperties
from azure.keyvault.secrets.aio import SecretClient as AsyncSecretClient

from base.services.common.meta import SingletonABC
from base.services.configuration.local_config import LocalConfig
from base.services.keyvault import AbstractKeyVaultService


class AzureKeyVaultService(AbstractKeyVaultService, metaclass=SingletonABC):
    def __init__(self) -> None:
        self._client: SecretClient | None = None
        self._async_client: AsyncSecretClient | None = None
        self._credential: DefaultAzureCredential | None = None
        self._async_credential: AsyncDefaultAzureCredential | None = None

    # ── Client lifecycle ──────────────────────────────────────────────

    @property
    def client(self) -> SecretClient:
        if self._client is None:
            self._credential = DefaultAzureCredential()
            self._client = SecretClient(
                vault_url=LocalConfig.get("keyvault_url"),
                credential=self._credential,
            )
        return self._client

    @property
    def async_client(self) -> AsyncSecretClient:
        if self._async_client is None:
            self._async_credential = AsyncDefaultAzureCredential()
            self._async_client = AsyncSecretClient(
                vault_url=LocalConfig.get("keyvault_url"),
                credential=self._async_credential,
            )
        return self._async_client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
        if self._credential is not None:
            self._credential.close()
            self._credential = None

    async def aclose(self) -> None:
        if self._async_client is not None:
            await self._async_client.close()
            self._async_client = None
        if self._async_credential is not None:
            await self._async_credential.close()
            self._async_credential = None

    def __enter__(self) -> "AzureKeyVaultService":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    async def __aenter__(self) -> "AzureKeyVaultService":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    # ── Secret operations ─────────────────────────────────────────────

    def get_secret(self, secret_name: str) -> str | None:
        formatted: str = self.format_secret_name(secret_name)
        return self.client.get_secret(formatted).value

    async def aget_secret(self, secret_name: str) -> str | None:
        formatted: str = self.format_secret_name(secret_name)
        secret = await self.async_client.get_secret(formatted)
        return secret.value

    def get_secrets(self, secret_names: list[str]) -> dict[str, str | None]:
        return {name: self.get_secret(name) for name in secret_names}

    async def aget_secrets(
        self, secret_names: list[str], concurrent: bool = True
    ) -> dict[str, str | None]:
        if not concurrent:
            return {name: await self.aget_secret(name) for name in secret_names}

        results: list[str | None] = await asyncio.gather(
            *(self.aget_secret(name) for name in secret_names)
        )
        return dict(zip(secret_names, results, strict=True))

    def upsert_secret(
        self, secret_key: str, secret_value: str, format_name: bool = True
    ) -> str:
        if format_name:
            secret_key = self.format_secret_name(secret_key)
        secret = self.client.set_secret(secret_key, secret_value)
        assert (
            secret.properties.version is not None
        ), "Azure returned no version after upsert"
        return secret.properties.version

    async def aupsert_secret(
        self, secret_key: str, secret_value: str, format_name: bool = True
    ) -> str:
        if format_name:
            secret_key = self.format_secret_name(secret_key)
        secret = await self.async_client.set_secret(secret_key, secret_value)
        assert (
            secret.properties.version is not None
        ), "Azure returned no version after upsert"
        return secret.properties.version

    def remove_secret(self, secret_name: str) -> None:
        formatted: str = self.format_secret_name(secret_name)
        self.client.begin_delete_secret(formatted)

    async def aremove_secret(self, secret_name: str) -> None:
        formatted: str = self.format_secret_name(secret_name)
        await self.async_client.delete_secret(formatted)

    def list_secrets(self) -> Iterator[SecretProperties]:
        return self.client.list_properties_of_secrets()

    def alist_secrets(self) -> AsyncIterator[SecretProperties]:
        return self.async_client.list_properties_of_secrets()

    # ── Naming ────────────────────────────────────────────────────────

    def format_secret_name(
        self, secret_name: str, allowed_prefix: str | None = None
    ) -> str:
        """Azure-specific secret name formatting with keyvault tag prefixes."""
        prefixes: list[str] = [
            LocalConfig.get("system_keyvault_tag"),
            LocalConfig.get("model_keyvault_tag"),
        ]

        for prefix in prefixes:
            if secret_name.startswith(prefix):
                if allowed_prefix and not secret_name.startswith(allowed_prefix):
                    raise ValueError(
                        f"Secret name '{secret_name}' does not start with "
                        f"the allowed prefix '{allowed_prefix}'."
                    )
                return secret_name

        return f"{LocalConfig.get('system_keyvault_tag')}-{secret_name}"

    def get_service_name(self) -> str:
        return "Azure Key Vault"
