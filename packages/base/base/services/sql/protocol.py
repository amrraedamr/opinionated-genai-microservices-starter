from typing import Protocol, runtime_checkable


@runtime_checkable
class SupportsSQLConfig(Protocol):
    """Settings shape the SQL client and service require.

    A service that uses `SQLService` without `SQLSettingsMixin` fails at type
    check time with a clear message, rather than at runtime with
    `AttributeError` on the first query.
    """

    sql_backend: str
    sqlite_db_path: str
    db_pool_size: int
    db_max_overflow: int
    db_pool_timeout: int
    db_pool_recycle: int
    db_ssl_enabled: bool


@runtime_checkable
class SupportsPostgresConfig(SupportsSQLConfig, Protocol):
    pg_host: str
    pg_port: str
    pg_database: str
    pg_ssl_root_cert: str
    pg_username: str
    pg_password: str


@runtime_checkable
class SupportsMySQLConfig(SupportsSQLConfig, Protocol):
    mysql_host: str
    mysql_database: str
    mysql_username: str
    mysql_password: str
