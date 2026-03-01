# POC-Skeleton Backend

A production-ready Python backend skeleton built with FastAPI, featuring a layered architecture, metaclass-based dependency injection, multi-database support, and pre-wired integrations for Azure services, Redis, vector databases, and LLMs.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Architecture Overview](#architecture-overview)
- [Configuration](#configuration)
- [Dependency Injection (Metaclass System)](#dependency-injection-metaclass-system)
- [Services](#services)
  - [SQL Databases](#sql-databases)
  - [NoSQL (MongoDB)](#nosql-mongodb)
  - [Redis Cache](#redis-cache)
  - [Blob Storage](#blob-storage)
  - [Key Vault](#key-vault)
  - [Vector Search](#vector-search)
  - [Text Embeddings](#text-embeddings)
  - [LLM (OpenAI)](#llm-openai)
  - [HTTP Client](#http-client)
  - [Logging](#logging)
- [Authentication](#authentication)
- [Store (Repository) Layer](#store-repository-layer)
- [Models](#models)
  - [ORM Models](#orm-models)
  - [View Models (Pydantic)](#view-models-pydantic)
  - [Definitions (Enums, Constants)](#definitions-enums-constants)
- [Routers](#routers)
- [Tools (Utilities)](#tools-utilities)
- [Streaming (SSE)](#streaming-sse)
- [Live Log Streaming](#live-log-streaming)
- [Webserver](#webserver)
- [API Endpoints](#api-endpoints)
- [Tech Stack](#tech-stack)

---

## Quick Start

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/)
- RSA key pair for JWT (see below)

### Installation

```bash
cd backend
poetry install
```

### Generate RSA Keys (JWT Auth)

```bash
mkdir -p keys
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
```

### Configure

1. Edit `config.local.ini` — fill in values for the services you need (SQLite works out of the box)
2. For other environments, edit the corresponding `config.{environment}.ini` file (e.g., `config.dev.ini`, `config.uat.ini`, `config.staging.ini`, `config.prod.ini`)
3. If using Key Vault secret loading, edit `config.keyvault.ini` with your tag prefixes

### Run

```bash
# Using poetry script
poetry run api

# Or directly with uvicorn
poetry run uvicorn base.main:app --reload
```

The API will be available at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

---

## Project Structure

```
backend/
├── base/
│   ├── __init__.py                  # Entry point (calls run_webserver)
│   ├── main.py                      # FastAPI app, lifespan, middleware, routes
│   │
│   ├── clients/                     # Low-level database/service clients
│   │   ├── blob/
│   │   │   └── azure_blob.py        # Azure Blob Storage client (sync + async)
│   │   ├── nosql/
│   │   │   └── mongodb.py           # MongoDB client (Motor async driver)
│   │   ├── redis/
│   │   │   └── __init__.py          # Redis client (aioredis async)
│   │   ├── sql/
│   │   │   ├── mysql.py             # MySQL client (aiomysql async)
│   │   │   ├── postgresql.py        # PostgreSQL client (asyncpg)
│   │   │   └── sqlite.py            # SQLite client (aiosqlite async)
│   │   └── vectors/
│   │       ├── azure_ai_search.py   # Azure AI Search client
│   │       └── qdrant.py            # Qdrant vector DB client
│   │
│   ├── models/
│   │   ├── definitions/             # Enums, constants, error definitions
│   │   │   ├── cache.py             # Cache channel enums
│   │   │   ├── database.py          # Database table name constants
│   │   │   ├── errors.py            # Auth, Database, Generic error enums
│   │   │   ├── exceptions.py        # Exception categories
│   │   │   ├── message.py           # Message role enum
│   │   │   ├── model.py             # LLM provider type enum
│   │   │   └── vector_search.py     # Vector search distance metrics
│   │   ├── orm/                     # SQLAlchemy ORM models
│   │   │   ├── __init__.py          # Base, TimestampMixin, auto-import
│   │   │   └── user.py              # UserDTO model
│   │   └── view_models/             # Pydantic request/response models
│   │       ├── __init__.py          # BaseModel, BaseResponse, ErrorResponse
│   │       ├── auth.py              # Auth request/response models, token types
│   │       ├── database.py          # Pagination, sorting, filtered params
│   │       ├── http.py              # HttpResponse model
│   │       ├── model.py             # ModelConfigurations, EmbeddingConfigurations
│   │       ├── streams.py           # SSE stream message models
│   │       ├── user.py              # User CRUD request/response models
│   │       └── vector_search.py     # Vector search result models
│   │
│   ├── routers/                     # FastAPI routers (auto-discovered)
│   │   ├── auth.py                  # /auth — register, login, refresh (placeholder)
│   │   └── user.py                  # /users — get/edit/delete me (placeholder)
│   │
│   ├── services/
│   │   ├── __init__.py              # AbstractService base class
│   │   ├── auth/
│   │   │   ├── __init__.py          # AuthService — JWT token management
│   │   │   ├── auths.py             # HTTPBearer scheme
│   │   │   └── dependencies.py      # validate_user FastAPI dependency
│   │   ├── blob/
│   │   │   ├── __init__.py          # AbstractBlobService
│   │   │   ├── azure_blob.py        # AzureBlobService implementation
│   │   │   └── memory.py            # InMemoryBlobService (for testing)
│   │   ├── cache/
│   │   │   ├── __init__.py          # AbstractCacheService
│   │   │   ├── memory.py            # InMemoryCacheService (for testing)
│   │   │   └── redis.py             # RedisCacheService implementation
│   │   ├── common/
│   │   │   └── meta/
│   │   │       └── __init__.py      # Metaclass DI system
│   │   ├── configuration/
│   │   │   ├── __init__.py
│   │   │   ├── keyvault_config.py   # KeyvaultConfig (reads from Key Vault)
│   │   │   ├── keyvault_config_loader.py  # Loads secrets at startup, pub/sub reload
│   │   │   └── local_config.py      # LocalConfig (reads from config.{environment}.ini)
│   │   ├── http/
│   │   │   └── __init__.py          # HttpRequestService (httpx + requests)
│   │   ├── keyvault/
│   │   │   ├── __init__.py          # AbstractKeyVaultService
│   │   │   └── azure_keyvault.py    # AzureKeyVaultService implementation
│   │   ├── llm/
│   │   │   ├── __init__.py          # AbstractLLMService
│   │   │   └── openai.py            # OpenAIService (OpenAI + Azure OpenAI)
│   │   ├── logging/
│   │   │   ├── __init__.py          # AbstractLoggerService
│   │   │   ├── config.py            # Colored logging config
│   │   │   ├── console.py           # ConsoleLoggerService implementation
│   │   │   ├── helper/
│   │   │   │   └── log_builder.py   # Log formatting helper
│   │   │   └── tee_stream/
│   │   │       └── __init__.py      # TeeStream + TerminalCaptureService
│   │   ├── nosql/
│   │   │   ├── __init__.py          # AbstractNoSQLService
│   │   │   └── mongodb.py           # MongoDBService implementation
│   │   ├── sql/
│   │   │   ├── __init__.py          # AbstractSQLService (query, paginate, upsert)
│   │   │   ├── mysql.py             # MySQLService implementation
│   │   │   ├── postgresql.py        # PostgreSQLService implementation
│   │   │   └── sqlite.py            # SQLiteService implementation
│   │   ├── store/
│   │   │   ├── __init__.py          # AbstractStore (generic repository)
│   │   │   └── user.py              # UserStore implementation
│   │   ├── text_embedding/
│   │   │   ├── __init__.py          # AbstractTextEmbeddingService
│   │   │   └── openai.py            # OpenAITextEmbeddingService (OpenAI + Azure OpenAI)
│   │   └── vector_search/
│   │       ├── __init__.py          # AbstractVectorSearchService
│   │       ├── azure_ai_search.py   # AzureAISearchService implementation
│   │       └── qdrant.py            # QdrantService implementation
│   │
│   └── tools/                       # Utility modules
│       ├── __init__.py
│       ├── database.py              # SQLResultFormats (query result processors)
│       ├── deserializers.py         # JSON deserialization helpers
│       ├── errors.py                # ErrorsException, raise_error
│       ├── locale.py                # Localization utilities
│       ├── misc.py                  # JSON serialization, general helpers
│       ├── routers.py               # Auto-discovery router registration
│       ├── security.py              # PasswordHashingService (Argon2), hash_args
│       ├── serializers.py           # ExpansiveEncoder, serialize()
│       ├── stream.py                # StreamIterator (SSE support)
│       ├── validators.py            # Password validation
│       └── webserver.py             # Uvicorn/Gunicorn launcher
│
├── database/
│   └── poc-skeleton.db              # SQLite database file
├── keys/
│   ├── private.pem                  # RSA private key (JWT signing)
│   └── public.pem                   # RSA public key (JWT verification)
│
├── config.local.ini                 # Local environment configuration
├── config.dev.ini                   # Dev environment configuration
├── config.uat.ini                   # UAT environment configuration
├── config.staging.ini               # Staging environment configuration
├── config.prod.ini                  # Production environment configuration
├── config.keyvault.ini              # Key Vault tag prefixes
├── pyproject.toml                   # Poetry project & dependencies
└── .pre-commit-config.yaml          # Pre-commit hooks
```

---

## Architecture Overview

The skeleton follows a layered architecture with strict separation of concerns:

```
Routers (thin controllers)
   ↓ Depends()
Services (business logic, singletons via metaclass DI)
   ↓
Stores (repository pattern, generic CRUD)
   ↓
SQL/NoSQL Services (session management, query execution)
   ↓
Clients (low-level connection management)
   ↓
Config (LocalConfig / KeyvaultConfig)
```

**Key principles:**
- Routes contain zero business logic — they delegate to services
- All services use metaclass-based DI (no manual wiring, no DI container)
- Every database client provides both sync and async interfaces
- Abstract base classes define contracts; concrete implementations are swappable
- Configuration is split into per-environment files (`config.{environment}.ini`) and Key Vault (`config.keyvault.ini`)

---

## Configuration

### config.{environment}.ini

Each environment has its own configuration file: `config.local.ini`, `config.dev.ini`, `config.uat.ini`, `config.staging.ini`, `config.prod.ini`. The active file is determined by the `ENVIRONMENT` env var (defaults to `local`), which loads `config.{ENVIRONMENT}.ini`.

Each file contains a single INI section matching the environment name (e.g., `[local]` in `config.local.ini`, `[prod]` in `config.prod.ini`). `LocalConfig` validates that the expected section exists at load time.

Supports `ENV:` prefix to resolve values from environment variables:
```ini
pg_password = ENV:DATABASE_PASSWORD
```

**Keys (section name matches the environment):**

| Section | Key | Used By | Description |
|---------|-----|---------|-------------|
| `[{environment}]` | `max_gunicorn_workers` | `webserver.py` | Max gunicorn worker count |
| | `auth_private_key_path` | `AuthService` | Path to RSA private key for JWT signing |
| | `auth_public_key_path` | `AuthService` | Path to RSA public key for JWT verification |
| | `access_token_expiry_seconds` | `AuthService` | Access token TTL (default: 900) |
| | `refresh_token_expiry_seconds` | `AuthService` | Refresh token TTL (default: 604800) |
| | `sqlite_db_path` | `SQLiteClient` | Path to SQLite database file |
| | `db_pool_size` | `MySQL/PostgreSQL` | Connection pool size |
| | `db_max_overflow` | `MySQL/PostgreSQL` | Max overflow connections |
| | `db_pool_timeout` | `MySQL/PostgreSQL` | Pool timeout in seconds |
| | `db_pool_recycle` | `MySQL/PostgreSQL` | Connection recycle time |
| | `db_ssl_enabled` | `MySQL/PostgreSQL` | Enable SSL for DB connections |
| | `pg_*` | `PostgreSQLClient` | PostgreSQL connection settings |
| | `mysql_*` | `MySQLClient` | MySQL connection settings |
| | `redis_*` | `RedisClient` | Redis connection settings |
| | `mongodb_*` | `MongoDBClient` | MongoDB connection settings |
| | `azure_blob_account_url` | `AzureBlobClient` | Azure Blob Storage account URL |
| | `keyvault_url` | `AzureKeyVaultService` | Azure Key Vault URL |
| | `system_keyvault_tag` | `AzureKeyVaultService` | System/app secret name prefix |
| | `model_keyvault_tag` | `AzureKeyVaultService` | Model secret name prefix |
| | `azure_openai_embedding_*` | `OpenAITextEmbedding` | Azure OpenAI embedding config |
| | `openai_embedding_*` | `OpenAITextEmbedding` | OpenAI embedding config |
| | `qdrant_*` | `QdrantClient` | Qdrant vector DB config |
| | `azure_search_*` | `AzureAISearchClient/Service` | Azure AI Search config |

### config.keyvault.ini

Static config for the Key Vault secret loading system. Read by `KeyvaultConfigLoader`.

| Key | Description |
|-----|-------------|
| `model_keyvault_tag` | Prefix for model-related secrets |
| `system_keyvault_tag` | Prefix for system/app-related secrets (loaded at startup) |

Secrets fetched from Key Vault are normalized and stored in memory. Access them via:
```python
KeyvaultConfig.get("some_secret_key")
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `local` | Selects `config.{ENVIRONMENT}.ini` and its matching section |
| `BUILD_VERSION` | `0.0.1` | Application build version |
| `API_HOST` | `0.0.0.0` | Webserver bind host |
| `API_PORT` | `8000` | Webserver bind port |

---

## Dependency Injection (Metaclass System)

Located in `base/services/common/meta/__init__.py`. All DI is handled through Python metaclasses — no container, no decorators, no manual wiring.

### Metaclass Types

| Metaclass | Behavior | Use Case |
|-----------|----------|----------|
| `Singleton` | One instance per class | Services, clients |
| `SingletonABC` | Singleton + ABC | Abstract service base classes |
| `SingletonSettings` | Singleton + Pydantic ModelMetaclass | Settings models |
| `Stored` | One instance per context scope (via `contextvars`) | Per-request scoped services |
| `StoredABC` | Stored + ABC | Abstract scoped services |
| `KeyedSingleton` | One instance per (class, key) pair; auto-derives key from args when `_key` is not provided | Named instances, config-driven services |
| `KeyedSingletonABC` | KeyedSingleton + ABC | Abstract keyed services |
| `ContextManager` | Auto-injects `__enter__`/`__exit__` | Classes needing context manager protocol |
| `ContextManagerSingleton` | ContextManager + Singleton | Singleton context managers |
| `ContextManagerABC` | ContextManager + ABC | Abstract context managers |
| `ContextManagerStored` | ContextManager + Stored | Scoped context managers |
| `NonInitialize` | Prevents instantiation, returns the class itself | Utility/static-only classes |

### Usage Examples

```python
# Singleton service — always returns same instance
class AuthService(AbstractService, metaclass=SingletonABC):
    ...

auth = AuthService()  # Always the same instance

# Keyed singleton with explicit key
class TerminalCaptureService(metaclass=KeyedSingleton):
    ...

capture = TerminalCaptureService(_key="MyApp")

# Keyed singleton with auto-derived key — same args = same instance
# Key is generated by serializing args via ExpansiveEncoder + SHA-256 hash
class OpenAIService(AbstractLLMService, metaclass=KeyedSingletonABC):
    def __init__(self, config: ModelConfigurations) -> None: ...

svc_a = OpenAIService(config=gpt4_config)   # Creates new instance
svc_b = OpenAIService(config=gpt4_config)   # Same config → same instance (cached)
svc_c = OpenAIService(config=mini_config)   # Different config → new instance

# Non-instantiable utility class
class PasswordHashingService(metaclass=NonInitialize):
    @classmethod
    def hash(cls, password: str) -> str: ...

PasswordHashingService.hash("secret")  # Direct class method call

# Scoped per-request
class RequestContext(metaclass=Stored):
    _processor: ClassVar[bool] = False  # Bound to request scope
```

### Global Operations

```python
from base.services.common.meta import purge_all, Singleton, Stored

Singleton.purge()       # Clear all singletons
Stored.delete_scope()   # Clear current scope
purge_all()             # Clear everything
```

---

## Services

### SQL Databases

**Abstract base:** `AbstractSQLService` in `base/services/sql/__init__.py`

Provides a complete SQL toolkit: `query`, `aquery`, `execute`, `aexecute`, `paginate`, `apaginate`, `upsert_row`, `aupsert_row`, `upsert_rows`, `aupsert_rows`, `health_check`, `ahealth_check`, and bulk operations.

**Implementations:**

| Service | Client | Driver | Config Keys |
|---------|--------|--------|-------------|
| `SQLiteService` | `SQLiteClient` | `aiosqlite` | `sqlite_db_path` |
| `MySQLService` | `MySQLClient` | `aiomysql` / `pymysql` | `mysql_*`, `db_*` |
| `PostgreSQLService` | `PostgreSQLClient` | `asyncpg` / `psycopg2` | `pg_*`, `db_*` |

All clients manage both sync and async SQLAlchemy engines with session factories. Features include connection pooling, SSL support, and auto-table creation.

### NoSQL (MongoDB)

**Abstract base:** `AbstractNoSQLService` in `base/services/nosql/__init__.py`

**Implementation:** `MongoDBService` with `MongoDBClient` using Motor (async) and PyMongo (sync).

Config keys: `mongodb_*` (host, username, password, database, pool sizes, timeouts, params).

### Redis Cache

**Abstract base:** `AbstractCacheService` in `base/services/cache/__init__.py`

**Implementations:**

| Service | Description | Config Keys |
|---------|-------------|-------------|
| `RedisCacheService` | Redis-backed with full pub/sub, distributed locks, connection pooling | `redis_*` |
| `InMemoryCacheService` | Thread-safe in-memory implementation for testing/local dev | None |

Features:
- Key-value get/set with TTL
- Hashset operations
- List operations
- Distributed locks (Redis) / local locks (in-memory)
- Pub/Sub messaging (publish, subscribe, batch publish)

### Blob Storage

**Abstract base:** `AbstractBlobService` in `base/services/blob/__init__.py`

**Implementations:**

| Service | Description |
|---------|-------------|
| `AzureBlobService` | Azure Blob Storage with SAS URL generation |
| `InMemoryBlobService` | In-memory implementation for testing |

Operations: `upload`, `download`, `delete`, `exists`, `get_properties`, `list_blobs`, `generate_url`, container management. All with sync + async variants.

Config keys: `azure_blob_account_url`

### Key Vault

**Abstract base:** `AbstractKeyVaultService` in `base/services/keyvault/__init__.py`

**Implementation:** `AzureKeyVaultService` — manages secrets in Azure Key Vault with sync and async clients, secret name formatting with tag prefixes, and `DefaultAzureCredential` authentication.

The `KeyvaultConfigLoader` loads tagged secrets at startup and listens for Redis pub/sub reload events for distributed config refresh.

Config keys: `keyvault_url`, `system_keyvault_tag`, `model_keyvault_tag`

### Vector Search

**Abstract base:** `AbstractVectorSearchService` in `base/services/vector_search/__init__.py`

**Implementations:**

| Service | Client | Config Keys |
|---------|--------|-------------|
| `QdrantService` | `QdrantClient` | `qdrant_*` |
| `AzureAISearchService` | `AzureAISearchClient` | `azure_search_*` |

Operations: `search`, `upsert`, `delete`, `create_collection`, `delete_collection`, `health_check`. All sync + async.

### Text Embeddings

**Abstract base:** `AbstractTextEmbeddingService` in `base/services/text_embedding/__init__.py`

**Implementation:** `OpenAITextEmbeddingService` (metaclass: `KeyedSingletonABC`) — works with any OpenAI-compatible embedding API (OpenAI, Azure OpenAI, vLLM, Ollama, LiteLLM, Together, Groq, etc.)

Uses `KeyedSingletonABC` with auto-derived keys: passing the same `EmbeddingConfigurations` returns the cached instance, while a different config creates a new one.

Features:
- Sync (`embed_query`, `embed_documents`) and async (`aembed_query`, `aembed_documents`) variants
- Configurable batch size and optional `dimensions` parameter (for OpenAI `text-embedding-3-*` models)
- HTTP/2 connection pooling via `httpx`
- Azure OpenAI and standard OpenAI client support

Configuration is passed via `EmbeddingConfigurations` Pydantic model (not from config.ini — designed to support dynamic embedding configs from Key Vault or database).

### LLM (OpenAI)

**Abstract base:** `AbstractLLMService` in `base/services/llm/__init__.py`

**Implementation:** `OpenAIService` (metaclass: `KeyedSingletonABC`) — works with any OpenAI-compatible API (OpenAI, Azure OpenAI, vLLM, Ollama, LiteLLM, Together, Groq, etc.)

Uses `KeyedSingletonABC` with auto-derived keys: passing the same `ModelConfigurations` returns the cached instance, while a different config creates a new one. This means one client + connection pool per unique model configuration, with no manual key management required.

Features:
- Sync (`generate`) and async (`agenerate`) chat completions
- Streaming with `StreamIterator` integration
- Automatic retry with backoff on rate limits and timeouts
- HTTP/2 connection pooling via `httpx`
- Azure OpenAI and standard OpenAI client support

Configuration is passed via `ModelConfigurations` Pydantic model (not from config.ini — designed to support dynamic model configs from Key Vault or database).

### HTTP Client

`HttpRequestService` in `base/services/http/__init__.py` — a singleton HTTP client providing both sync (via `requests`) and async (via `httpx` with HTTP/2) request methods.

Features:
- Automatic retry with exponential backoff on timeouts
- JSON and non-JSON response parsing
- Error detail extraction
- Returns `HttpResponse` model with `ok()`/`fail()` factory methods

### Logging

**Abstract base:** `AbstractLoggerService` in `base/services/logging/__init__.py`

**Implementation:** `ConsoleLoggerService` — colored console logging with structured error formatting (code, category, location, tag).

Logging config in `base/services/logging/config.py` uses `colorlog` for colored output.

---

## Authentication

JWT-based authentication with RS256 (RSA asymmetric keys).

**Components:**
- `AuthService` (`base/services/auth/__init__.py`) — token generation, refresh, and validation
- `PasswordHashingService` (`base/tools/security.py`) — Argon2 password hashing
- `validate_user` dependency (`base/services/auth/dependencies.py`) — FastAPI `Depends()` for route protection

**Token flow:**
1. Register: hash password, create user in DB
2. Login: verify password, generate access + refresh token pair
3. Protected routes: `Depends(validate_user)` validates access token, returns `UserDTO`
4. Refresh: validate refresh token, generate new token pair

**Token types:** `AccessToken` and `RefreshToken` are `NewType` wrappers around `str` for type safety.

---

## Store (Repository) Layer

**Abstract base:** `AbstractStore[T]` in `base/services/store/__init__.py`

A **database-agnostic** generic repository pattern with complete CRUD + pagination. Works with both SQL and NoSQL backends. All operations have sync and async variants:

| Operation | Sync | Async |
|-----------|------|-------|
| Get by ID/column | `get()` | `aget()` |
| Get many | `get_many()` | `aget_many()` |
| Add | `add()` | `aadd()` |
| Add many | `add_many()` | `aadd_many()` |
| Edit | `edit()` | `aedit()` |
| Delete (soft) | `delete()` | `adelete()` |
| Get all | `get_all()` | `aget_all()` |
| Get all paged | `get_all_paged()` | `aget_all_paged()` |

Public methods are `@final` and handle duplicate-key errors → `UNIQUE_CONSTRAINT_VIOLATION` and missing records → `RECORD_NOT_FOUND`. Subclasses implement the `_` prefixed abstract methods.

`AbstractStore` has **no dependency on any specific database library**. Subclasses are responsible for:
- Setting up their own database service (SQL or NoSQL) in `__init__`
- Implementing all abstract CRUD methods using their chosen service
- Overriding `_is_duplicate_error(error)` to map their DB driver's duplicate-key exception

### SQL Store Example (UserStore)

```python
class UserStore(AbstractStore[UserDTO], metaclass=SingletonABC):
    def __init__(self) -> None:
        super().__init__()
        self._sql_service = SQLiteService()
        self._base_select_query = select(UserDTO)

    def _is_duplicate_error(self, error: Exception) -> bool:
        return isinstance(error, IntegrityError)

    def _get(self, value: Any, column_name: str = "id") -> UserDTO | None:
        query = self._base_select_query.where(getattr(UserDTO, column_name) == value)
        return self._sql_service.query(query, SQLResultFormats.one_or_none_scalar)
    ...
```

### NoSQL Store Example (MongoDB)

```python
class DocumentStore(AbstractStore[dict[str, Any]], metaclass=SingletonABC):
    def __init__(self) -> None:
        super().__init__()
        self._nosql_service = MongoDBService()
        self._collection_name = "documents"

    def _is_duplicate_error(self, error: Exception) -> bool:
        from pymongo.errors import DuplicateKeyError
        return isinstance(error, DuplicateKeyError)

    def _get(self, value: Any, column_name: str = "id") -> dict[str, Any] | None:
        return self._nosql_service.find_one(self._collection_name, {column_name: value})
    ...
```

---

## Models

### ORM Models

Located in `base/models/orm/`.

- `Base` — `MappedAsDataclass + DeclarativeBase` with `to_dict()`, `update_from_dict()`, `clone()` helpers
- `TimestampMixin` — adds `created_at`, `updated_at`, `deleted_at` with `soft_delete()` and `restore()` methods
- `UserDTO` — example user model with UUID primary key, email, password hash, name fields, and indexes

ORM models are auto-discovered via `pkgutil.walk_packages` in `base/models/orm/__init__.py`.

### View Models (Pydantic)

Located in `base/models/view_models/`.

- `BaseModel` — Pydantic BaseModel with camelCase alias generation, `serialize()`, `deserialize()`, `jsonify()` methods
- `BaseResponse[T]` — generic success response wrapper (`success: True, data: T`)
- `ErrorResponse[T]` — generic error response wrapper (`success: False, error: str`)
- `HttpResponse` — HTTP response model with `ok()`/`fail()` factory methods
- `PaginatedResult[T]` — paginated response with `data`, `page`, `size`, `total`, `total_pages`
- `PaginationParams`, `SortingParams`, `FilteredPaginationParams` — query parameter models
- `ModelConfigurations` — LLM provider configuration model
- `EmbeddingConfigurations` — text embedding provider configuration model
- `StreamStart`, `StreamMessage`, `StreamEnd`, `StreamError` — SSE stream event models
- Auth models: `RegisterRequest`, `LoginRequest/Response`, `RefreshRequest/Response`, `TokenPair`
- User models: `GetUserResponse`, `EditUserRequest/Response`, `CreateUserResponse`, `DeleteUserResponse`

### Definitions (Enums, Constants)

Located in `base/models/definitions/`.

- `AuthErrors`, `DatabaseErrors`, `GenericErrors` — error enums with message and status code
- `DatabaseTable` — table name constants
- `CacheChannels` — Redis pub/sub channel names
- `ProviderType` — AI provider enum (OpenAI, Azure OpenAI, Ollama, vLLM, Groq, Together, LiteLLM)
- `MessageRole` — chat message role enum
- `ExceptionCategory` — exception classification
- `DistanceMetric` — vector search distance metrics

---

## Routers

Routers are auto-discovered from the `base/routers/` package using `pkgutil.iter_modules`. Each module must export a `router` variable (`APIRouter` instance).

All routers are mounted under the `/api/v1` prefix.

**Note:** The included `auth.py` and `user.py` routers are **testing placeholders**. They demonstrate how to structure routes, wire up services, use `Depends()` for auth, and interact with the store layer. Replace or extend them with your own routes for your actual application.

### Adding a New Router

1. Create a file in `base/routers/` (e.g., `items.py`)
2. Define `router = APIRouter(prefix="/items", tags=["Items"])`
3. Add your route handlers
4. It's automatically registered — no manual wiring needed

---

## Tools (Utilities)

| Module | Purpose |
|--------|---------|
| `database.py` | `SQLResultFormats` — query result processor functions for SQLAlchemy |
| `errors.py` | `ErrorsException` class and `raise_error()` helper |
| `security.py` | `PasswordHashingService` (Argon2 hashing), `hash_args` (deterministic SHA-256 of arbitrary args via `ExpansiveEncoder`) |
| `serializers.py` | `ExpansiveEncoder` (JSON encoder for Pydantic, DTOs, UUIDs, datetimes), `serialize()` |
| `deserializers.py` | JSON deserialization helpers |
| `routers.py` | `init_routers()` — auto-discovery router registration |
| `webserver.py` | `run_webserver()` — Uvicorn (dev) / Gunicorn (prod) launcher |
| `stream.py` | `StreamIterator` — async iterator for SSE streaming |
| `validators.py` | Password validation logic |
| `misc.py` | JSON serialization, general utilities |
| `locale.py` | Localization utilities |

---

## Streaming (SSE)

The skeleton includes full Server-Sent Events support via `sse-starlette`.

**Components:**
- `StreamIterator` (`base/tools/stream.py`) — async iterator that wraps an `asyncio.Queue` or `AsyncIterator` and formats messages as SSE events
- Stream models (`base/models/view_models/streams.py`):
  - `StreamStart` — sent when streaming begins
  - `StreamMessage` — carries content chunks
  - `StreamEnd` — signals stream completion
  - `StreamError` — signals stream failure
- `OpenAIService` integrates directly with `StreamIterator` for streaming LLM responses

---

## Live Log Streaming

The skeleton includes a built-in live log streaming system via `TerminalCaptureService`:

1. At startup, `TeeStream` wraps `stdout`/`stderr` to capture all output
2. Captured output is buffered and published to Redis pub/sub
3. The `POST /logs` endpoint (authenticated) returns an SSE stream of live application logs

This enables real-time log monitoring from the frontend without direct server access.

---

## Webserver

The webserver launcher (`base/tools/webserver.py`) automatically selects the server based on environment:

| Environment | Server | Features |
|-------------|--------|----------|
| `local` | Uvicorn | Hot reload enabled |
| Any other | Gunicorn + Uvicorn workers | Multi-process, configurable workers, preload |

Gunicorn is configured with:
- Worker count: `min(cpu_count + 1, max_gunicorn_workers)`
- Worker class: `UvicornWorker`
- Timeout: 500s, graceful timeout: 300s

---

## API Endpoints

### Main

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | No | Welcome message + version |
| GET | `/health-check` | No | Health check |
| POST | `/logs` | Yes | Live SSE log stream |

### Auth (`/api/v1/auth`) — *placeholder*

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/register` | No | Create user account |
| POST | `/login` | No | Login, get token pair |
| POST | `/refresh` | No | Refresh token pair |

### Users (`/api/v1/users`) — *placeholder*

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/me` | Yes | Get current user profile |
| PUT | `/me` | Yes | Edit current user profile |
| DELETE | `/me` | Yes | Soft-delete current user |

---

## Tech Stack

| Category | Technology |
|----------|------------|
| **Language** | Python 3.12+ |
| **Framework** | FastAPI + Uvicorn + Gunicorn |
| **ORM** | SQLAlchemy 2.x (async + sync) |
| **Validation** | Pydantic v2 |
| **Auth** | PyJWT (RS256), Argon2 |
| **HTTP Client** | httpx (HTTP/2), requests |
| **Databases** | SQLite, MySQL, PostgreSQL, MongoDB |
| **Cache** | Redis (pub/sub, caching, lists) |
| **Vector DBs** | Qdrant, Azure AI Search |
| **LLM** | OpenAI SDK (OpenAI, Azure OpenAI, any compatible) |
| **Cloud** | Azure Key Vault, Azure Blob Storage, Azure Identity |
| **Streaming** | SSE via sse-starlette |
| **Password Hashing** | argon2-cffi |
| **Logging** | colorlog (colored console output) |
| **Package Manager** | Poetry |
| **Linting** | Ruff |
| **Pre-commit** | pre-commit hooks |
