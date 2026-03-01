import base64
import json

from base.services.configuration.keyvault_config_loader import KeyvaultConfigLoader


class KeyvaultConfig:
    _keyvault_config_loader: KeyvaultConfigLoader = KeyvaultConfigLoader()

    @staticmethod
    def get(key: str, default: str = "") -> str:
        return KeyvaultConfig._keyvault_config_loader.get(key, default)

    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        value = KeyvaultConfig.get(key)
        return int(value) if value else default

    @staticmethod
    def get_float(key: str, default: float = 0.0) -> float:
        value = KeyvaultConfig.get(key)
        return float(value) if value else default

    @staticmethod
    def get_boolean(key: str, default: bool = False) -> bool:
        value = KeyvaultConfig.get(key)
        return value.lower() in ("true", "1", "yes") if value else default

    @staticmethod
    def get_dict(key: str, default: dict = {}) -> dict:
        value = KeyvaultConfig.get(key)
        return json.loads(value) if value else default

    @staticmethod
    def get_bytes(key: str, default: bytes = b"") -> bytes:
        value = KeyvaultConfig.get(key)
        if value:
            # This decodes the base64 string to bytes
            return base64.urlsafe_b64decode(value)
        return default
