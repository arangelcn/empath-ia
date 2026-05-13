"""Streaming scaffold for unified chat."""

from __future__ import annotations

import json
from typing import Any, AsyncGenerator, AsyncIterator

from .chat_facade import ChatFacade


class StreamFacade:
    """Emit SSE events using the unified chat facade."""

    def __init__(self, chat_facade: ChatFacade) -> None:
        self.chat_facade = chat_facade

    async def stream_reply(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        """Yield the compatibility streaming sequence for gateway-style endpoints."""
        async for event in self.chat_facade.process_user_message_stream(
            session_id=payload.get("session_id", "default"),
            user_message=payload.get("message", ""),
            session_objective=payload.get("session_objective"),
            is_voice_mode=bool(payload.get("is_voice_mode", False)),
            trace_id=payload.get("trace_id"),
            client_metrics=payload.get("client_metrics"),
        ):
            yield self._event(event["event"], event["data"])

    async def stream_graph_reply(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        """Yield the architecture-first LangGraph streaming sequence."""
        async for event in self.chat_facade.agent_service.stream(payload):
            yield self._event(event["event"], event["data"])

    async def stream_legacy_openai_compat(self, payload: dict[str, Any]) -> AsyncGenerator[str, None]:
        """Yield the legacy `/openai/chat/stream` contract using the new orchestration path."""
        first_text_delta_ms: int | None = None
        total_ms: int | None = None
        trace_id = payload.get("trace_id")

        try:
            async for event in self.chat_facade.agent_service.stream(payload):
                event_name = event["event"]
                data = event["data"]

                if event_name == "text_delta":
                    if first_text_delta_ms is None:
                        first_text_delta_ms = data.get("elapsed_ms")
                    trace_id = data.get("trace_id") or trace_id
                    yield self._event("text_delta", data)
                    continue

                if event_name == "metrics":
                    metrics = data.get("metrics") or {}
                    total_ms = metrics.get("orchestration_total_ms") or total_ms
                    if metrics.get("first_text_delta_ms") is not None:
                        first_text_delta_ms = metrics.get("first_text_delta_ms")
                    trace_id = data.get("trace_id") or trace_id
                    continue

                if event_name == "done":
                    trace_id = data.get("trace_id") or trace_id
                    yield self._event(
                        "done",
                        {
                            "response": data.get("response", ""),
                            "model": data.get("model", "unconfigured"),
                            "provider": data.get("provider", "unconfigured"),
                            "session_id": data.get("session_id") or payload.get("session_id", "default"),
                            "username": data.get("username") or payload.get("username", "anonymous"),
                            "trace_id": trace_id,
                            "metrics": {
                                "ai_total_ms": total_ms,
                                "ai_first_delta_ms": first_text_delta_ms,
                            },
                            "success": True,
                        },
                    )
                    return
        except Exception:
            yield self._event(
                "error",
                {"error": "Erro interno no stream", "trace_id": trace_id},
            )

    @staticmethod
    def _event(event: str, data: dict[str, Any]) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
