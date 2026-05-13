"""HTTP client adapters for legacy services used during migration."""

from __future__ import annotations

import json
from typing import Any, AsyncGenerator

import httpx


class LegacyAIClient:
    """Bridge to the current ai-service during the migration."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Call the legacy non-streaming AI endpoint."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    async def stream_chat(self, payload: dict[str, Any]) -> AsyncGenerator[dict[str, Any], None]:
        """Consume the legacy SSE stream and yield parsed events."""
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/openai/chat/stream",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                response.raise_for_status()
                current_event = "message"
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                        continue
                    if not line.startswith("data:"):
                        continue
                    payload_data = json.loads(line.split(":", 1)[1].strip() or "{}")
                    yield {"event": current_event, "data": payload_data}


class LegacyGatewayClient:
    """Bridge to legacy gateway paths not yet migrated, like session-1 registration."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def send_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Delegate the request to the legacy gateway send endpoint."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat/send",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    async def stream_message(self, payload: dict[str, Any]) -> AsyncGenerator[dict[str, Any], None]:
        """Delegate a streaming request to the legacy gateway."""
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat/send-stream",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                response.raise_for_status()
                current_event = "message"
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                        continue
                    if not line.startswith("data:"):
                        continue
                    payload_data = json.loads(line.split(":", 1)[1].strip() or "{}")
                    yield {"event": current_event, "data": payload_data}
