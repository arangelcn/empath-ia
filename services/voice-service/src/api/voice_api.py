"""
API endpoints para o serviço de voz usando F5-TTS
"""
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import FileResponse
from typing import Optional
import logging
import os
from pathlib import Path
from datetime import datetime

from ..models.voice_models import (
    SynthesizeRequest, SynthesizeResponse, 
    TextToSpeechRequest, TextToSpeechResponse,
    HealthResponse, ModelInfo
)
from ..services.f5_tts_service import F5TTSService

logger = logging.getLogger(__name__)
router = APIRouter()

# Instância global do serviço F5-TTS
f5_tts_service = None

def set_f5_tts_service(service: F5TTSService):
    """Define a instância do serviço F5-TTS"""
    global f5_tts_service
    f5_tts_service = service

@router.get("/health", response_model=HealthResponse)
async def voice_health():
    """Health check específico para o serviço de voz"""
    global f5_tts_service
    
    if not f5_tts_service:
        return HealthResponse(
            status="error",
            service="voice-service",
            timestamp=datetime.now(),
            model_info=None
        )
    
    model_info_dict = f5_tts_service.get_model_info()
    model_info = ModelInfo(
        model_name=model_info_dict["model_name"],
        device=model_info_dict["device"],
        model_loaded=model_info_dict["model_loaded"],
        sample_rate=model_info_dict["sample_rate"],
        output_dir=model_info_dict["output_directory"]
    )
    
    return HealthResponse(
        status="healthy" if model_info.model_loaded else "loading",
        service="voice-service",
        timestamp=datetime.now(),
        model_info=model_info
    )

@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(request: SynthesizeRequest):
    """
    Sintetiza fala a partir de texto usando F5-TTS-pt-br
    """
    global f5_tts_service
    
    if not f5_tts_service:
        raise HTTPException(status_code=503, detail="Serviço F5-TTS não disponível")
    
    try:
        # Clean text
        clean_text = f5_tts_service._clean_text(request.text)
        if not clean_text:
            raise HTTPException(status_code=400, detail="Texto vazio após limpeza")
        
        # Generate filename
        filename = f5_tts_service._generate_filename(clean_text)
        audio_path = f5_tts_service.output_dir / filename
        
        # Synthesize audio
        success = f5_tts_service.synthesize(
            text=clean_text,
            output_path=str(audio_path)
        )
        
        if success:
            # Calculate duration by reading the audio file
            import soundfile as sf
            try:
                audio_data, sample_rate = sf.read(str(audio_path))
                duration = len(audio_data) / sample_rate
            except:
                duration = len(clean_text) * 0.08  # Fallback estimation
            
            audio_url = f"/api/v1/audio/{filename}"
            return SynthesizeResponse(
                success=True,
                message="Áudio sintetizado com F5-TTS",
                audio_path=str(audio_path),
                filename=filename,
                audio_url=audio_url,
                duration=duration,
                text_length=len(request.text)
            )
        else:
            raise HTTPException(status_code=500, detail="Falha na síntese de áudio")
            
    except Exception as e:
        logger.error(f"Erro na síntese de áudio: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/synthesize-form")
async def synthesize_speech_form(text: str = Form(...)):
    """
    Sintetiza fala a partir de texto usando formulário
    """
    request = SynthesizeRequest(text=text)
    return await synthesize_speech(request)

@router.get("/model-info", response_model=ModelInfo)
async def get_model_info():
    """
    Retorna informações sobre o modelo F5-TTS
    """
    global f5_tts_service
    
    if not f5_tts_service:
        raise HTTPException(status_code=503, detail="Serviço F5-TTS não disponível")
    
    model_info_dict = f5_tts_service.get_model_info()
    return ModelInfo(
        model_name=model_info_dict["model_name"],
        device=model_info_dict["device"],
        model_loaded=model_info_dict["model_loaded"],
        sample_rate=model_info_dict["sample_rate"],
        output_dir=model_info_dict["output_directory"]
    )

@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """
    Serve arquivos de áudio gerados
    """
    global f5_tts_service
    
    if not f5_tts_service:
        raise HTTPException(status_code=503, detail="Serviço F5-TTS não disponível")
    
    file_path = f5_tts_service.get_audio_file_path(filename)
    
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        headers={
            "Content-Disposition": f"inline; filename={filename}",
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600"
        }
    )

@router.delete("/cleanup")
async def cleanup_old_files(max_age_hours: Optional[int] = 24):
    """
    Remove arquivos antigos do diretório de saída
    """
    global f5_tts_service
    
    if not f5_tts_service:
        raise HTTPException(status_code=503, detail="Serviço F5-TTS não disponível")
    
    try:
        removed_count = f5_tts_service.cleanup_old_files(max_age_hours)
        return {
            "success": True,
            "message": f"Limpeza concluída",
            "files_removed": removed_count,
            "max_age_hours": max_age_hours
        }
    except Exception as e:
        logger.error(f"Erro na limpeza: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/files")
async def list_audio_files():
    """
    Lista arquivos de áudio disponíveis
    """
    global f5_tts_service
    
    if not f5_tts_service:
        raise HTTPException(status_code=503, detail="Serviço F5-TTS não disponível")
    
    try:
        files = f5_tts_service.list_audio_files()
        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        logger.error(f"Erro ao listar arquivos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ENDPOINTS DEPRECATED - Mantidos para compatibilidade
@router.post("/generate", response_model=TextToSpeechResponse)
async def generate_speech(tts_request: TextToSpeechRequest):
    """
    Gera áudio a partir de texto usando TTS (DEPRECATED - use /synthesize)
    """
    logger.warning("Endpoint /generate está deprecated. Use /synthesize")
    
    global f5_tts_service
    
    if not f5_tts_service:
        raise HTTPException(status_code=503, detail="Serviço F5-TTS não disponível")
    
    try:
        success, message, audio_path, filename, duration = f5_tts_service.synthesize(
            text=tts_request.text,
            voice_speed=tts_request.voice_speed
        )
        
        if success:
            audio_url = f"/api/v1/audio/{filename}" if filename else None
            return TextToSpeechResponse(
                success=True,
                message=message,
                audio_url=audio_url,
                filename=filename,
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
    Gera áudio a partir de texto usando formulário (DEPRECATED - use /synthesize-form)
    """
    logger.warning("Endpoint /generate-form está deprecated. Use /synthesize-form")
    tts_request = TextToSpeechRequest(text=text, voice_speed=voice_speed)
    return await generate_speech(tts_request)

# COMENTADO: Endpoints do Bark deixando para implementação futura
# @router.get("/bark/voices")
# async def get_bark_voices():
#     """Retorna as vozes disponíveis do Bark"""
#     # Implementação futura

# @router.post("/bark/generate")
# async def generate_bark_speech(tts_request: TextToSpeechRequest):
#     """Gera áudio usando o Bark"""
#     # Implementação futura 