"""Streaming scaffold for unified chat."""

import json
from typing import Any, AsyncIterator

from .chat_facade import ChatFacade


class StreamFacade:
    """Emit SSE scaffold events using the unified chat facade."""

    def __init__(self, chat_facade: ChatFacade) -> None:
        self.chat_facade = chat_facade

    async def stream_reply(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        """Yield a minimal SSE sequence compatible with the future unified stream."""
        yield self._event("status", {"phase": "scaffold", "service": "ai-service-v2"})
        response = await self.chat_facade.generate_reply(payload)
        yield self._event(
            "done",
            {
                "response": response["response"],
                "trace_id": response["trace_id"],
                "success": response["success"],
                "migration": response["migration"],
            },
        )

    @staticmethod
    def _event(event: str, data: dict[str, Any]) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
