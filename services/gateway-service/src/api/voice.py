"""Voice Service proxy routes."""

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from ..config import SERVICE_URLS


router = APIRouter(prefix="/api/voice", tags=["Voice"])


def _rewrite_audio_url(data: dict) -> dict:
    """Reescreve audio_url para usar o proxy do gateway, acessível pelo browser."""
    audio_url = data.get("audio_url")
    if audio_url and "/api/v1/audio/" in audio_url:
        filename = audio_url.split("/api/v1/audio/")[-1]
        data["audio_url"] = f"/api/voice/audio/{filename}"
    return data


@router.post("/speak")
async def voice_speak(request: Request):
    """Text-to-speech através do voice service"""
    body = await request.json()

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['voice']}/api/v1/synthesize",
                json=body,
                timeout=30,
            )

            if response.status_code == 200:
                return _rewrite_audio_url(response.json())
            raise HTTPException(status_code=response.status_code, detail=response.text)

        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Serviço Voice indisponível: {str(exc)}") from exc


@router.post("/synthesize")
async def voice_synthesize(request: Request):
    """Text-to-speech via voice service"""
    body = await request.json()

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['voice']}/api/v1/synthesize",
                json=body,
                timeout=30,
            )

            if response.status_code == 200:
                return _rewrite_audio_url(response.json())
            raise HTTPException(status_code=response.status_code, detail=response.text)

        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Serviço Voice indisponível: {str(exc)}") from exc


@router.get("/health")
async def voice_health():
    """Status do voice service F5-TTS"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICE_URLS['voice']}/health", timeout=10)
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Serviço Voice indisponível: {str(exc)}") from exc


@router.get("/config")
async def voice_config():
    """Obter configurações do voice service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICE_URLS['voice']}/api/v1/model-info", timeout=10)
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Serviço Voice indisponível: {str(exc)}") from exc


@router.get("/models")
async def voice_models():
    """Listar modelos de TTS disponíveis (F5-TTS)"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICE_URLS['voice']}/api/v1/model-info", timeout=10)
            model_info = response.json()
            return {
                "available_models": {
                    model_info.get("model_name", "F5-TTS-pt-br"): model_info,
                },
                "current_model": model_info.get("model_name", "F5-TTS-pt-br"),
                "descriptions": {
                    model_info.get("model_name", "F5-TTS-pt-br"): "F5-TTS Português Brasileiro",
                },
            }
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Serviço Voice indisponível: {str(exc)}") from exc


@router.get("/audio/{filename}")
async def voice_audio(filename: str):
    """Servir arquivos de áudio gerados pelo voice service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICE_URLS['voice']}/api/v1/audio/{filename}", timeout=30)

            if response.status_code == 200:
                media_type = response.headers.get("content-type", "audio/mpeg")
                return Response(
                    content=response.content,
                    media_type=media_type,
                    headers={"Content-Disposition": f"inline; filename={filename}"},
                )
            raise HTTPException(status_code=response.status_code, detail="Arquivo não encontrado")

        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Serviço Voice indisponível: {str(exc)}") from exc
