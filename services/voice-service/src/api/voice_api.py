from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import logging
import os
import tempfile

from ..models.voice_models import TextToSpeechRequest, TextToSpeechResponse, ModelChangeRequest, VoiceCloneRequest
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

@router.post("/clone-voice", response_model=TextToSpeechResponse)
async def clone_voice(
    text: str,
    voice_speed: float = 1.0,
    voice_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Endpoint para clonagem de voz usando arquivo de referência
    """
    try:
        logger.info(f"Processando clonagem de voz para texto: '{text[:50]}...'")
        
        # Salvar arquivo de voz temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(await voice_file.read())
            temp_voice_path = temp_file.name
        
        try:
            # Converter texto em áudio com clonagem
            success, message, audio_url, duration = tts_service.text_to_speech(
                text=text,
                voice_speed=voice_speed,
                voice_reference=temp_voice_path
            )
            
            if success:
                # Agendar limpeza de arquivos antigos em background
                if background_tasks:
                    background_tasks.add_task(tts_service.cleanup_old_files, max_age_hours=24)
                
                # Extrair filename da URL
                filename = audio_url.split("/")[-1] if audio_url else None
                
                return TextToSpeechResponse(
                    success=True,
                    message=f"{message} com clonagem de voz",
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
        logger.error(f"Erro no endpoint de clonagem: {e}")
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
        file_path = Path("/app/output") / filename
        
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

@router.post("/models/change")
async def change_model(request: ModelChangeRequest):
    """
    Endpoint para trocar o modelo TTS em tempo de execução
    """
    try:
        success = tts_service.change_model(request.model_key)
        
        if success:
            model_info = tts_service.get_model_info()
            return {
                "success": True,
                "message": f"Modelo alterado para {request.model_key}",
                "current_model": model_info["current_model"],
                "model_name": model_info["model_name"]
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Modelo {request.model_key} não disponível ou erro ao carregar"
            )
            
    except Exception as e:
        logger.error(f"Erro ao trocar modelo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao trocar modelo: {str(e)}")

@router.get("/models/available")
async def get_available_models():
    """
    Endpoint para listar modelos disponíveis
    """
    try:
        model_info = tts_service.get_model_info()
        return {
            "available_models": model_info["available_models"],
            "current_model": model_info["current_model"],
            "descriptions": {
                "xtts_v2": "XTTS-v2 - Melhor para português brasileiro, suporta clonagem de voz",
                "vits_pt": "VITS PT - Modelo original português europeu, rápido",
                "your_tts": "YourTTS - Multilíngue com clonagem, boa qualidade"
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar modelos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar modelos: {str(e)}")

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
    Endpoint para verificar status completo do modelo TTS
    """
    try:
        model_info = tts_service.get_model_info()
        return {
            **model_info,
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
            model_info = tts_service.get_model_info()
            return {
                "success": True,
                "message": "Modelo carregado com sucesso",
                "current_model": model_info["current_model"],
                "model_name": model_info["model_name"],
                "device": model_info["device"]
            }
        else:
            raise HTTPException(status_code=500, detail="Falha ao carregar modelo TTS")
            
    except Exception as e:
        logger.error(f"Erro ao carregar modelo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao carregar modelo: {str(e)}")

@router.get("/test-models")
async def test_models():
    """
    Endpoint para testar todos os modelos disponíveis com uma frase em português brasileiro
    """
    try:
        test_text = "Olá! Este é um teste de síntese de voz em português brasileiro."
        results = {}
        original_model = tts_service.current_model
        
        for model_key in tts_service.available_models.keys():
            try:
                logger.info(f"Testando modelo {model_key}")
                
                # Trocar para o modelo de teste
                if tts_service.change_model(model_key):
                    # Gerar áudio de teste
                    success, message, audio_url, duration = tts_service.text_to_speech(
                        text=test_text,
                        voice_speed=1.0
                    )
                    
                    results[model_key] = {
                        "success": success,
                        "message": message,
                        "audio_url": audio_url,
                        "duration": duration,
                        "model_name": tts_service.available_models[model_key]
                    }
                else:
                    results[model_key] = {
                        "success": False,
                        "message": f"Falha ao carregar modelo {model_key}",
                        "audio_url": None,
                        "duration": None
                    }
                    
            except Exception as e:
                results[model_key] = {
                    "success": False,
                    "message": f"Erro ao testar modelo {model_key}: {str(e)}",
                    "audio_url": None,
                    "duration": None
                }
        
        # Retornar ao modelo original
        tts_service.change_model(original_model)
        
        return {
            "test_text": test_text,
            "results": results,
            "restored_model": original_model
        }
        
    except Exception as e:
        logger.error(f"Erro ao testar modelos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao testar modelos: {str(e)}") 