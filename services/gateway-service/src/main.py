from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .models.database import init_mongodb, close_mongodb, create_indexes
from .services.prompt_service import PromptService
from .api.admin_contexts import router as admin_contexts_router
from .api.admin_conversations import router as admin_conversations_router
from .api.admin_dashboard import router as admin_dashboard_router
from .api.admin_knowledge import router as admin_knowledge_router
from .api.admin_sessions import router as admin_sessions_router
from .api.admin_users import router as admin_users_router
from .api.auth import router as auth_router
from .api.chat import router as chat_router
from .api.chat_context import router as chat_context_router
from .api.emotions import router as emotions_router
from .api.health import router as health_router
from .api.prompts import router as prompts_router
from .api.proxy import router as proxy_router
from .api.sessions import router as sessions_router
from .api.users import router as users_router
from .api.voice import router as voice_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar app FastAPI
app = FastAPI(
    title="empatIA Gateway Service",
    description="API Gateway para microserviços empatIA - Com persistência MongoDB",
    version="2.0.0",
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

# Instâncias dos serviços
prompt_service = PromptService()

# Incluir rotas
app.include_router(auth_router)
app.include_router(admin_contexts_router)
app.include_router(admin_conversations_router)
app.include_router(admin_dashboard_router)
app.include_router(admin_knowledge_router)
app.include_router(admin_sessions_router)
app.include_router(admin_users_router)
app.include_router(chat_router)
app.include_router(chat_context_router)
app.include_router(emotions_router)
app.include_router(health_router)
app.include_router(prompts_router)
app.include_router(proxy_router)
app.include_router(sessions_router)
app.include_router(users_router)
app.include_router(voice_router)

# Eventos de startup e shutdown
@app.on_event("startup")
async def startup_event():
    """Inicializar conexões na startup"""
    try:
        init_mongodb()
        logger.info("✅ Gateway Service iniciado com sucesso")
        logger.info("✅ MongoDB conectado")
        await create_indexes()
        
        # ✅ NOVO: Auto-inicializar prompts padrão se não existirem
        await auto_initialize_prompts()
        
    except Exception as e:
        logger.error(f"❌ Erro na startup: {e}")
        raise

async def auto_initialize_prompts():
    """
    Auto-inicializar prompts padrão na startup se não existirem
    """
    try:
        result = await prompt_service.create_default_prompts()
        logger.info(
            "✅ Auto-inicialização concluída: %s prompts criados de %s",
            result.get("created_count", 0),
            result.get("total_prompts", 0),
        )
            
    except Exception as e:
        logger.error(f"❌ Erro na auto-inicialização de prompts: {e}")
        # Não fazer raise aqui para não impedir o startup da aplicação

@app.on_event("shutdown")
async def shutdown_event():
    """Fechar conexões no shutdown"""
    try:
        close_mongodb()
        logger.info("✅ Conexões fechadas com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro no shutdown: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
