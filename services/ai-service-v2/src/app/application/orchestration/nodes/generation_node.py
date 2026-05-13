"""Generation node."""

from __future__ import annotations


class GenerationNode:
    """Compile the prompt and ask the runtime for a response."""

    def __init__(self, prompt_pipeline, runtime_service) -> None:
        self.prompt_pipeline = prompt_pipeline
        self.runtime_service = runtime_service

    async def __call__(self, state):
        state.node_trace.append("generation")
        state.compiled_prompt = await self.prompt_pipeline.build_chat_prompt(state)
        state.generation_result = (
            await self.runtime_service.generate(state, state.compiled_prompt)
        ).model_dump()
        return state
