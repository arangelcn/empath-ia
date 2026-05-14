"""RAG gateway implementation."""

from __future__ import annotations

from typing import Any

import httpx


class RAGGateway:
    """Adapter for retrieval requests to the knowledge boundary."""

    def __init__(self, knowledge_service_url: str) -> None:
        self.knowledge_service_url = knowledge_service_url.rstrip("/")

    async def retrieve(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Call the knowledge-service retrieval endpoint."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.knowledge_service_url}/api/v1/retrieve",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
                if isinstance(data, dict) and "success" in data:
                    return self._normalize_response(data)
                return self._empty_response("invalid_retrieval_response")
        except httpx.HTTPStatusError as exc:
            return self._empty_response(
                f"retrieval_http_{exc.response.status_code}",
                status_code=exc.response.status_code,
            )
        except httpx.TimeoutException:
            return self._empty_response("retrieval_timeout")
        except Exception as exc:
            return self._empty_response(f"retrieval_failed:{type(exc).__name__}")

    def describe(self) -> dict[str, object]:
        """Describe the retrieval gateway."""
        return {
            "owner": "application.retrieval.rag_gateway",
            "status": "http-adapter",
            "knowledge_service_url": self.knowledge_service_url,
        }

    def _normalize_response(self, data: dict[str, Any]) -> dict[str, Any]:
        results = data.get("results")
        warnings = data.get("warnings")
        return {
            "success": bool(data.get("success")),
            "index_version": data.get("index_version"),
            "results": results if isinstance(results, list) else [],
            "warnings": warnings if isinstance(warnings, list) else [],
        }

    def _empty_response(
        self,
        warning: str,
        *,
        status_code: int | None = None,
    ) -> dict[str, Any]:
        payload = {
            "success": False,
            "index_version": None,
            "results": [],
            "warnings": [warning],
        }
        if status_code is not None:
            payload["status_code"] = status_code
        return payload
