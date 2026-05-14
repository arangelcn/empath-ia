"""Execution policy helpers for the orchestration layer."""


class ExecutionPolicy:
    """Decide which orchestration features are enabled for a request."""

    def should_retrieve(self, rag_policy: dict) -> bool:
        """Return whether retrieval should run for the current request."""
        return bool(rag_policy)
