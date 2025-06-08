"""
API endpoints para o serviço de voz
"""
from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from fastapi.responses import FileResponse
from typing import Optional, Dict, Any
import logging
import os
from pathlib import Path

from ..models.voice_models import TextToSpeechRequest, TextToSpeechResponse
from ..services.tts_service import TTSService

logger = logging.getLogger(__name__)
router = APIRouter()

# Instância global do serviço TTS
tts_service = None

def set_tts_service(service: TTSService):
    """Define a instância do serviço TTS"""
    global tts_service
    tts_service = service

@router.get("/health")
async def voice_health():
    """Health check específico para o serviço de voz"""
    global tts_service
    
    if not tts_service:
        return {"status": "error", "message": "Serviço TTS não inicializado"}
    
    model_info = tts_service.get_model_info()
    return {
        "status": "healthy",
        "service": "voice-service",
        "model": model_info['current_model'],
        "model_name": model_info['model_name'],
        "device": model_info['device'],
        "available_models": list(model_info['available_models'].keys())
    }

@router.post("/generate", response_model=TextToSpeechResponse)
async def generate_speech(tts_request: TextToSpeechRequest):
    """
    Gera áudio a partir de texto usando TTS
    """
    global tts_service
    
    if not tts_service:
        raise HTTPException(status_code=503, detail="Serviço TTS não disponível")
    
    try:
        success, message, audio_url, duration = tts_service.text_to_speech(
            text=tts_request.text,
            voice_speed=tts_request.voice_speed
        )
        
        if success:
            return TextToSpeechResponse(
                success=True,
                message=message,
                audio_url=audio_url,
                filename=audio_url.split("/")[-1] if audio_url else None,
                duration=duration,
                text_length=len(tts_request.text)
            )
        else:
            raise HTTPException(status_code=500, detail=message)
            
    except Exception as e:
        logger.error(f"Erro na geração de áudio: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/generate-form")
async def generate_speech_form(
    text: str = Form(...),
    voice_speed: Optional[float] = Form(1.0)
):
    """
    Gera áudio a partir de texto usando formulário
    """
    tts_request = TextToSpeechRequest(text=text, voice_speed=voice_speed)
    return await generate_speech(tts_request)

@router.get("/models")
async def get_available_models():
    """
    Retorna os modelos TTS disponíveis
    """
    global tts_service
    
    if not tts_service:
        raise HTTPException(status_code=503, detail="Serviço TTS não disponível")
    
    model_info = tts_service.get_model_info()
    return {
        "current_model": model_info['current_model'],
        "model_name": model_info['model_name'],
        "available_models": model_info['available_models'],
        "device": model_info['device']
    }

@router.post("/models/{model_name}")
async def switch_model(model_name: str):
    """
    Troca o modelo TTS atual
    """
    global tts_service
    
    if not tts_service:
        raise HTTPException(status_code=503, detail="Serviço TTS não disponível")
    
    try:
        success = tts_service.change_model(model_name)
        if success:
            model_info = tts_service.get_model_info()
            return {
                "success": True,
                "message": f"Modelo trocado para {model_name}",
                "current_model": model_info['current_model'],
                "model_name": model_info['model_name']
            }
        else:
            raise HTTPException(status_code=400, detail=f"Não foi possível trocar para o modelo {model_name}")
            
    except Exception as e:
        logger.error(f"Erro ao trocar modelo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """
    Serve arquivos de áudio gerados
    """
    file_path = Path("/app/output") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename=filename
    )

@router.delete("/cleanup")
async def cleanup_old_files(max_age_hours: Optional[int] = 24):
    """
    Remove arquivos antigos do diretório de saída
    """
    global tts_service
    
    if not tts_service:
        raise HTTPException(status_code=503, detail="Serviço TTS não disponível")
    
    try:
        removed_count = tts_service.cleanup_old_files(max_age_hours)
        return {
            "success": True,
            "message": f"Limpeza concluída",
            "files_removed": removed_count,
            "max_age_hours": max_age_hours
        }
    except Exception as e:
        logger.error(f"Erro na limpeza: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# COMENTADO: Endpoints do Bark deixando para implementação futura
# @router.get("/bark/voices")
# async def get_bark_voices():
#     """Retorna as vozes disponíveis do Bark"""
#     # Implementação futura

# @router.post("/bark/generate")
# async def generate_bark_speech(tts_request: TextToSpeechRequest):
#     """Gera áudio usando o Bark"""
#     # Implementação futura 