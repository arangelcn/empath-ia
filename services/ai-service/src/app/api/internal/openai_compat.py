"""Legacy ai-service compatibility routes exposed by ai-service."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ...bootstrap.dependencies import AppContainer, get_container


router = APIRouter(prefix="/openai", tags=["openai-compat"])


class LegacyOpenAIChatRequest(BaseModel):
    """Request shape currently sent by the gateway to ai-service."""

    message: str
    session_id: str = "default"
    username: str
    user_profile: dict[str, Any] | None = None
    conversation_history: list[dict[str, Any]] | None = None
    session_objective: dict[str, Any] | None = None
    initial_prompt: str | None = None
    previous_session_context: dict[str, Any] | None = None
    rag_policy: dict[str, Any] | None = None
    prompt_key: str | None = None
    prompt_version: int | None = None
    chat_id: str | None = None
    is_voice_mode: bool = False
    trace_id: str | None = None
    rag_language: str | None = None


@router.post("/chat")
async def chat(
    request: LegacyOpenAIChatRequest,
    container: AppContainer = Depends(get_container),
) -> dict[str, Any]:
    """Expose the legacy non-streaming ai-service contract via the new boundary."""
    try:
        return await container.chat_facade.generate_legacy_compat_reply(request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from exc


@router.post("/chat/stream")
async def stream_chat(
    request: LegacyOpenAIChatRequest,
    container: AppContainer = Depends(get_container),
) -> StreamingResponse:
    """Expose the legacy streaming ai-service contract via the new boundary."""

    return StreamingResponse(
        container.stream_facade.stream_legacy_openai_compat(request.model_dump()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
