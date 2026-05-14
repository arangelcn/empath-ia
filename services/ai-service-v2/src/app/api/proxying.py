"""Shared HTTP proxy helpers for temporary edge compatibility."""

from __future__ import annotations

from typing import Mapping

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import Response


HOP_BY_HOP_HEADERS = {
    "connection",
    "content-length",
    "host",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


async def proxy_request(
    request: Request,
    upstream_base_url: str,
    *,
    path_override: str | None = None,
    extra_headers: Mapping[str, str] | None = None,
    timeout: float = 120.0,
) -> Response:
    """Forward the current request to an upstream HTTP service."""
    target_path = path_override or request.url.path
    target_url = f"{upstream_base_url.rstrip('/')}{target_path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }
    if extra_headers:
        headers.update(extra_headers)

    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream_response = await client.request(
                request.method,
                target_url,
                content=body,
                headers=headers,
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Servico upstream indisponivel: {exc}",
        ) from exc

    response_headers = {
        key: value
        for key, value in upstream_response.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
        media_type=upstream_response.headers.get("content-type"),
    )
