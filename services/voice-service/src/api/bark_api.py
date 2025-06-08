from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import logging
import os
import tempfile

from ..models.voice_models import TextToSpeechRequest, TextToSpeechResponse
from ..services.bark_service import BarkService

# Configurar logging
logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(prefix="/api/bark", tags=["bark"])

# Instanciar serviço Bark
bark_service = BarkService()

@router.post("/speak", response_model=TextToSpeechResponse)
async def bark_speak(request: TextToSpeechRequest, background_tasks: BackgroundTasks):
    """
    Endpoint principal para conversão de texto em fala usando Bark
    """
    try:
        logger.info(f"Processando TTS com Bark para texto: '{request.text[:50]}...'")
        
        # Converter texto em áudio usando Bark
        success, message, audio_url, duration = bark_service.text_to_speech(
            text=request.text,
            voice_speed=request.voice_speed
        )
        
        if success:
            # Agendar limpeza de arquivos antigos em background
            background_tasks.add_task(bark_service.cleanup_old_files, max_age_hours=24)
            
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
        logger.error(f"Erro no endpoint Bark speak: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/speak-with-voice", response_model=TextToSpeechResponse)
async def bark_speak_with_voice(
    text: str,
    voice_preset: str,
    voice_speed: float = 1.0,
    background_tasks: BackgroundTasks = None
):
    """
    Endpoint para TTS com voz específica do Bark
    """
    try:
        logger.info(f"Processando TTS com Bark (voz: {voice_preset}) para texto: '{text[:50]}...'")
        
        # Converter texto em áudio com voz específica
        success, message, audio_url, duration = bark_service.text_to_speech(
            text=text,
            voice_speed=voice_speed,
            voice_preset=voice_preset
        )
        
        if success:
            # Agendar limpeza de arquivos antigos em background
            if background_tasks:
                background_tasks.add_task(bark_service.cleanup_old_files, max_age_hours=24)
            
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
        logger.error(f"Erro no endpoint Bark speak with voice: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/clone-voice", response_model=TextToSpeechResponse)
async def bark_clone_voice(
    text: str,
    voice_speed: float = 1.0,
    voice_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Endpoint para análise de voz e seleção de voz similar no Bark
    (Bark não faz clonagem real, mas seleciona voz similar)
    """
    try:
        logger.info(f"Processando análise de voz para seleção similar com Bark: '{text[:50]}...'")
        
        # Salvar arquivo de voz temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(await voice_file.read())
            temp_voice_path = temp_file.name
        
        try:
            # Analisar voz e sugerir voz similar
            suggested_voice = bark_service.clone_voice_from_audio(temp_voice_path)
            
            if not suggested_voice:
                suggested_voice = bark_service.current_voice
                logger.warning("Não foi possível analisar a voz, usando voz padrão")
            
            # Converter texto em áudio com voz sugerida
            success, message, audio_url, duration = bark_service.text_to_speech(
                text=text,
                voice_speed=voice_speed,
                voice_preset=suggested_voice
            )
            
            if success:
                # Agendar limpeza de arquivos antigos em background
                if background_tasks:
                    background_tasks.add_task(bark_service.cleanup_old_files, max_age_hours=24)
                
                # Extrair filename da URL
                filename = audio_url.split("/")[-1] if audio_url else None
                
                return TextToSpeechResponse(
                    success=True,
                    message=f"{message} (voz similar selecionada: {suggested_voice})",
                    audio_url=audio_url,
                    filename=filename,
                    duration=duration
                )
            else:
                raise HTTPException(status_code=500, detail=message)
                
        finally:
            # Limpar arquivo temporário
            if os.path.exists(temp_voice_path):
                os.unlink(temp_voice_path)
            
    except Exception as e:
        logger.error(f"Erro no endpoint de clonagem Bark: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/voices/available")
async def get_available_voices():
    """
    Endpoint para listar vozes disponíveis no Bark
    """
    try:
        service_info = bark_service.get_service_info()
        return {
            "available_voices": service_info["available_voices"],
            "current_voice": service_info["current_voice"],
            "total_voices": len(service_info["available_voices"])
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar vozes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar vozes: {str(e)}")

@router.post("/voices/change")
async def change_voice(voice_key: str):
    """
    Endpoint para trocar a voz padrão do Bark
    """
    try:
        success = bark_service.change_voice(voice_key)
        
        if success:
            service_info = bark_service.get_service_info()
            return {
                "success": True,
                "message": f"Voz alterada para {voice_key}",
                "current_voice": service_info["current_voice"],
                "voice_description": service_info["available_voices"].get(voice_key, "Descrição não disponível")
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Voz {voice_key} não disponível"
            )
            
    except Exception as e:
        logger.error(f"Erro ao trocar voz: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao trocar voz: {str(e)}")

@router.get("/status")
async def bark_status():
    """
    Endpoint para verificar status do serviço Bark
    """
    try:
        service_info = bark_service.get_service_info()
        
        return {
            "status": "healthy" if service_info["models_loaded"] else "loading",
            "service_name": service_info["service_name"],
            "model_type": service_info["model_type"],
            "device": service_info["device"],
            "models_loaded": service_info["models_loaded"],
            "current_voice": service_info["current_voice"],
            "sample_rate": service_info["sample_rate"],
            "features": service_info["features"]
        }
        
    except Exception as e:
        logger.error(f"Erro no status do Bark: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no status: {str(e)}")

@router.post("/preload")
async def preload_models():
    """
    Endpoint para pré-carregar modelos do Bark
    """
    try:
        success = bark_service.load_models()
        
        if success:
            return {
                "success": True,
                "message": "Modelos do Bark carregados com sucesso",
                "device": bark_service.device
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Erro ao carregar modelos do Bark"
            )
            
    except Exception as e:
        logger.error(f"Erro ao pré-carregar modelos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao pré-carregar: {str(e)}")

@router.post("/cleanup")
async def cleanup_old_files(max_age_hours: int = 24):
    """
    Endpoint para limpeza manual de arquivos antigos do Bark
    """
    try:
        removed_count = bark_service.cleanup_old_files(max_age_hours)
        
        return {
            "success": True,
            "message": f"Limpeza concluída: {removed_count} arquivos removidos",
            "removed_count": removed_count,
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        logger.error(f"Erro na limpeza: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na limpeza: {str(e)}")

@router.get("/info")
async def bark_info():
    """
    Endpoint com informações detalhadas do serviço Bark
    """
    try:
        service_info = bark_service.get_service_info()
        
        return {
            "service": service_info["service_name"],
            "model": service_info["model_type"],
            "version": "1.0.0",
            "capabilities": {
                "natural_speech": True,
                "multiple_voices": True,
                "portuguese_brazilian": True,
                "emotion_support": True,
                "voice_analysis": True
            },
            "current_config": {
                "voice": service_info["current_voice"],
                "device": service_info["device"],
                "sample_rate": service_info["sample_rate"],
                "models_loaded": service_info["models_loaded"]
            },
            "available_voices": service_info["available_voices"],
            "features": service_info["features"]
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter informações: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter informações: {str(e)}") 