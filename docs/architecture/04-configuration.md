# 04 — Configuration

> **Requirement:** each app/service has its own `.env` — different deployments, different
> LLM keys. Settings should be a base class that each service inherits and extends, with
> only genuinely shared settings living in `base`.

That is the right instinct. This document refines it in two ways: **compose mixins rather
than inherit one class**, and **resolve settings through a provider** so that `base` code
sees the service's settings rather than its own.

---

## Problem with the current shape

`base/services/configuration/settings.py` is a single 231-line `Settings` class holding
every field for every integration — app, auth, five OAuth providers, enterprise IdP, SQL,
NoSQL, vectors, blob, Key Vault, LLM, cache.

It is exposed as a module-level singleton and imported directly in **20 places**:

```python
from base.services.configuration import settings
```

Two consequences for multiple services:

1. **Inheriting one god-class gives every service every field.** A worker with no HTTP
   surface still carries `oauth_apple_private_key_path`. Worse, you lose the ability to
   *require* a field: `OPENAI_API_KEY` cannot be mandatory in `chat-api` if the same class
   must also validate for a service that has no LLM.
2. **A subclass is invisible to `base`.** If `chat-api` defines
   `class Settings(BaseSettings)`, the 20 modules inside `base` still import the *base*
   instance. The subclass is never consulted.

---

## Design

### Layer 1 — `CoreSettings`: genuinely universal only

Everything here must apply to *every* deployable, including a worker with no database and
no HTTP server. That is about six fields.

```python
# packages/base/base/services/configuration/core.py
from pydantic_settings import BaseSettings, SettingsConfigDict

from base.services.common.meta import SingletonSettings


class CoreSettings(BaseSettings, metaclass=SingletonSettings):
    """Settings every deployable has, regardless of shape."""

    model_config = SettingsConfigDict(
        env_file=(".env.shared", ".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    service_name: str                       # required — identifies the service everywhere
    environment: str = "local"
    log_level: str = "INFO"
    api_prefix: str = "/api"
    max_gunicorn_workers: int = 2
```

`service_name` is deliberately **required and unnamed-by-default**. It is the namespace key
for Redis channels (`CacheChannels.for_app`), cache keys, queue names, log fields and
trace attributes — a wrong default here causes cross-service collisions, so the service
must state it.

### Layer 2 — mixins per subsystem

One mixin per optional subsystem, mirroring the dependency extras in
[doc 02](02-library-boundary.md). A service includes a mixin only if it uses that subsystem.

```python
# packages/base/base/services/configuration/mixins.py
from typing import Literal

from pydantic import BaseModel, Field


class SQLSettingsMixin(BaseModel):
    sql_backend: Literal["sqlite", "mysql", "postgresql"] = "sqlite"
    sqlite_db_path: str = "database/app.db"
    db_host: str = ""
    db_port: int = 5432
    db_name: str = ""
    db_user: str = ""
    db_password: str = ""
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    db_ssl_enabled: bool = True


class LLMSettingsMixin(BaseModel):
    llm_provider: str = "openai"
    openai_api_key: str = Field(default="")
    openai_base_url: str = ""
    default_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 120


class RedisSettingsMixin(BaseModel):
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300


class TokenVerificationMixin(BaseModel):
    """Verify tokens. Does NOT issue them — see doc 05."""
    auth_public_key_path: str = "keys/public.pem"
    auth_algorithms: str = "RS256"
    auth_issuer: str = ""
    auth_audience: str = ""


class TokenIssuingMixin(TokenVerificationMixin):
    """Only the identity service should include this."""
    auth_private_key_path: str = "keys/private.pem"
    access_token_expiry_seconds: int = 900
    refresh_token_expiry_seconds: int = 604800
```

Further mixins lift the remaining groups from today's file unchanged:
`OAuthSettingsMixin`, `IdpResourceServerMixin`, `MongoSettingsMixin`,
`VectorSettingsMixin`, `BlobSettingsMixin`, `KeyVaultSettingsMixin`.

### Layer 3 — the service composes and extends

```python
# services/chat-api/chat_api/settings.py
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from base.services.configuration.core import CoreSettings
from base.services.configuration.mixins import (
    LLMSettingsMixin,
    RedisSettingsMixin,
    SQLSettingsMixin,
    TokenVerificationMixin,
)


class ChatApiSettings(
    CoreSettings,
    SQLSettingsMixin,
    LLMSettingsMixin,
    RedisSettingsMixin,
    TokenVerificationMixin,
):
    model_config = SettingsConfigDict(
        env_file=("../../.env.shared", ".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "chat-api"

    # Tightened: required here, absent elsewhere
    openai_api_key: str = Field(min_length=1)

    # Service-specific
    max_tokens_per_conversation: int = 8_000
    conversation_retention_days: int = 90
    cors_origins: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = ChatApiSettings()
```

This is the inheritance model asked for — just granular enough that each service carries
only what it uses, and can **tighten** validation (`openai_api_key` is mandatory here and
does not exist at all in `identity`).

---

## Making `base` see the service's settings

`base` modules cannot import a service's settings — that would invert the dependency. Two
mechanisms, used together.

### Mechanism 1 — provider registration (runtime)

The existing `SingletonSettings` metaclass and `Singleton.replace()` already provide the
hook.

