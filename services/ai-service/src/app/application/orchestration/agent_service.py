"""LangGraph-oriented orchestration service."""

from __future__ import annotations

import time
from datetime import UTC, datetime
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
from ..retrieval.citations import CitationService
from ..retrieval.rag_gateway import RAGGateway
from ..retrieval.retrieval_policy import RetrievalPolicy
from ...services.streaming_utils import SentenceChunker, now_ms
from .graph_state import GraphState
from .nodes.context_node import ContextNode
from .nodes.generation_node import GenerationNode
from .nodes.input_node import InputNode
from .nodes.persistence_node import PersistenceNode
from .nodes.response_node import ResponseNode, resolve_response_text
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
        citation_service: CitationService,
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
        self.voice_synthesis_service = voice_synthesis_service
        self.execution_policy = ExecutionPolicy()
        self.input_node = InputNode()
        self.context_node = ContextNode(
            conversation_repository=conversation_repository,
            user_profile_service=user_profile_service,
            session_context_service=session_context_service,
        )
        self.retrieval_node = RetrievalNode(retrieval_policy, rag_gateway, citation_service)
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
            user_message_id=payload.get("user_message_id"),
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
        """Stream the architecture-first orchestration flow as SSE-ready events."""
        state = self.build_graph_state(
            payload,
            trace_id=payload.get("trace_id") or "trace_graph",
        )
        started_at = time.perf_counter()
        first_text_ms: int | None = None
        first_audio_ms: int | None = None
        audio_events = 0
        native_streaming_used = False
        native_generation_chunks: list[str] = []

        state = self.input_node(state)
        yield self._status_event(state, "input", started_at)

        state = await self.context_node(state)
        yield {
            "event": "meta",
            "data": {
                "trace_id": state.trace_id,
                "session_id": state.session_id,
                "chat_id": state.chat_id,
                "username": state.username,
                "voice": state.selected_voice,
                "voice_enabled": state.voice_enabled,
                "is_voice_mode": state.is_voice_mode,
                "started_at": datetime.now(UTC).isoformat(),
            },
        }
        yield self._status_event(state, "session_context", started_at)

        if self.execution_policy.should_retrieve(state.rag_policy):
            state = await self.retrieval_node(state)
            yield {
                "event": "status",
                "data": {
                    "trace_id": state.trace_id,
                    "node": "retrieval",
                    "elapsed_ms": now_ms(started_at),
                    "retrieved_documents": len((state.retrieval_result or {}).get("results", [])),
                    "warnings": list((state.retrieval_result or {}).get("warnings", [])),
                },
            }

        state.compiled_prompt = await self.prompt_pipeline.build_chat_prompt(state)
        final_generation_output = None
        async for runtime_event in self.runtime_service.stream_generate(state, state.compiled_prompt):
            if runtime_event.get("type") == "delta":
                delta = str(runtime_event.get("delta") or "")
                if delta:
                    native_streaming_used = True
                    native_generation_chunks.append(delta)
            elif runtime_event.get("type") == "final":
                final_generation_output = runtime_event.get("output")
        if final_generation_output is None:
            final_generation_output = await self.runtime_service.generate(state, state.compiled_prompt)
        state.generation_result = final_generation_output.model_dump()
        yield {
            "event": "status",
            "data": {
                "trace_id": state.trace_id,
                "node": "generation",
                "elapsed_ms": now_ms(started_at),
                "provider": (state.generation_result or {}).get("provider", "unconfigured"),
                "model": (state.generation_result or {}).get("model", "unconfigured"),
                "native_streaming": native_streaming_used,
            },
        }

        state = self.safety_node(state)
        yield {
            "event": "status",
            "data": {
                "trace_id": state.trace_id,
                "node": "safety",
                "elapsed_ms": now_ms(started_at),
                "severity": (state.safety_result or {}).get("severity", "unknown"),
                "allow_response": (state.safety_result or {}).get("allow_response", True),
            },
        }

        response_text = resolve_response_text(state).strip()
        text_chunks = self._select_stream_text_chunks(
            state=state,
            response_text=response_text,
            native_generation_chunks=native_generation_chunks,
        )
        for text_chunk in text_chunks:
            if first_text_ms is None:
                first_text_ms = now_ms(started_at)
            yield {
                "event": "text_delta",
                "data": {
                    "trace_id": state.trace_id,
                    "delta": text_chunk,
                    "elapsed_ms": now_ms(started_at),
                },
            }

        async for audio_event in self._stream_audio_events(
            state=state,
            response_text=response_text,
            text_chunks=text_chunks,
            started_at=started_at,
        ):
            if audio_event["event"] in {"audio_chunk", "audio_url"}:
                audio_events += 1
                if first_audio_ms is None:
                    first_audio_ms = now_ms(started_at)
                if audio_event["event"] == "audio_url":
                    state.audio_url = audio_event["data"].get("audio_url") or state.audio_url
            yield audio_event

        state = await self.persistence_node(state)
        yield {
            "event": "status",
            "data": {
                "trace_id": state.trace_id,
                "node": "persistence",
                "elapsed_ms": now_ms(started_at),
                "user_message_id": state.user_message_id,
                "ai_message_id": state.ai_message_id,
                "audio_url": state.audio_url,
            },
        }

        state = self.response_node(state)
        yield self._status_event(state, "response", started_at)
        final_state = state

        yield {
            "event": "metrics",
            "data": {
                "trace_id": state.trace_id,
                "metrics": {
                    "orchestration_total_ms": now_ms(started_at),
                    "first_text_delta_ms": first_text_ms,
                    "first_audio_event_ms": first_audio_ms,
                    "audio_events": audio_events,
                    "native_streaming_used": native_streaming_used,
                    "native_generation_chunks": len(native_generation_chunks),
                },
            },
        }
        yield {
            "event": "done",
            "data": {
                "trace_id": state.trace_id,
                "response": (final_state.final_response or {}).get("response", ""),
                "provider": (final_state.final_response or {}).get("provider", "unconfigured"),
                "model": (final_state.final_response or {}).get("model", "unconfigured"),
                "username": final_state.username,
                "node_trace": final_state.node_trace,
                "warnings": final_state.warnings,
                "session_id": final_state.session_id,
                "chat_id": final_state.chat_id,
                "user_message_id": final_state.user_message_id,
                "ai_message_id": final_state.ai_message_id,
                "audio_url": final_state.audio_url,
                "conversation_ended": final_state.conversation_ended,
                "citations": final_state.citations,
            },
        }

    async def run(self, state: GraphState) -> GraphState:
        """Execute the graph if LangGraph is available, otherwise run sequentially."""
        if self._compiled_graph is not None:
            result = await self._compiled_graph.ainvoke(state)
            return self._coerce_graph_state(result)

        state = self.input_node(state)
        state = await self.context_node(state)
        if self.execution_policy.should_retrieve(state.rag_policy):
            state = await self.retrieval_node(state)
        state = await self.generation_node(state)
        state = self.safety_node(state)
        state = await self.persistence_node(state)
        state = self.response_node(state)
        return state

    def _coerce_graph_state(self, result: Any) -> GraphState:
        """Normalize LangGraph outputs back into the canonical dataclass state."""
        if isinstance(result, GraphState):
            return result

        if isinstance(result, dict):
            state = GraphState(trace_id="trace_graph", session_id="default", username="anonymous")
            for field_name in state.__dataclass_fields__:
                if field_name in result:
                    setattr(state, field_name, result[field_name])
            return state

        raise TypeError(f"Resultado inesperado do grafo: {type(result)!r}")

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

    def _status_event(self, state: GraphState, node_name: str, started_at: float) -> dict[str, Any]:
        return {
            "event": "status",
            "data": {
                "trace_id": state.trace_id,
                "node": node_name,
                "elapsed_ms": now_ms(started_at),
            },
        }

    def _chunk_text_for_stream(self, response_text: str) -> list[str]:
        if not response_text:
            return []

        chunker = SentenceChunker(
            max_chars=220,
            max_wait_ms=450,
            min_timed_flush_chars=32,
            min_timed_flush_words=4,
        )
        chunks = chunker.push(response_text)
        remaining = chunker.flush()
        if remaining:
            chunks.append(remaining)
        return chunks

    async def _stream_audio_events(
        self,
        *,
        state: GraphState,
        response_text: str,
        text_chunks: list[str],
        started_at: float,
    ):
        if not (state.voice_enabled and state.is_voice_mode and response_text):
            return

        sequence = 0
        emitted_audio = False
        tts_stream_failed = False

        for text_chunk in text_chunks:
            chunk_emitted = False
            async for audio_event in self.voice_synthesis_service.stream_tts_chunk(
                text_chunk,
                state.selected_voice,
                state.trace_id,
                sequence,
                started_at,
            ):
                if audio_event["event"] == "audio_chunk":
                    chunk_emitted = True
                    emitted_audio = True
                    sequence += 1
                elif audio_event["event"] == "error":
                    tts_stream_failed = True
                yield audio_event

            if not chunk_emitted:
                audio_url = await self.voice_synthesis_service.generate_audio(
                    text_chunk,
                    state.selected_voice,
                    is_voice_mode=True,
                )
                if audio_url:
                    emitted_audio = True
                    state.audio_url = audio_url
                    yield {
                        "event": "audio_url",
                        "data": {
                            "trace_id": state.trace_id,
                            "audio_url": audio_url,
                            "sequence": sequence,
                            "segment": True,
                            "elapsed_ms": now_ms(started_at),
                        },
                    }
                    sequence += 1

        if not emitted_audio:
            audio_url = await self.voice_synthesis_service.generate_audio(
                response_text,
                state.selected_voice,
                is_voice_mode=True,
            )
            if audio_url:
                state.audio_url = audio_url
                yield {
                    "event": "audio_url",
                    "data": {
                        "trace_id": state.trace_id,
                        "audio_url": audio_url,
                        "sequence": sequence,
                        "segment": False,
                        "elapsed_ms": now_ms(started_at),
                    },
                }
            elif tts_stream_failed:
                yield {
                    "event": "error",
                    "data": {
                        "trace_id": state.trace_id,
                        "stage": "tts_stream",
                        "error": "voice_stream_unavailable",
                        "recoverable": True,
                    },
                }

    def _select_stream_text_chunks(
        self,
        *,
        state: GraphState,
        response_text: str,
        native_generation_chunks: list[str],
    ) -> list[str]:
        generation_text = ((state.generation_result or {}).get("text") or "").strip()
        if (
            native_generation_chunks
            and response_text
            and response_text == generation_text
        ):
            return [chunk for chunk in native_generation_chunks if chunk]
        return self._chunk_text_for_stream(response_text)
