"""Shared API helpers for scaffold responses."""

from typing import Any


def scaffold_payload(route: str, area: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a consistent scaffold response body."""
    payload: dict[str, Any] = {
        "status": "scaffold",
        "service": "ai-service-v2",
        "route": route,
        "area": area,
        "message": "Fluxo ainda nao migrado para o boundary unificado.",
    }
    if extra:
        payload.update(extra)
    return payload
