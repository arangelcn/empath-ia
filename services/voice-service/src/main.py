"""
Voice Service - Serviço de Text-to-Speech usando F5-TTS-pt-br
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .services.f5_tts_service import F5TTSService
from .api.voice_api import router as voice_router, set_f5_tts_service
from .models.voice_models import HealthResponse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações do serviço
SERVICE_NAME = "voice-service"
SERVICE_VERSION = "2.0.0"
SERVICE_DESCRIPTION = "Serviço de Text-to-Speech usando F5-TTS-pt-br"

# Instância global do serviço F5-TTS
f5_tts_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    global f5_tts_service
    
    # Startup
    logger.info(f"🚀 Iniciando {SERVICE_NAME} v{SERVICE_VERSION}")
    logger.info(f"📝 {SERVICE_DESCRIPTION}")
    
    try:
        # Inicializar serviço F5-TTS
        logger.info("🔧 Inicializando serviço F5-TTS...")
        f5_tts_service = F5TTSService()
        
        # Configurar o serviço na API
        set_f5_tts_service(f5_tts_service)
        
        # Tentar carregar o modelo
        logger.info("📦 Carregando modelo F5-TTS...")
        if f5_tts_service.load_model():
            logger.info("✅ Modelo F5-TTS carregado com sucesso!")
        else:
            logger.warning("⚠️ Modelo F5-TTS não pôde ser carregado no startup")
        
        logger.info("🎉 Voice Service iniciado com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar Voice Service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Finalizando Voice Service...")
    if f5_tts_service:
        # Cleanup se necessário
        try:
            f5_tts_service.cleanup_old_files(max_age_hours=1)
        except Exception as e:
            logger.error(f"Erro na limpeza final: {e}")
    
    logger.info("👋 Voice Service finalizado")

# Criar aplicação FastAPI
app = FastAPI(
    title=SERVICE_NAME,
    description=SERVICE_DESCRIPTION,
    version=SERVICE_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens específicas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas da API
app.include_router(voice_router, prefix="/api/v1", tags=["voice"])

# Rota raiz
@app.get("/")
async def root():
    """Endpoint raiz com informações do serviço"""
    global f5_tts_service
    
    model_info = None
    if f5_tts_service:
        try:
            model_info = f5_tts_service.get_model_info()
        except Exception as e:
            logger.error(f"Erro ao obter info do modelo: {e}")
    
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": SERVICE_DESCRIPTION,
        "status": "running",
        "model_info": model_info,
        "endpoints": {
            "health": "/api/v1/health",
            "synthesize": "/api/v1/synthesize",
            "synthesize_form": "/api/v1/synthesize-form",
            "model_info": "/api/v1/model-info",
            "audio": "/api/v1/audio/{filename}",
            "cleanup": "/api/v1/cleanup",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

# Health check global
@app.get("/health")
async def global_health():
    """Health check global do serviço"""
    global f5_tts_service
    
    if not f5_tts_service:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "service": SERVICE_NAME,
                "message": "Serviço F5-TTS não inicializado"
            }
        )
    
    try:
        model_info = f5_tts_service.get_model_info()
        return {
            "status": "healthy" if model_info["model_loaded"] else "loading",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "model_loaded": model_info["model_loaded"],
            "device": model_info["device"]
        }
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "service": SERVICE_NAME,
                "message": f"Erro interno: {str(e)}"
            }
        )

# Servir arquivos de áudio estáticos
output_dir = Path(os.getenv("F5_TTS_OUTPUT_DIR", "/app/tts_output"))
if output_dir.exists():
    app.mount("/audio", StaticFiles(directory=str(output_dir)), name="audio")
else:
    logger.warning(f"Diretório de áudio não encontrado: {output_dir}")
    # Criar diretório se não existir
    output_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/audio", StaticFiles(directory=str(output_dir)), name="audio")

# Handler de exceções global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções não tratadas"""
    logger.error(f"Exceção não tratada: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "service": SERVICE_NAME,
            "message": "Erro interno do servidor"
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("VOICE_SERVICE_PORT", 8004))
    host = os.getenv("VOICE_SERVICE_HOST", "0.0.0.0")
    
    logger.info(f"🚀 Iniciando servidor em {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    ) 