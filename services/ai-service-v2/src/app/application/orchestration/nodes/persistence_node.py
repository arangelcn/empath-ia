"""Persistence planning node."""

from __future__ import annotations


class PersistenceNode:
    """Plan persistence side effects without coupling the graph to transport."""

    def __call__(self, state):
        state.node_trace.append("persistence")
        state.persistence_plan = {
            "save_user_message": True,
            "save_ai_message": True,
            "update_message_count": True,
            "generate_session_context_async": False,
        }
        return state
