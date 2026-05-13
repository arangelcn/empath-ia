"""Response assembly node."""

from __future__ import annotations

from ...llm.structured_outputs import OrchestrationOutput


class ResponseNode:
    """Assemble the final graph output shape."""

    def __call__(self, state):
        state.node_trace.append("response")
        generation = state.generation_result or {}
        final_output = OrchestrationOutput(
            trace_id=state.trace_id,
            response=generation.get("text") or "",
            provider=generation.get("provider", "unconfigured"),
            model=generation.get("model", "unconfigured"),
            execution_mode=state.execution_mode,
            node_trace=state.node_trace,
            warnings=state.warnings,
        )
        state.final_response = final_output.model_dump()
        return state
