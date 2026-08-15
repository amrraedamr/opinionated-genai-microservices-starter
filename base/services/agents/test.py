from typing import ClassVar

from base.services.agents import AbstractAgent
from base.services.llm import OpenAIMessageAdapter


class TestAgent(AbstractAgent):
    """Test agent for development and debugging."""

    PROMPT_KEY: ClassVar[str] = "test_prompt"
    MAX_OUTPUT_TOKENS: ClassVar[int] = 500

    async def _execute(self) -> None:
        rendered_prompt = self._prompt_service.render(
            self.PROMPT_KEY,
            history=await self._aget_history(),
            user_query=self._execution_context.flow_variables.user_query,
        )
        responses_input = OpenAIMessageAdapter.to_responses_input(
            prompt=rendered_prompt,
        )
        result = await self._llm_service.aresponses(
            responses_input,
            label=type(self).__name__,
            max_output_tokens=self.MAX_OUTPUT_TOKENS,
            stream_iterator=(
                self._execution_context.stream_iterator
                if self._execution_context.streaming
                else None
            ),
        )
        self._execution_context.flow_variables.final_answer = (
            result.content or ""
        ).strip()
