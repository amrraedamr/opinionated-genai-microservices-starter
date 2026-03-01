import base64
import json
import os
from configparser import ConfigParser


class LocalConfig:
    _parser: ConfigParser | None = None

    environment: str = os.environ.get("ENVIRONMENT", "local")
    build_version: str = os.environ.get("BUILD_VERSION", "0.0.1")

    @staticmethod
    def _load() -> bool:
        if LocalConfig._parser is None:
            LocalConfig._parser = ConfigParser()
            LocalConfig._parser.read(f"config.{LocalConfig.environment}.ini")

            section = LocalConfig.environment
            if section not in LocalConfig._parser:
                raise ValueError(
                    f"Config section '{section}' is missing in config.{LocalConfig.environment}.ini"
                )

        return True

    @staticmethod
    def get(key: str, default: str = "") -> str:
        if LocalConfig._load():
            if not LocalConfig._parser:
                raise ValueError("ConfigParser not initialized properly")

            value = LocalConfig._parser[LocalConfig.environment].get(key, None)
            if value and value.startswith("ENV:"):
                value = os.getenv(value[4:])
            if value is not None:
                return value
        print(
            f"Key '{key}' not found in configuration or environment variables"
            f". Configuration key '{key}' loaded with value: '{default}'"
        )
        return default

    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        value = LocalConfig.get(key)
        return int(value) if value else default

    @staticmethod
    def get_float(key: str, default: float = 0.0) -> float:
        value = LocalConfig.get(key)
        return float(value) if value else default

    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        value = LocalConfig.get(key)
        return value.lower() in ("true", "1", "yes") if value else default

    @staticmethod
    def get_dict(key: str, default: dict | None = None) -> dict:
        value = LocalConfig.get(key)
        return json.loads(value) if value else (default if default is not None else {})

    @staticmethod
    def get_bytes(key: str, default: bytes = b"") -> bytes:
        value = LocalConfig.get(key)
        if value:
            # This decodes the base64 string to bytes
            return base64.urlsafe_b64decode(value)
        return default
