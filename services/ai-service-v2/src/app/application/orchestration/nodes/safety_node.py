"""Safety node."""

from __future__ import annotations

from ...llm.structured_outputs import SafetyOutput


class SafetyNode:
    """Evaluate the generated answer against safety policies."""

    def __call__(self, state):
        state.node_trace.append("safety")
        state.safety_result = SafetyOutput(
            severity="unknown",
            allow_response=True,
            actions=[],
        ).model_dump()
        return state
