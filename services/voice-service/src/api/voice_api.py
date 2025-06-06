from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
import logging
import os

from ..models.voice_models import TextToSpeechRequest, TextToSpeechResponse
from ..services.tts_service import TTSService

# Configurar logging
logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(prefix="/api/voice", tags=["voice"])

# Instanciar serviço TTS
tts_service = TTSService()

@router.post("/speak", response_model=TextToSpeechResponse)
async def speak(request: TextToSpeechRequest, background_tasks: BackgroundTasks):
    """
    Endpoint principal para conversão de texto em fala
    """
    try:
        logger.info(f"Processando TTS para texto: '{request.text[:50]}...'")
        
        # Converter texto em áudio
        success, message, audio_url, duration = tts_service.text_to_speech(
            text=request.text,
            voice_speed=request.voice_speed
        )
        
        if success:
            # Agendar limpeza de arquivos antigos em background
            background_tasks.add_task(tts_service.cleanup_old_files, max_age_hours=24)
            
            # Extrair filename da URL
            filename = audio_url.split("/")[-1] if audio_url else None
            
            return TextToSpeechResponse(
                success=True,
                message=message,
                audio_url=audio_url,
                filename=filename,
                duration=duration
            )
        else:
            raise HTTPException(status_code=500, detail=message)
            
    except Exception as e:
        logger.error(f"Erro no endpoint speak: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """
    Endpoint para servir arquivos de áudio gerados
    """
    try:
        # Validar nome do arquivo
        if not filename.endswith('.wav') or '..' in filename or '/' in filename:
            raise HTTPException(status_code=400, detail="Nome de arquivo inválido")
        
        # Caminho do arquivo
        file_path = Path("/shared_tts") / filename
        
        # Verificar se arquivo existe
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Arquivo de áudio não encontrado")
        
        # Retornar arquivo
        return FileResponse(
            path=str(file_path),
            media_type="audio/wav",
            filename=filename,
            headers={"Cache-Control": "public, max-age=3600"}  # Cache por 1 hora
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao servir áudio: {e}")
        raise HTTPException(status_code=500, detail="Erro ao acessar arquivo de áudio")

@router.post("/cleanup")
async def cleanup_old_files(max_age_hours: int = 24):
    """
    Endpoint para limpeza manual de arquivos antigos
    """
    try:
        removed_count = tts_service.cleanup_old_files(max_age_hours)
        
        return {
            "success": True,
            "message": f"Limpeza concluída: {removed_count} arquivos removidos",
            "removed_count": removed_count,
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        logger.error(f"Erro na limpeza: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na limpeza: {str(e)}")

@router.get("/models/status")
async def model_status():
    """
    Endpoint para verificar status do modelo TTS
    """
    try:
        return {
            "model_name": tts_service.model_name,
            "device": tts_service.device,
            "model_loaded": tts_service.is_model_loaded(),
            "output_directory": str(tts_service.output_dir),
            "base_url": tts_service.base_url
        }
        
    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao verificar status: {str(e)}")

@router.post("/models/load")
async def load_model():
    """
    Endpoint para carregar modelo TTS manualmente
    """
    try:
        success = tts_service.load_model()
        
        if success:
            return {
                "success": True,
                "message": "Modelo carregado com sucesso",
                "model_name": tts_service.model_name,
                "device": tts_service.device
            }
        else:
            raise HTTPException(status_code=500, detail="Falha ao carregar modelo TTS")
            
    except Exception as e:
        logger.error(f"Erro ao carregar modelo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao carregar modelo: {str(e)}") 