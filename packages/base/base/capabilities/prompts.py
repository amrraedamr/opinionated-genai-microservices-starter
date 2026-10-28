from collections.abc import Sequence
from types import ModuleType

from fastapi import FastAPI

from base.models.definitions.health import ProbeStatus
from base.models.view_models.health import ProbeResult
from base.services.prompt.loader import PromptLoader


class Prompts:
    """Loads prompt templates and subscribes to distributed reload events."""

    name = "prompts"

    def __init__(self, templates: Sequence[ModuleType] = ()) -> None:
        self._templates = tuple(templates)

    async def astartup(self, app: FastAPI) -> None:
        await PromptLoader().initialize(self._templates)

    async def ashutdown(self, app: FastAPI) -> None:
        await PromptLoader().shutdown()

    async def aprobe(self) -> ProbeResult:
        keys = PromptLoader().list_keys()
        if not keys:
            return ProbeResult(
                name=self.name,
                status=ProbeStatus.DEGRADED,
                detail="No prompts registered.",
            )
        return ProbeResult(
            name=self.name,
            status=ProbeStatus.OK,
            detail=f"{len(keys)} prompts loaded.",
        )
