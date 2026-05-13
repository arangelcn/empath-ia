"""LangGraph-oriented orchestration service."""

from __future__ import annotations

from typing import Any

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - optional dependency in scaffold phase
    END = "__end__"
    START = "__start__"
    StateGraph = None

from ..llm.fallback_service import FallbackService
from ..llm.prompt_pipeline import PromptPipeline
from ..llm.runtime_service import RuntimeService
from ..retrieval.rag_gateway import RAGGateway
from ..retrieval.retrieval_policy import RetrievalPolicy
from .graph_state import GraphState
from .nodes.context_node import ContextNode
from .nodes.generation_node import GenerationNode
from .nodes.input_node import InputNode
from .nodes.persistence_node import PersistenceNode
from .nodes.response_node import ResponseNode
from .nodes.retrieval_node import RetrievalNode
from .nodes.safety_node import SafetyNode
from .policies.execution_policy import ExecutionPolicy


class AgentService:
    """Owner for chat orchestration inside the unified monolith."""

    def __init__(
        self,
        prompt_pipeline: PromptPipeline,
        retrieval_policy: RetrievalPolicy,
        rag_gateway: RAGGateway,
        runtime_service: RuntimeService,
        fallback_service: FallbackService,
        conversation_repository,
        user_profile_service,
        session_context_service,
        voice_synthesis_service,
    ) -> None:
        self.prompt_pipeline = prompt_pipeline
        self.retrieval_policy = retrieval_policy
        self.rag_gateway = rag_gateway
        self.runtime_service = runtime_service
        self.fallback_service = fallback_service
        self.execution_policy = ExecutionPolicy()
        self.input_node = InputNode()
        self.context_node = ContextNode(
            conversation_repository=conversation_repository,
            user_profile_service=user_profile_service,
            session_context_service=session_context_service,
        )
        self.retrieval_node = RetrievalNode(retrieval_policy, rag_gateway)
        self.generation_node = GenerationNode(prompt_pipeline, runtime_service)
        self.safety_node = SafetyNode()
        self.persistence_node = PersistenceNode(
            conversation_repository=conversation_repository,
            voice_synthesis_service=voice_synthesis_service,
            session_context_service=session_context_service,
        )
        self.response_node = ResponseNode()
        self._compiled_graph = self._build_graph()

    def build_graph_state(self, payload: dict[str, Any], trace_id: str) -> GraphState:
        """Normalize incoming request data into the canonical graph state."""
        return GraphState(
            trace_id=trace_id,
            session_id=payload.get("session_id", "default"),
            username=payload.get("username", "anonymous"),
            chat_id=payload.get("chat_id"),
            user_message=payload.get("message", ""),
            conversation_history=payload.get("conversation_history") or [],
            user_profile=payload.get("user_profile") or {},
            previous_session_context=payload.get("previous_session_context"),
            session_objective=payload.get("session_objective"),
            initial_prompt=payload.get("initial_prompt"),
            prompt_key=payload.get("prompt_key"),
            rag_policy=payload.get("rag_policy") or {},
            is_voice_mode=bool(payload.get("is_voice_mode", False)),
        )

    def plan(self, state: GraphState) -> dict[str, Any]:
        """Return the execution plan for the graph."""
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
            "langgraph_available": StateGraph is not None,
        }

    async def chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Run the graph and return the final structured response."""
        state = self.build_graph_state(
            payload,
            trace_id=payload.get("trace_id") or "trace_graph",
        )
        final_state = await self.run(state)
        if final_state.final_response:
            return final_state.final_response
        return {
            "response": "",
            "provider": "unconfigured",
            "model": "unconfigured",
            "trace_id": final_state.trace_id,
            "session_id": final_state.session_id,
            "username": final_state.username,
            "chat_id": final_state.chat_id,
            "node_trace": final_state.node_trace,
            "warnings": final_state.warnings,
        }

    async def stream(self, payload: dict[str, Any]):
        """Stream graph progress events for inspection and future UI streaming."""
        state = self.build_graph_state(
            payload,
            trace_id=payload.get("trace_id") or "trace_graph",
        )
        yield {"event": "status", "data": {"trace_id": state.trace_id, "node": "input"}}
        final_state = await self.run(state)
        for node_name in final_state.node_trace:
            yield {"event": "status", "data": {"trace_id": state.trace_id, "node": node_name}}
        yield {
            "event": "done",
            "data": {
                "trace_id": state.trace_id,
                "response": (final_state.final_response or {}).get("response", ""),
                "provider": (final_state.final_response or {}).get("provider", "unconfigured"),
                "model": (final_state.final_response or {}).get("model", "unconfigured"),
                "node_trace": final_state.node_trace,
                "warnings": final_state.warnings,
                "session_id": final_state.session_id,
                "chat_id": final_state.chat_id,
                "ai_message_id": final_state.ai_message_id,
            },
        }

    async def run(self, state: GraphState) -> GraphState:
        """Execute the graph if LangGraph is available, otherwise run sequentially."""
        if self._compiled_graph is not None:
            return await self._compiled_graph.ainvoke(state)

        state = self.input_node(state)
        state = self.context_node(state)
        if self.execution_policy.should_retrieve(state.rag_policy):
            state = await self.retrieval_node(state)
        state = await self.generation_node(state)
        state = self.safety_node(state)
        state = self.persistence_node(state)
        state = self.response_node(state)
        return state

    def _build_graph(self):
        """Compile the LangGraph state machine when available."""
        if StateGraph is None:
            return None

        graph = StateGraph(GraphState)
        graph.add_node("input", self.input_node)
        graph.add_node("session_context", self.context_node)
        graph.add_node("retrieval", self.retrieval_node)
        graph.add_node("generation", self.generation_node)
        graph.add_node("safety", self.safety_node)
        graph.add_node("persistence", self.persistence_node)
        graph.add_node("response", self.response_node)

        graph.add_edge(START, "input")
        graph.add_edge("input", "session_context")
        graph.add_conditional_edges(
            "session_context",
            self._next_after_context,
            {"retrieval": "retrieval", "generation": "generation"},
        )
        graph.add_edge("retrieval", "generation")
        graph.add_edge("generation", "safety")
        graph.add_edge("safety", "persistence")
        graph.add_edge("persistence", "response")
        graph.add_edge("response", END)
        return graph.compile()

    def _next_after_context(self, state: GraphState) -> str:
        """Route to retrieval only when the execution policy enables it."""
        return "retrieval" if self.execution_policy.should_retrieve(state.rag_policy) else "generation"
