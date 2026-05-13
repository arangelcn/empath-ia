"""Agent orchestration scaffold."""

from typing import Any

from ..llm.fallback_service import FallbackService
from ..llm.prompt_pipeline import PromptPipeline
from ..llm.runtime_service import RuntimeService
from ..retrieval.rag_gateway import RAGGateway
from ..retrieval.retrieval_policy import RetrievalPolicy
from .graph_state import GraphState


class AgentService:
    """Planned owner for chat orchestration inside the unified monolith."""

    def __init__(
        self,
        prompt_pipeline: PromptPipeline,
        retrieval_policy: RetrievalPolicy,
        rag_gateway: RAGGateway,
        runtime_service: RuntimeService,
        fallback_service: FallbackService,
    ) -> None:
        self.prompt_pipeline = prompt_pipeline
        self.retrieval_policy = retrieval_policy
        self.rag_gateway = rag_gateway
        self.runtime_service = runtime_service
        self.fallback_service = fallback_service

    def build_graph_state(self, payload: dict[str, Any], trace_id: str) -> GraphState:
        """Normalize incoming request data into the canonical graph state."""
        return GraphState(
            trace_id=trace_id,
            session_id=payload.get("session_id", "default"),
            username=payload.get("username", "anonymous"),
            chat_id=payload.get("chat_id"),
            user_message=payload.get("message", ""),
            prompt_key=payload.get("prompt_key"),
            rag_policy=payload.get("rag_policy") or {},
            is_voice_mode=bool(payload.get("is_voice_mode", False)),
        )

    def plan(self, state: GraphState) -> dict[str, Any]:
        """Return the initial execution plan for the scaffold."""
        return {
            "owner": "application.orchestration.agent_service",
            "planned_nodes": [
                "input",
                "session_context",
                "retrieval",
                "generation",
                "safety",
                "persistence",
                "response",
            ],
            "prompt_pipeline": self.prompt_pipeline.describe(state.prompt_key),
            "retrieval_policy": self.retrieval_policy.describe(state.rag_policy),
            "rag_gateway": self.rag_gateway.describe(),
            "runtime": self.runtime_service.describe(),
            "fallback": self.fallback_service.describe(),
        }
