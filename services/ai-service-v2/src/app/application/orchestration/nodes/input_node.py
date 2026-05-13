"""Input normalization node for the orchestration graph."""

from __future__ import annotations


class InputNode:
    """Normalize the inbound state before any expensive work happens."""

    def __call__(self, state):
        state.node_trace.append("input")
        if not state.user_message.strip():
            state.errors.append("empty_user_message")
        return state
