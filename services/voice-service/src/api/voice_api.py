"""
Voice API - Endpoints para síntese de voz usando Google Cloud Text-to-Speech API
Documentação oficial: https://cloud.google.com/text-to-speech/docs/quickstart-client-libraries
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, File, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from ..services.gcp_tts_service import GCPTextToSpeechService

logger = logging.getLogger(__name__)

# Inicializar serviço
voice_service = GCPTextToSpeechService()

# Router
router = APIRouter(prefix="/api/v1", tags=["voice"])

# Modelos Pydantic
class SpeakRequest(BaseModel):
    text: str = Field(..., description="Texto para sintetizar", min_length=1, max_length=5000)
    voice_name: Optional[str] = Field(None, description="Nome da voz (ex: pt-BR-Wavenet-A)")
    language_code: Optional[str] = Field("pt-BR", description="Código do idioma")
    speaking_rate: float = Field(1.0, description="Velocidade da fala (0.25 a 4.0)", ge=0.25, le=4.0)
    pitch: float = Field(0.0, description="Tom da voz (-20.0 a 20.0)", ge=-20.0, le=20.0)
    volume_gain_db: float = Field(0.0, description="Ganho de volume (-96.0 a 16.0)", ge=-96.0, le=16.0)

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    model_info: Dict[str, Any]

class SpeakResponse(BaseModel):
    success: bool
    message: str
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    voice_used: Optional[str] = None

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Verificar status do serviço de voz
    """
    try:
        from datetime import datetime
        
        model_info = voice_service.get_model_info()
        
        return HealthResponse(
            status="healthy",
            service="voice-service-gcp",
            timestamp=datetime.now().isoformat(),
            model_info=model_info
        )
    except Exception as e:
        logger.error(f"❌ Erro no health check: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no health check: {str(e)}")

@router.post("/speak", response_model=SpeakResponse)
async def text_to_speech(request: SpeakRequest):
    """
    Converter texto em áudio usando Google Cloud Text-to-Speech
    """
    try:
        logger.info(f"🎙️ Recebida solicitação TTS para texto: '{request.text[:50]}...'")
        
        success, message, audio_url, duration = voice_service.text_to_speech(
            text=request.text,
            voice_name=request.voice_name,
            language_code=request.language_code,
            speaking_rate=request.speaking_rate,
            pitch=request.pitch,
            volume_gain_db=request.volume_gain_db
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)

        return SpeakResponse(
            success=success,
            message=message,
            audio_url=audio_url,
            duration=duration,
            voice_used=request.voice_name or voice_service.default_voice_name
        )
        
    except HTTPException as e:
        logger.error(f"❌ Erro na API TTS: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Erro inesperado na síntese: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor durante a síntese.")

@router.post("/synthesize-stream")
async def synthesize_text_stream(request: SpeakRequest):
    """
    Sintetizar áudio em streaming usando Google Cloud Chirp 3 HD.
    Retorna PCM/LINEAR16 em chunks para reprodução via AudioContext no frontend.
    """
    try:
        if not voice_service.is_streaming_supported():
            raise HTTPException(
                status_code=503,
                detail="Streaming TTS indisponível; use síntese batch como fallback.",
            )

        def audio_stream():
            try:
                yield from voice_service.stream_text_to_speech(
                    text=request.text,
                    voice_name=request.voice_name,
                    language_code=request.language_code,
                )
            except Exception as exc:
                logger.error("❌ Erro durante streaming TTS: %s", exc, exc_info=True)
                raise

        streaming_voice = voice_service.map_to_streaming_voice(request.voice_name)
        return StreamingResponse(
            audio_stream(),
            media_type="audio/L16; rate=24000; channels=1",
            headers={
                "Cache-Control": "no-cache",
                "X-Audio-Encoding": voice_service.streaming_audio_encoding,
                "X-Audio-Sample-Rate": str(voice_service.streaming_sample_rate_hertz),
                "X-Voice-Used": streaming_voice,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro inesperado no streaming de síntese: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor durante streaming de síntese.")

@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """
    Obter arquivo de áudio gerado
    """
    try:
        # Validar nome do arquivo
        if not (filename.endswith('.mp3') or filename.endswith('.wav')) or not filename.startswith('output_'):
            raise HTTPException(status_code=400, detail="Nome de arquivo inválido")
        
        # Construir caminho do arquivo
        file_path = os.path.join(voice_service.output_dir, filename)
        
        # Verificar se arquivo existe
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        # Retornar arquivo
        media_type = "audio/wav" if filename.endswith(".wav") else "audio/mpeg"
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao obter arquivo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter arquivo: {str(e)}")

@router.get("/voices")
async def get_available_voices():
    """
    Listar vozes disponíveis
    """
    try:
        voices = voice_service.get_available_voices()
        return {
            "available_voices": voices,
            "default_voice": voice_service.default_voice_name,
            "language_code": voice_service.default_language_code
        }
    except Exception as e:
        logger.error(f"❌ Erro ao listar vozes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar vozes: {str(e)}")

@router.get("/model-info")
async def get_model_info():
    """
    Obter informações do serviço GCP Text-to-Speech
    """
    try:
        return voice_service.get_model_info()
    except Exception as e:
        logger.error(f"❌ Erro ao obter info do modelo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter informações: {str(e)}")

@router.get("/files")
async def list_audio_files():
    """
    Listar arquivos de áudio disponíveis
    """
    try:
        return voice_service.list_audio_files()
    except Exception as e:
        logger.error(f"❌ Erro ao listar arquivos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar arquivos: {str(e)}")

@router.delete("/cleanup")
async def cleanup_old_files(max_age_hours: int = Query(24, description="Idade máxima dos arquivos em horas")):
    """
    Limpar arquivos antigos
    """
    try:
        if max_age_hours < 1:
            raise HTTPException(status_code=400, detail="max_age_hours deve ser pelo menos 1")
        
        result = voice_service.cleanup_old_files(max_age_hours)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na limpeza: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na limpeza: {str(e)}")

# Manter compatibilidade com endpoint antigo
@router.post("/synthesize", response_model=SpeakResponse)
async def synthesize_text_legacy(request: SpeakRequest):
    """
    Endpoint legado para compatibilidade - redireciona para /speak
    """
    return await text_to_speech(request) 
