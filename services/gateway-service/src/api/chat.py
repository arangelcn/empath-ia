"""Core chat routes."""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..services.chat_service import ChatService
from ..services.streaming_utils import sse_event


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])
chat_service = ChatService()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    session_objective: Optional[Dict[str, Any]] = None
    is_voice_mode: Optional[bool] = False
    client_metrics: Optional[Dict[str, Any]] = None


class ConversationRequest(BaseModel):
    session_id: str
    username: Optional[str] = None
    therapeutic_session_id: Optional[str] = None


@router.post("/send")
async def send_message(request: ChatRequest):
    """Enviar mensagem e receber resposta com persistência"""
    try:
        logger.info(
            "🌐 GATEWAY: Recebendo mensagem para session_id=%s, VoiceMode=%s",
            request.session_id,
            request.is_voice_mode,
        )

        result = await chat_service.process_user_message(
            session_id=request.session_id or "default",
            user_message=request.message,
            session_objective=request.session_objective,
            is_voice_mode=request.is_voice_mode,
        )

        logger.info("✅ GATEWAY: Processamento concluído com sucesso para session_id=%s", request.session_id)
        return result

    except Exception as exc:
        logger.error("❌ GATEWAY: Erro ao processar mensagem: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.post("/send-stream")
async def send_message_stream(request: ChatRequest):
    """
    Enviar mensagem no modo voz com resposta SSE.
    Mantém /api/chat/send intacto e usa fallback de áudio MP3 quando streaming TTS falha.
    """
    trace_id = f"trace_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
    logger.info(
        "🌐 GATEWAY STREAM: session_id=%s VoiceMode=%s trace_id=%s",
        request.session_id,
        request.is_voice_mode,
        trace_id,
    )

    async def event_stream():
        async for item in chat_service.process_user_message_stream(
            session_id=request.session_id or "default",
            user_message=request.message,
            session_objective=request.session_objective,
            is_voice_mode=True,
            trace_id=trace_id,
            client_metrics=request.client_metrics,
        ):
            yield sse_event(item["event"], item["data"])

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Trace-Id": trace_id,
        },
    )


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Obter histórico completo de uma conversa"""
    try:
        history = await chat_service.get_conversation_history(session_id)
        return {"success": True, "data": history}
    except Exception as exc:
        logger.error("Erro ao obter histórico: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.post("/start")
async def start_conversation(request: ConversationRequest):
    """Iniciar ou recuperar conversa existente"""
    try:
        conversation = await chat_service.start_or_get_conversation(
            request.session_id,
            username=request.username,
            therapeutic_session_id=request.therapeutic_session_id,
        )
        return {"success": True, "data": conversation}
    except Exception as exc:
        logger.error("Erro ao iniciar conversa: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.get("/conversations")
async def list_conversations(limit: int = 10):
    """Listar conversas recentes"""
    try:
        conversations = await chat_service.list_recent_conversations(limit)
        return {
            "success": True,
            "data": {
                "conversations": conversations,
                "total": len(conversations),
            },
        }
    except Exception as exc:
        logger.error("Erro ao listar conversas: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc
