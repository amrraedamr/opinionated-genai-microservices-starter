from pydantic_settings import BaseSettings, SettingsConfigDict

from base.services.common.meta import SingletonSettings


class CoreSettings(BaseSettings, metaclass=SingletonSettings):
    """Settings every deployable has, regardless of shape.

    Deliberately tiny. Everything a *particular* subsystem needs lives in a
    mixin in `base.services.configuration.mixins`, and a service composes only
    the mixins it actually uses — so a worker with no HTTP surface never
    carries OAuth redirect URIs, and `openai_llm_api_key` can be made
    mandatory in one service without being mandatory in all of them.

    Optional later — Key Vault as a pydantic-settings source + pub/sub reload:
      1. Implement `PydanticBaseSettingsSource` that reads secrets via
         `AzureKeyVaultService` (prefix with `system_keyvault_tag`), mapping
         `appconfig-sql-backend` -> field `sql_backend`.
      2. Override `settings_customise_sources` to insert that source after
         env (so env still wins locally).
      3. On reload: `Singleton._instances.pop(cls, None)` then construct
         again (or `cls.replace(new_instance)`), and publish
         `CacheChannels.KEYVAULT_RELOAD` so other workers refresh. Namespace
         that channel by `service_name` so one service's reload does not wake
         the rest. Subscribe in a capability the way `PromptLoader` does for
         `PROMPT_RELOAD`.
    """

    model_config = SettingsConfigDict(
        env_file=(".env.shared", ".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    service_name: str
    """Required, and deliberately without a default.

    This is the namespace key for Redis pub/sub channels
    (`CacheChannels.for_app`), cache keys, queue names, log fields and trace
    attributes. A wrong default here causes silent cross-service collisions,
    so the service has to state it.
    """

    environment: str = "local"
    log_level: str = "INFO"
    api_prefix: str = "/api"
    max_gunicorn_workers: int = 2
