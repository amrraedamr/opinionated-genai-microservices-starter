from enum import Enum


class CacheKeys(Enum):
    TEST = "test_cache_key"


class CacheChannels(Enum):
    TEST = "test_channel"
    KEYVAULT_RELOAD = "keyvault_reload"
    LOGS = "logs"

    def for_app(self, app_name: str) -> str:
        return f"{app_name}:{self.value}"
