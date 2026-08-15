import asyncio
import importlib
import pkgutil
from collections.abc import AsyncGenerator

import base.services.prompt.templates as pkg
from base.models.definitions.cache import CacheChannels
from base.models.view_models.prompt import Prompt
from base.services.cache.memory import InMemoryCacheService
from base.services.common.meta import Singleton
from base.services.configuration import settings
from base.services.logging.console import ConsoleLoggerService


class PromptLoader(metaclass=Singleton):
    def __init__(self) -> None:
        self._prompts: dict[str, Prompt] = {}
        self._loading: bool = False
        self._templates_loaded: bool = False
        self._pubsub_reload_task: asyncio.Task[None] | None = None
        self._cache_service: InMemoryCacheService = InMemoryCacheService()
        self._logger: ConsoleLoggerService = ConsoleLoggerService()

    async def initialize(self) -> None:
        """Must be called ONCE at app startup.

        Subscribes to pub/sub for distributed reload events.
        If load_prompts_from_db is enabled, loads DB overrides.
        """
        reload_pubsub: AsyncGenerator[str, None] = self._cache_service.subscribe(
            CacheChannels.PROMPT_RELOAD.value
        )
        self._pubsub_reload_task = asyncio.create_task(
            self.listen_for_reload_events(reload_pubsub)
        )

        # Load all templates from code first, so they're available for DB overrides and in-memory access.
        self.load_templates()
        self._templates_loaded = True

        if settings.load_prompts_from_db:
            await self.load_prompts_from_db()

        self._logger.info(
            "PromptLoader initialized with %d prompts", len(self._prompts)
        )

    async def shutdown(self) -> None:
        """Must be called ONCE at app shutdown.

        Cancels pub/sub listener task.
        """
        if self._pubsub_reload_task:
            self._pubsub_reload_task.cancel()
            self._logger.info("PromptLoader shut down")

    async def listen_for_reload_events(self, pubsub: AsyncGenerator[str, None]) -> None:
        async for _ in pubsub:
            self._logger.info("Received prompt reload event, reloading from DB...")
            await self.load_prompts_from_db()
            self._logger.info("Prompts reloaded")
            await asyncio.sleep(0.1)

    async def load_prompts_from_db(self) -> None:
        # TODO: Implement when DBPromptService is built.
        # Should query ActivePromptDTO joined with PromptDTO,
        # deserialize templates, and call self.override() for each.
        if self._loading:
            return
        self._loading = True
        try:
            pass
        finally:
            self._loading = False

    def load_templates(self) -> None:
        """Import all template modules so @register_prompt decorators fire.

        Must be called ONCE at app startup.
        """
        if self._templates_loaded:
            self._logger.warning("Templates already loaded, skipping")
            return

        for info in pkgutil.walk_packages(pkg.__path__, prefix=f"{pkg.__name__}."):
            importlib.import_module(info.name)

        self._logger.info("Loaded prompt templates: %d", len(self._prompts))

    def register(self, prompt: Prompt) -> None:
        """Register a prompt. Called by the @register_prompt decorator."""
        if prompt.key in self._prompts:
            self._logger.warning(
                "Prompt key %s already registered, overwriting", prompt.key
            )
        self._prompts[prompt.key] = prompt
        self._logger.info("Registered prompt: %s", prompt.key)

    def get(self, key: str) -> Prompt:
        prompt: Prompt | None = self._prompts.get(key)
        if prompt is None:
            raise KeyError(f"Prompt not found: {key}")
        return prompt

    def list_keys(self) -> list[str]:
        return list(self._prompts.keys())

    def override(self, key: str, prompt: Prompt) -> None:
        """Override a prompt (used by DB-backed services for hot-reload)."""
        self._prompts[key] = prompt
        self._logger.info("Prompt overridden: %s", prompt.key)
