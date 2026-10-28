from fastapi import FastAPI

from base.capabilities import BaseCapability
from base.models.definitions.health import ProbeStatus
from base.models.view_models.health import ProbeResult
from base.services.prompt.loader import PromptLoader


class Prompts(BaseCapability):
    """Loads prompt templates and subscribes to distributed reload events."""

    name = "prompts"

    async def startup(self, app: FastAPI) -> None:
        await PromptLoader().initialize()

    async def shutdown(self, app: FastAPI) -> None:
        await PromptLoader().shutdown()

    async def probe(self) -> ProbeResult:
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
