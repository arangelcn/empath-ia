"""Client for runtime retrieval calls to the Knowledge Service."""

import logging
import os
from typing import Any, Dict

import httpx


logger = logging.getLogger(__name__)


class RAGClientService:
    """Call the Knowledge Service retrieval endpoint with safe fallbacks."""

    def __init__(self):
        self.knowledge_service_url = os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge-service:8005").rstrip("/")
        self.retrieve_endpoint = f"{self.knowledge_service_url}/api/v1/retrieve"
        self.timeout_seconds = float(os.getenv("KNOWLEDGE_RETRIEVE_TIMEOUT_SECONDS", "8"))

    async def retrieve(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Request retrieval results; degrade safely on transport or payload failures."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.retrieve_endpoint, json=payload)

            if response.status_code != 200:
                logger.warning(
                    "⚠️ Retrieval HTTP error from Knowledge Service: status=%s body=%s",
                    response.status_code,
                    response.text[:400],
                )
                return {
                    "success": False,
                    "results": [],
                    "warnings": [f"knowledge_service_http_{response.status_code}"],
                }

            body = response.json()
            if not isinstance(body, dict):
                logger.warning("⚠️ Retrieval payload is not a JSON object")
                return {"success": False, "results": [], "warnings": ["knowledge_service_invalid_payload"]}

            body.setdefault("success", False)
            body.setdefault("results", [])
            body.setdefault("warnings", [])
            return body

        except httpx.TimeoutException:
            logger.warning("⚠️ Retrieval timeout while calling Knowledge Service")
            return {"success": False, "results": [], "warnings": ["knowledge_service_timeout"]}
        except Exception as exc:
            logger.warning("⚠️ Retrieval transport failure: %s", exc)
            return {"success": False, "results": [], "warnings": ["knowledge_service_unavailable"]}
