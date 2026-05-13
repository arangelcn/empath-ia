"""Streaming scaffold for unified chat."""

import json
from typing import Any, AsyncIterator

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

    @staticmethod
    def _event(event: str, data: dict[str, Any]) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
