from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import logging
from datetime import datetime
from pathlib import Path

from .api.voice_api import router as voice_router
from .models.voice_models import HealthResponse
from .services.tts_service import TTSService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar diretório de saída se não existir
OUTPUT_DIR = Path("/shared_tts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Criar app FastAPI
app = FastAPI(
    title="empatIA Voice Service",
    description="Microserviço de síntese de voz usando Coqui TTS para o projeto empatIA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos para servir áudios
app.mount("/audio", StaticFiles(directory=str(OUTPUT_DIR)), name="audio")

# Instanciar serviço TTS global
tts_service = None

@app.on_event("startup")
async def startup_event():
    """Inicialização da aplicação"""
    global tts_service
    logger.info("Iniciando Voice Service...")
    
    # Criar diretório de saída se não existir
    output_dir = Path("/shared_tts")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Inicializar serviço TTS
    tts_service = TTSService()
    
    # Carregar modelo TTS na inicialização para estar pronto
    logger.info("Carregando modelo TTS...")
    if tts_service.load_model():
        logger.info("✅ Modelo TTS carregado com sucesso na inicialização!")
    else:
        logger.warning("⚠️ Falha ao carregar modelo TTS na inicialização")
    
    logger.info("Voice Service iniciado com sucesso!")

@app.on_event("shutdown")
async def shutdown_event():
    """Finalização da aplicação"""
    logger.info("Finalizando Voice Service...")

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint de verificação de saúde do serviço"""
    global tts_service
    
    model_loaded = False
    if tts_service:
        model_loaded = tts_service.is_model_loaded()
    
    return HealthResponse(
        status="healthy",
        service="voice-service",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        tts_model_loaded=model_loaded
    )

# Root endpoint
@app.get("/")
async def root():
    """Endpoint raiz do serviço"""
    return {
        "message": "empatIA Voice Service",
        "description": "Microserviço de síntese de voz",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "speak": "/api/voice/speak",
            "audio": "/api/voice/audio/{filename}",
            "cleanup": "/api/voice/cleanup",
            "model_status": "/api/voice/models/status",
            "load_model": "/api/voice/models/load"
        }
    }

# Incluir routers
app.include_router(voice_router)

# Endpoint direto para compatibilidade
@app.post("/speak")
async def speak_direct(request: dict):
    """
    Endpoint direto para compatibilidade com chamadas simples
    """
    try:
        from .models.voice_models import TextToSpeechRequest
        
        # Converter dict para modelo Pydantic
        tts_request = TextToSpeechRequest(**request)
        
        # Processar com o serviço TTS
        success, message, audio_url, duration = tts_service.text_to_speech(
            text=tts_request.text,
            voice_speed=tts_request.voice_speed
        )
        
        if success:
            return {
                "success": True,
                "message": message,
                "audio_url": audio_url,
                "filename": audio_url.split("/")[-1] if audio_url else None,
                "duration": duration
            }
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": message}
            )
            
    except Exception as e:
        logger.error(f"Erro no endpoint speak direto: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erro interno: {str(e)}"}
        )

# Endpoint para configurações
@app.get("/config")
async def get_config():
    """Retorna configurações do serviço"""
    global tts_service
    
    config = {
        "service_name": "voice-service",
        "service_port": os.getenv("VOICE_SERVICE_PORT", "8004"),
        "base_url": os.getenv("VOICE_SERVICE_BASE_URL", "http://localhost:8004"),
        "output_directory": "/shared_tts",
        "debug": os.getenv("DEBUG", "false").lower() == "true"
    }
    
    if tts_service:
        config.update({
            "model_name": tts_service.model_name,
            "device": tts_service.device,
            "model_loaded": tts_service.is_model_loaded()
        })
    
    return config

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 