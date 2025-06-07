import logging
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.voice_api import router as voice_router
from .models.voice_models import HealthResponse
from .services.tts_service import TTSService

# Configurar logging avançado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/output/voice_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configurações da aplicação
SERVICE_NAME = "voice-service"
SERVICE_VERSION = "2.0.0"
SERVICE_DESCRIPTION = """
🎤 Serviço de Síntese de Voz Aprimorado

Suporte avançado para português brasileiro com:
- Múltiplos modelos TTS (XTTS-v2, VITS, YourTTS)
- Clonagem de voz com amostras de 6 segundos
- Troca dinâmica de modelos
- Qualidade otimizada para sotaque brasileiro
- API RESTful completa

Principais recursos:
- ✨ XTTS-v2: Melhor qualidade para português brasileiro
- 🎯 Clonagem de voz em tempo real
- 🔄 Troca de modelos sem reinicialização
- 📊 Monitoramento completo de performance
- 🌎 Suporte nativo ao português brasileiro
"""

# Criar aplicação FastAPI
app = FastAPI(
    title="Voice Service Enhanced",
    description=SERVICE_DESCRIPTION,
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instância global do serviço TTS
tts_service = None

@app.on_event("startup")
async def startup_event():
    """Inicialização do serviço"""
    global tts_service
    
    logger.info("🚀 Iniciando Voice Service Enhanced v%s", SERVICE_VERSION)
    
    try:
        # Criar diretório de saída se não existir
        output_dir = Path("/app/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("📁 Diretório de saída configurado: %s", output_dir)
        
        # Inicializar serviço TTS
        tts_service = TTSService()
        logger.info("🎤 Inicializando serviço TTS...")
        
        # Carregar modelo padrão
        if tts_service.load_model():
            model_info = tts_service.get_model_info()
            logger.info("✅ TTS inicializado com sucesso!")
            logger.info("   Modelo: %s", model_info['current_model'])
            logger.info("   Nome técnico: %s", model_info['model_name'])
            logger.info("   Dispositivo: %s", model_info['device'])
            logger.info("   Modelos disponíveis: %s", list(model_info['available_models'].keys()))
        else:
            logger.error("❌ Falha ao carregar modelo TTS")
            raise RuntimeError("Falha na inicialização do modelo TTS")
            
        # Limpeza inicial de arquivos antigos
        try:
            removed_count = tts_service.cleanup_old_files(max_age_hours=24)
            logger.info("🧹 Limpeza inicial: %d arquivos antigos removidos", removed_count)
        except Exception as e:
            logger.warning("⚠️ Aviso na limpeza inicial: %s", e)
        
        logger.info("🎯 Voice Service Enhanced pronto para uso!")
        logger.info("📖 Documentação disponível em: http://localhost:8004/docs")
        logger.info("🔍 Monitoramento em: http://localhost:8004/health")
        
    except Exception as e:
        logger.error("💥 Erro crítico na inicialização: %s", e)
        raise

# Configurar arquivos estáticos para servir áudios
try:
    output_dir = Path("/app/output")
    if output_dir.exists():
        app.mount("/audio", StaticFiles(directory=str(output_dir)), name="audio")
        logger.info("🔊 Arquivos de áudio disponíveis em: /audio/")
    else:
        logger.warning("⚠️ Diretório de áudio não encontrado: %s", output_dir)
except Exception as e:
    logger.error("❌ Erro ao configurar arquivos estáticos: %s", e)

@app.on_event("shutdown")
async def shutdown_event():
    """Limpeza ao desligar o serviço"""
    global tts_service
    
    logger.info("🛑 Desligando Voice Service Enhanced...")
    
    try:
        if tts_service:
            # Limpeza final
            removed_count = tts_service.cleanup_old_files(max_age_hours=1)
            logger.info("🧹 Limpeza final: %d arquivos removidos", removed_count)
            
        logger.info("✅ Serviço desligado com sucesso")
        
    except Exception as e:
        logger.error("❌ Erro durante desligamento: %s", e)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções"""
    logger.error("Erro não tratado em %s: %s", request.url, exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "detail": "Consulte os logs para mais informações",
            "timestamp": datetime.now().isoformat(),
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION
        }
    )

@app.get("/", tags=["root"])
async def root():
    """Endpoint raiz com informações do serviço"""
    global tts_service
    
    model_info = None
    if tts_service:
        try:
            model_info = tts_service.get_model_info()
        except Exception as e:
            logger.warning("Erro ao obter info do modelo: %s", e)
    
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": "Serviço de Síntese de Voz Aprimorado para Português Brasileiro",
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Múltiplos modelos TTS",
            "Clonagem de voz",
            "Português brasileiro nativo",
            "Troca dinâmica de modelos",
            "API RESTful completa"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "api": "/api/voice",
            "direct_tts": "/speak"
        },
        "current_model": model_info.get('current_model') if model_info else None,
        "models_available": list(model_info.get('available_models', {}).keys()) if model_info else []
    }

@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check completo do serviço"""
    global tts_service
    
    try:
        # Verificar status do TTS
        tts_loaded = False
        current_model = "unknown"
        
        if tts_service:
            tts_loaded = tts_service.is_model_loaded()
            if tts_loaded:
                model_info = tts_service.get_model_info()
                current_model = model_info.get('current_model', 'unknown')
        
        # Verificar diretório de saída
        output_dir = Path("/app/output")
        output_accessible = output_dir.exists() and output_dir.is_dir()
        
        # Determinar status geral
        if tts_loaded and output_accessible:
            status = "healthy"
        elif tts_loaded:
            status = "degraded"  # TTS ok mas diretório com problema
        else:
            status = "unhealthy"
        
        return HealthResponse(
            status=status,
            service=f"{SERVICE_NAME} v{SERVICE_VERSION}",
            timestamp=datetime.now(),
            version=SERVICE_VERSION,
            tts_model_loaded=tts_loaded
        )
        
    except Exception as e:
        logger.error("Erro no health check: %s", e)
        return HealthResponse(
            status="error",
            service=f"{SERVICE_NAME} v{SERVICE_VERSION}",
            timestamp=datetime.now(),
            version=SERVICE_VERSION,
            tts_model_loaded=False
        )

# Endpoint direto para compatibilidade (sem prefixo /api)
@app.post("/speak", tags=["compatibility"])
async def direct_speak(request_data: dict):
    """
    Endpoint direto para TTS (compatibilidade com versão anterior)
    Redireciona para o endpoint principal da API
    """
    try:
        from .models.voice_models import TextToSpeechRequest
        
        # Converter dict para modelo
        tts_request = TextToSpeechRequest(**request_data)
        
        # Usar o serviço TTS diretamente
        global tts_service
        if not tts_service:
            raise HTTPException(status_code=503, detail="Serviço TTS não disponível")
        
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
            raise HTTPException(status_code=500, detail=message)
            
    except Exception as e:
        logger.error("Erro no endpoint direto: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Incluir roteador da API principal
app.include_router(voice_router)

# Endpoint de informações detalhadas
@app.get("/info", tags=["info"])
async def service_info():
    """Informações detalhadas do serviço e capacidades"""
    global tts_service
    
    info = {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": "Serviço avançado de síntese de voz para português brasileiro"
        },
        "capabilities": {
            "languages": ["pt-BR", "pt"],
            "voice_cloning": True,
            "model_switching": True,
            "batch_processing": True,
            "real_time_processing": True
        },
        "api": {
            "version": "2.0",
            "formats": ["wav"],
            "max_text_length": 5000,
            "supported_speeds": {"min": 0.1, "max": 3.0}
        }
    }
    
    # Adicionar informações do modelo se disponível
    if tts_service:
        try:
            model_info = tts_service.get_model_info()
            info["current_model"] = {
                "key": model_info.get('current_model'),
                "name": model_info.get('model_name'),
                "device": model_info.get('device'),
                "loaded": model_info.get('model_loaded')
            }
            info["available_models"] = model_info.get('available_models', {})
        except Exception as e:
            logger.warning("Erro ao obter info do modelo: %s", e)
    
    return info

if __name__ == "__main__":
    import uvicorn
    
    # Configurações para desenvolvimento
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info",
        access_log=True
    ) 