"""
Voice Service - Serviço de síntese de voz usando Google Cloud Text-to-Speech API
Documentação oficial: https://cloud.google.com/text-to-speech/docs/quickstart-client-libraries
"""

import os
import sys
import logging
import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configurar logging
os.makedirs('/app/logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/voice-service.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

# Importar API
from .api.voice_api import router as voice_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerenciar ciclo de vida da aplicação
    """
    logger.info("🚀 Iniciando Voice Service com Google Cloud Text-to-Speech...")
    
    try:
        # Criar diretórios necessários
        os.makedirs("/app/logs", exist_ok=True)
        os.makedirs("/app/output", exist_ok=True)
        
        logger.info("✅ Diretórios criados com sucesso")
        
        # Verificar configuração do GCP
        gcp_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if gcp_credentials:
            logger.info(f"✅ Credenciais GCP configuradas: {gcp_credentials}")
        else:
            logger.warning("⚠️ GOOGLE_APPLICATION_CREDENTIALS não definida - usando credenciais padrão do ambiente")
        
        # Testar importações críticas
        try:
            from google.cloud import texttospeech
            logger.info("✅ Google Cloud Text-to-Speech carregado")
            
            # Testar inicialização do cliente (sem fazer requisições)
            try:
                client = texttospeech.TextToSpeechClient()
                logger.info("✅ Cliente GCP Text-to-Speech inicializado")
            except Exception as e:
                logger.warning(f"⚠️ Aviso na inicialização do cliente GCP: {e}")
                
        except ImportError as e:
            logger.error(f"❌ Erro ao importar Google Cloud Text-to-Speech: {e}")
            raise
        
        logger.info("🎙️ Voice Service iniciado com sucesso!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        raise
    finally:
        logger.info("🛑 Finalizando Voice Service...")

# Criar aplicação FastAPI
app = FastAPI(
    title="Voice Service - GCP TTS",
    description="Serviço de síntese de voz usando Google Cloud Text-to-Speech API",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(voice_router)

# Endpoints básicos
@app.get("/")
async def root():
    """
    Endpoint raiz
    """
    return {
        "service": "voice-service",
        "version": "3.0.0",
        "description": "Serviço de síntese de voz usando Google Cloud Text-to-Speech API",
        "provider": "Google Cloud",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

@app.get("/health")
async def health():
    """
    Health check básico
    """
    try:
        from google.cloud import texttospeech
        
        # Verificar credenciais
        gcp_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        credentials_status = "configured" if gcp_credentials else "using_default"
        
        return {
            "status": "healthy",
            "service": "voice-service-gcp",
            "version": "3.0.0",
            "provider": "Google Cloud Text-to-Speech",
            "credentials_status": credentials_status,
            "output_dir": "/app/output"
        }
    except Exception as e:
        logger.error(f"❌ Erro no health check: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no health check: {str(e)}")

# Handler de exceções global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Handler global para exceções não tratadas
    """
    logger.error(f"❌ Erro não tratado: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )

if __name__ == "__main__":
    # Configurações do servidor
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8004))
    workers = int(os.getenv("WORKERS", 1))
    
    logger.info(f"🚀 Iniciando servidor em {host}:{port} com {workers} workers")
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        workers=workers,
        reload=False,
        log_level="info"
    ) 