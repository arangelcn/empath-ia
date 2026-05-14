"""Retrieval node."""

from __future__ import annotations


class RetrievalNode:
    """Attach retrieval metadata according to the selected policy."""

    def __init__(self, retrieval_policy, rag_gateway, citation_service) -> None:
        self.retrieval_policy = retrieval_policy
        self.rag_gateway = rag_gateway
        self.citation_service = citation_service

    async def __call__(self, state):
        state.node_trace.append("retrieval")
        policy = self.retrieval_policy.describe(state.rag_policy)
        if not policy["enabled"]:
            state.retrieval_result = {
                "success": True,
                "policy": policy,
                "gateway": self.rag_gateway.describe(),
                "results": [],
                "warnings": ["retrieval_skipped"],
            }
            state.citations = []
            return state
        if not policy["allowed_scopes"]:
            state.retrieval_result = {
                "success": False,
                "policy": policy,
                "gateway": self.rag_gateway.describe(),
                "results": [],
                "warnings": ["retrieval_skipped_no_scopes"],
            }
            state.citations = []
            state.warnings.append("retrieval_skipped_no_scopes")
            return state

        retrieval_payload = {
            "query": state.user_message,
            "chat_id": state.chat_id,
            "prompt_key": state.prompt_key or "system_rogers",
            "prompt_version": 1,
            "allowed_scopes": policy["allowed_scopes"],
            "language": policy["language"],
            "top_k": policy["top_k"],
            "trace_id": state.trace_id,
        }
        response = await self.rag_gateway.retrieve(retrieval_payload)
        raw_results = response.get("results", [])
        filtered_results = self.citation_service.filter_results(
            raw_results,
            policy["min_confidence"],
        )
        warnings = list(response.get("warnings", []))
        if raw_results and not filtered_results:
            warnings.append("retrieval_filtered_by_min_confidence")
        if response.get("success") and not filtered_results:
            warnings.append("retrieval_empty")
        state.retrieval_result = {
            "success": bool(response.get("success")),
            "index_version": response.get("index_version"),
            "policy": policy,
            "gateway": self.rag_gateway.describe(),
            "results": filtered_results,
            "warnings": warnings,
        }
        state.citations = self.citation_service.format_results(state.retrieval_result)
        for warning in warnings:
            if warning not in state.warnings:
                state.warnings.append(warning)
        return state
