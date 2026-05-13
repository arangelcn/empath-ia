"""HTTP client adapters for legacy services used during migration."""

from __future__ import annotations

from typing import Any

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
