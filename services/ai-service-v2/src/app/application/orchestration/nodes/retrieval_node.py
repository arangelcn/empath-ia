"""Retrieval node."""

from __future__ import annotations


class RetrievalNode:
    """Attach retrieval metadata according to the selected policy."""

    def __init__(self, retrieval_policy, rag_gateway) -> None:
        self.retrieval_policy = retrieval_policy
        self.rag_gateway = rag_gateway

    async def __call__(self, state):
        state.node_trace.append("retrieval")
        policy = self.retrieval_policy.describe(state.rag_policy)
        state.retrieval_result = {
            "policy": policy,
            "gateway": self.rag_gateway.describe(),
            "documents": [],
        }
        return state
