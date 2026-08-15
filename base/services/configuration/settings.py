from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from base.services.common.meta import SingletonSettings


class Settings(BaseSettings, metaclass=SingletonSettings):
    """Typed app settings from process env and optional `.env`.

    Starter default: env-only. Deploy the same vars via App Service / Container Apps /
    compose.

    Optional later — Key Vault as a pydantic-settings source + pub/sub reload:
      1. Implement `PydanticBaseSettingsSource` that reads secrets via
         `AzureKeyVaultService` (prefix with `system_keyvault_tag`), mapping
         `appconfig-sql-backend` → field `sql_backend`.
      2. Override `Settings.settings_customise_sources` to insert that source
         after env (so env still wins locally).
      3. On reload: `Singleton._instances.pop(Settings, None)` then call
         `Settings()` again (or `Settings.replace(new_instance)`), and publish
         `CacheChannels.KEYVAULT_RELOAD` so other workers refresh. Subscribe in
         app lifespan the same way `PromptLoader` does for `PROMPT_RELOAD`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # App
    app_name: str = "opinionated-genai-starter"
    environment: str = "local"
    max_gunicorn_workers: int = 2

    # Auth
    auth_private_key_path: str = "keys/private.pem"
    auth_public_key_path: str = "keys/public.pem"
    access_token_expiry_seconds: int = 900
    refresh_token_expiry_seconds: int = 604800

    # SQL
    sql_backend: Literal["sqlite", "mysql", "postgresql"] = "sqlite"
    sqlite_db_path: str = "database/app.db"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    db_ssl_enabled: bool = True

    # PostgreSQL
    pg_host: str = ""
    pg_port: str = "5432"
    pg_database: str = ""
    pg_ssl_root_cert: str = ""
    pg_username: str = Field(
        default="",
        validation_alias=AliasChoices("POSTGRES_USER", "PG_USERNAME"),
    )
    pg_password: str = Field(
        default="",
        validation_alias=AliasChoices("POSTGRES_PASSWORD", "PG_PASSWORD"),
    )

    # MySQL
    mysql_host: str = ""
    mysql_database: str = ""
    mysql_username: str = Field(
        default="",
        validation_alias=AliasChoices("MYSQL_USER", "MYSQL_USERNAME"),
    )
    mysql_password: str = Field(
        default="",
        validation_alias=AliasChoices("MYSQL_PASSWORD"),
    )

    # Redis
    redis_url: str = ""
    redis_ssl_cert_reqs: str = ""
    redis_max_connections: int = 50
    redis_socket_timeout: float = 5.0
    redis_socket_connect_timeout: float = 5.0
    redis_retry_on_timeout: bool = True
    redis_health_check_interval: int = 30
    redis_decode_responses: bool = True

    # Cosmos DB
    azure_cosmos_account_uri: str = ""
    azure_cosmos_account_key: str = ""
    azure_cosmos_database_name: str = ""

    # MongoDB
    mongodb_username: str = Field(
        default="",
        validation_alias=AliasChoices("MONGODB_USER", "MONGODB_USERNAME"),
    )
    mongodb_password: str = Field(
        default="",
        validation_alias=AliasChoices("MONGODB_PASSWORD"),
    )
    mongodb_base_path: str = "mongodb"
    mongodb_host: str = "localhost"
    mongodb_database: str = ""
    mongodb_params: str = ""
    mongodb_min_pool_size: int = 5
    mongodb_max_pool_size: int = 50
    mongodb_connect_timeout_ms: int = 10_000
    mongodb_socket_timeout_ms: int = 30_000
    mongodb_server_selection_timeout_ms: int = 30_000

    # Azure Blob
    azure_blob_account_url: str = ""

    # Azure Key Vault — runtime secret API only (not a Settings backend; see class docstring)
    keyvault_url: str = ""
    system_keyvault_tag: str = "appconfig"
    model_keyvault_tag: str = "modelconfig"

    # Azure OpenAI LLM
    azure_openai_api_version: str = ""
    azure_openai_llm_endpoint: str = ""
    azure_openai_llm_deployment_name: str = ""
    azure_openai_llm_api_key: str = ""

    # Azure OpenAI Embeddings
    azure_openai_embedding_endpoint: str = ""
    azure_openai_embedding_deployment_name: str = ""
    azure_openai_embedding_api_key: str = ""
    azure_openai_embedding_dimensions: int = 3072
    azure_openai_embedding_batch_size: int = 2048

    # OpenAI LLM
    openai_llm_endpoint: str = ""
    openai_llm_model: str = ""
    openai_llm_api_key: str = ""

    # OpenAI Embeddings
    openai_embedding_endpoint: str = ""
    openai_embedding_model: str = ""
    openai_embedding_api_key: str = ""
    openai_embedding_dimensions: int = 1536
    openai_embedding_batch_size: int = 2048

    # Qdrant
    qdrant_url: str = ""
    qdrant_grpc_port: int = 6334
    qdrant_prefer_grpc: bool = True
    qdrant_timeout: int = 30
    qdrant_api_key: str = ""

    # Azure AI Search
    azure_search_endpoint: str = ""
    azure_search_vector_field: str = "vector"
    azure_search_key_field: str = "id"
    azure_search_api_key: str = ""

    # Prompts
    load_prompts_from_db: bool = False


settings = Settings()
