"""Emotion Service proxy and user emotion query routes."""

import logging
from typing import Optional

import httpx
from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from ..config import SERVICE_URLS
from ..services.chat_service import ChatService
from ..services.user_emotion_service import UserEmotionService


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Emotions"])
chat_service = ChatService()
user_emotion_service = UserEmotionService()


@router.post("/api/emotion/analyze-face")
async def emotion_analyze_face(file: UploadFile = File(...)):
    """Proxy para análise facial"""
    async with httpx.AsyncClient() as client:
        try:
            files = {"file": (file.filename, await file.read(), file.content_type)}
            response = await client.post(
                f"{SERVICE_URLS['emotion']}/analyze-facial-expression",
                files=files,
                timeout=30,
            )
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Serviço Emotion indisponível: {str(exc)}") from exc


@router.post("/api/emotion/analyze-video")
async def emotion_analyze_video(file: UploadFile = File(...)):
    """Proxy para análise de vídeo emocional"""
    async with httpx.AsyncClient() as client:
        try:
            files = {"file": (file.filename, await file.read(), file.content_type)}
            response = await client.post(
                f"{SERVICE_URLS['emotion']}/analyze-video",
                files=files,
                timeout=60,
            )
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Serviço Emotion indisponível: {str(exc)}") from exc


@router.post("/api/emotion/analyze-realtime")
async def emotion_analyze_realtime(request: Request):
    """Proxy para análise emocional em tempo real (Base64) com salvamento assíncrono"""
    body = await request.json()

    username = body.get("username")
    session_id = body.get("session_id")
    chat_id = None
    therapeutic_session_id = None
    if session_id:
        identity = await chat_service.resolve_conversation_ref(session_id)
        chat_id = identity.get("chat_id")
        session_id = identity.get("legacy_session_id") or session_id
        therapeutic_session_id = identity.get("therapeutic_session_id")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['emotion']}/analyze-realtime",
                json=body,
                timeout=30,
            )

            emotion_result = response.json()

            if emotion_result.get("status") == "success" and username and session_id:
                emotion_data = {
                    "username": username,
                    "chat_id": chat_id,
                    "session_id": session_id,
                    "therapeutic_session_id": therapeutic_session_id,
                    "dominant_emotion": emotion_result.get("dominant_emotion"),
                    "emotions": emotion_result.get("emotions", {}),
                    "confidence": emotion_result.get("confidence", 0),
                    "face_detected": emotion_result.get("face_detected", False),
                }

                await user_emotion_service.save_emotion_async(emotion_data)
                logger.info(
                    "🎭 Emoção detectada e agendada para salvamento: %s - %s",
                    username,
                    emotion_result.get("dominant_emotion"),
                )

            return emotion_result

        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Serviço Emotion indisponível: {str(exc)}") from exc


@router.get("/api/emotions/{username}")
async def get_user_emotions(
    username: str,
    session_id: Optional[str] = None,
    limit: int = 100,
    hours_back: int = 24,
):
    """Obter emoções de um usuário"""
    try:
        emotions = await user_emotion_service.get_user_emotions(
            username=username,
            session_id=session_id,
            limit=limit,
            hours_back=hours_back,
        )

        return {
            "success": True,
            "data": {
                "username": username,
                "session_id": session_id,
                "emotions": emotions,
                "total": len(emotions),
                "hours_back": hours_back,
            },
        }

    except Exception as exc:
        logger.error("❌ Erro ao buscar emoções: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/api/emotions/{username}/summary")
async def get_user_emotion_summary(
    username: str,
    session_id: Optional[str] = None,
    hours_back: int = 24,
):
    """Obter resumo das emoções de um usuário"""
    try:
        summary = await user_emotion_service.get_emotion_summary(
            username=username,
            session_id=session_id,
            hours_back=hours_back,
        )

        return {
            "success": True,
            "data": {
                "username": username,
                "session_id": session_id,
                **summary,
            },
        }

    except Exception as exc:
        logger.error("❌ Erro ao calcular resumo de emoções: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/api/emotions/{username}/timeline")
async def get_user_emotion_timeline(
    username: str,
    session_id: Optional[str] = None,
    hours_back: int = 24,
    interval_minutes: int = 5,
):
    """Obter timeline de emoções de um usuário"""
    try:
        timeline = await user_emotion_service.get_emotion_timeline(
            username=username,
            session_id=session_id,
            hours_back=hours_back,
            interval_minutes=interval_minutes,
        )

        return {
            "success": True,
            "data": {
                "username": username,
                "session_id": session_id,
                "timeline": timeline,
                "hours_back": hours_back,
                "interval_minutes": interval_minutes,
            },
        }

    except Exception as exc:
        logger.error("❌ Erro ao gerar timeline de emoções: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
