"""Retrieval policy scaffold."""

from typing import Any


class RetrievalPolicy:
    """Future owner for retrieval policy normalization."""

    def describe(self, rag_policy: dict[str, Any]) -> dict[str, Any]:
        """Return the retrieval policy preview used by the scaffold."""
        return {
            "owner": "application.retrieval.retrieval_policy",
            "enabled": bool(rag_policy),
            "raw_policy": rag_policy,
        }