```python
# packages/base/base/services/configuration/__init__.py
_settings: CoreSettings | None = None


def configure(instance: CoreSettings) -> None:
    """Called once by the service composition root, before anything else."""
    global _settings
    _settings = instance


def get_settings() -> CoreSettings:
    if _settings is None:
        raise RuntimeError(
            "Settings not configured. Call base.services.configuration.configure(...) "
            "in your service entrypoint before importing base services."
        )
    return _settings
```

The 20 `settings.foo` sites in `base` become `get_settings().foo`. A deprecation shim can
keep the old import working during the migration.

### Mechanism 2 — Protocols (static)

Runtime lookup alone loses type safety. Each `base` subsystem declares the shape it needs,
and type checkers verify structurally that a service's composed settings satisfy it:

```python
# packages/base/base/services/sql/protocol.py
from typing import Protocol, runtime_checkable


@runtime_checkable
class SupportsSQLConfig(Protocol):
    sql_backend: str
    db_pool_size: int
    db_pool_recycle: int
    db_ssl_enabled: bool
```

```python
class SQLService:
    def __init__(self, config: SupportsSQLConfig | None = None) -> None:
        self._config = config or cast(SupportsSQLConfig, get_settings())
```

A service that uses `SQLService` without `SQLSettingsMixin` now fails at type-check time
with a clear message, rather than at runtime with `AttributeError`.

> **Preferred for new code:** pass config explicitly into constructors. The provider is the
> pragmatic bridge for the 20 existing call sites, not the long-term ideal.

---

## Per-service `.env`

### Layout

```
.env.shared.example          # local-dev infra shared by all services (committed)
.env.shared                  # gitignored
services/identity/.env.example
services/identity/.env       # gitignored
services/chat-api/.env.example
services/chat-api/.env       # gitignored
```

The existing root `.gitignore` already does the right thing and applies at every depth:

```
.env
.env.*
!.env.example
```

### Precedence

`pydantic-settings` applies `env_file` entries in order, with **later files winning**, and
real process environment variables beating all files.

| Priority | Source | Purpose |
| --- | --- | --- |
| 1 (highest) | Process environment | Production. Injected by Container Apps / K8s / App Service |
| 2 | `.env.local` | Personal overrides. Never committed |
| 3 | `.env` | The service's own local values — **its own LLM key, its own database** |
| 4 | `.env.shared` | Shared local infra only (Postgres host, Redis URL) |
| 5 (lowest) | Field defaults | Safe defaults in code |

`.env.shared` is strictly a **local developer convenience** for infrastructure endpoints. It
must never hold a secret that differs per environment — in deployment it does not exist,
and process env supplies everything.

### Different keys per service, per deployment

This falls out naturally. `chat-api` and `ingestion-worker` each read `OPENAI_API_KEY` from
their **own** `.env`, so they can use different keys, different quotas, different models:

```ini
# services/chat-api/.env
SERVICE_NAME=chat-api
OPENAI_API_KEY=sk-chat-...
DEFAULT_MODEL=gpt-4o
DB_NAME=chat_db
```

```ini
# services/ingestion-worker/.env
SERVICE_NAME=ingestion-worker
OPENAI_API_KEY=sk-batch-...
DEFAULT_MODEL=gpt-4o-mini
MONGO_DATABASE=ingestion
```

In production each service is a separate deployment unit with its own environment
configuration, so the same separation holds with no extra mechanism.

### Compose: keep the files, don't flatten them

```yaml
chat-api:
  build: { context: ., dockerfile: docker/service.Dockerfile, args: { SERVICE: chat-api } }
  env_file:
    - ./.env.shared
    - ./services/chat-api/.env
  environment:
    ENVIRONMENT: local
```

Compose's `env_file` honours the same ordering, so one `docker compose up` reproduces the
local precedence exactly.

> **If you ever must put several services in one env file**, use `env_prefix` per settings
> class (`CHAT_API_`, `IDENTITY_`) to disambiguate. Prefer separate files; the prefix is a
> fallback, not the default.

---

## Secrets

| Environment | Mechanism |
| --- | --- |
| Local | `.env` / `.env.local`, gitignored |
| CI | Repository/environment secrets as process env |
| Production | Key Vault, K8s Secrets, or Container Apps secrets → injected as process env |

`.env` files never ship inside an image. `.dockerignore` must exclude them, and
[doc 06](06-build-and-deploy.md) treats that as a build-time assertion rather than a
convention.

The existing `Settings` docstring already sketches a Key Vault settings source plus
`CacheChannels.KEYVAULT_RELOAD` pub/sub reload. That design carries over unchanged — add it
as a source on `CoreSettings` so **every** service inherits hot reload at once, and
namespace the reload channel by `service_name` so one service's reload does not wake the
rest.

---

## Validation at startup

Fail fast and loudly. A service that boots with a missing key and only fails on the first
user request is worse than one that refuses to start.

- Mark truly required fields with no default (`service_name`, and per-service keys like
  `openai_api_key` above).
- Instantiate settings in the composition root **before** `create_app()` returns.
- Surface Pydantic's validation error directly — it already names the offending field.
- Add a `uv run --package chat-api python -m chat_api.settings --check` entrypoint for CI
  and for a container `preStart` probe.
