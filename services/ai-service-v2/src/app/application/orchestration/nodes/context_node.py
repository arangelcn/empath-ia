"""Session context assembly node."""

from __future__ import annotations


class ContextNode:
    """Gather and attach session context to the graph state."""

    def __call__(self, state):
        state.node_trace.append("session_context")
        if state.previous_session_context is None:
            state.warnings.append("previous_session_context_missing")
        return state
