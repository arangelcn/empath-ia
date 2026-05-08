from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar app FastAPI
app = FastAPI(
    title="empatIA AI Service",
    description="Serviço de IA para conversas terapêuticas com psicólogo Rogers",
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

# Incluir rotas do OpenAI
from .api import chat_routes
from .services.deps import llm_service as openai_service, token_economy_svc as token_economy_service
app.include_router(chat_routes.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-service",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "empatIA AI Service",
        "description": "Serviço de IA para conversas terapêuticas",
        "docs": "/docs"
    }

# Evento de startup para inicializar nova arquitetura
@app.on_event("startup")
async def startup_event():
    """Inicializar nova arquitetura MongoDB + Redis na startup"""
    try:
        await token_economy_service.initialize()
        logger.info("✅ TokenEconomyService inicializado com sucesso")
        logger.info("✅ Nova arquitetura MongoDB (repositório) + Redis (performance) inicializada")

        await verify_and_initialize_prompts()

    except Exception as e:
        logger.warning(f"⚠️ Erro ao inicializar nova arquitetura: {e}")

async def verify_and_initialize_prompts():
    """
    Verificar se existem prompts no banco de dados e inicializar se necessário
    """
    try:
        logger.info("🔍 Verificando prompts no banco de dados...")
        
        # Tentar buscar prompt principal do sistema
        system_prompt = await openai_service.prompt_client.get_prompt("system_rogers")
        
        if not system_prompt:
            logger.warning("⚠️ Prompts não encontrados no banco. Inicializando prompts padrão...")
            
            # Chamar endpoint do Gateway para inicializar prompts padrão
            await initialize_prompts_via_gateway()
        else:
            logger.info("✅ Prompts encontrados no banco de dados")
            
    except Exception as e:
        logger.error(f"❌ Erro ao verificar prompts: {e}")

async def initialize_prompts_via_gateway():
    """
    Inicializar prompts padrão via Gateway Service
    """
    try:
        import httpx
        gateway_url = os.getenv("GATEWAY_SERVICE_URL", "http://gateway:8000")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{gateway_url}/api/prompts/initialize")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Prompts inicializados via Gateway: {result.get('created_count', 0)} prompts criados")
            else:
                logger.error(f"❌ Erro ao inicializar prompts via Gateway: {response.status_code}")
                
    except Exception as e:
        logger.error(f"❌ Erro ao chamar inicialização de prompts no Gateway: {e}")
        logger.warning("⚠️ Sistema irá usar prompts hardcodados como fallback")

# Chat endpoint (melhorado)
@app.post("/chat")
async def chat(message: dict):
    """
    Endpoint principal para conversas de chat com isolamento por usuário
    """
    user_message = message.get("message", "")
    session_id = message.get("session_id", "default")
    username = message.get("username", "")  # ✅ NOVO: Username obrigatório
    user_profile = message.get("user_profile", None)  # ✅ NOVO: Perfil do usuário
    conversation_history = message.get("conversation_history", None)
    session_objective = message.get("session_objective", None)
    initial_prompt = message.get("initial_prompt", None)
    previous_session_context = message.get("previous_session_context", None)  # ✅ EXTRAIR: Contexto da sessão anterior
    
    # ✅ DEBUG: Log detalhado do que foi recebido
    logger.info(f"🔍 DEBUG ENDPOINT /chat - Campos recebidos:")
    logger.info(f"  - message: {'✅' if user_message else '❌'}")
    logger.info(f"  - session_id: {'✅' if session_id else '❌'}")
    logger.info(f"  - username: {'✅' if username else '❌'}")
    logger.info(f"  - user_profile: {'✅' if user_profile else '❌'}")
    logger.info(f"  - conversation_history: {'✅' if conversation_history else '❌'} ({len(conversation_history) if conversation_history else 0} mensagens)")
    logger.info(f"  - session_objective: {'✅' if session_objective else '❌'}")
    logger.info(f"  - initial_prompt: {'✅' if initial_prompt else '❌'}")
    logger.info(f"  - previous_session_context: {'✅' if previous_session_context else '❌'}")
    
    if previous_session_context:
        logger.info(f"🔍 DEBUG - previous_session_context recebido: {len(str(previous_session_context))} chars")
        logger.info(f"🔍 DEBUG - Chaves do previous_session_context: {list(previous_session_context.keys()) if isinstance(previous_session_context, dict) else 'Não é dict'}")
    else:
        logger.warning(f"⚠️ DEBUG - previous_session_context está VAZIO ou NULO!")
    
    try:
        # ✅ NOVO: Validar parâmetros obrigatórios
        if not username or not username.strip():
            logger.error("❌ Username não fornecido no chat endpoint")
            return {
                "error": "Username é obrigatório",
                "service": "ai-service",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
        
        if not session_id or not session_id.strip():
            logger.error("❌ Session ID não fornecido no chat endpoint")
            return {
                "error": "Session ID é obrigatório",
                "service": "ai-service",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
        
        if not user_message or not user_message.strip():
            logger.error("❌ Mensagem não fornecida no chat endpoint")
            return {
                "error": "Mensagem é obrigatória",
                "service": "ai-service",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"🔗 Chat endpoint: {username} -> {session_id}")
        
        # ✅ NOVO: Cachear perfil do usuário se fornecido
        if user_profile:
            openai_service.cache_user_profile(username, user_profile)
            logger.info(f"💾 Perfil do usuário {username} cacheado no AI Service")
        
        # Usar OpenAI se disponível, senão fallback
        response = await openai_service.generate_therapeutic_response(
            user_message=user_message,
            session_id=session_id,
            username=username,  # ✅ NOVO: Passar username
            conversation_history=conversation_history,
            session_objective=session_objective,
            initial_prompt=initial_prompt,
            previous_session_context=previous_session_context  # ✅ CORRIGIDO: Usar variável extraída
        )
        
        # Verificar se response é uma coroutine
        if hasattr(response, '__await__'):
            response = await response
            
        return {
            "response": response["response"],
            "service": "ai-service",
            "status": "active",
            "session_id": session_id,
            "username": username,  # ✅ NOVO: Incluir username na resposta
            "timestamp": datetime.now().isoformat(),
            "provider": response.get("provider", "fallback"),
            "model": response.get("model", "fallback")
        }
        
    except ValueError as e:
        # ✅ NOVO: Capturar erros de validação específicos
        logger.error(f"❌ Erro de validação no chat: {e}")
        return {
            "error": str(e),
            "service": "ai-service",
            "status": "error",
            "session_id": session_id,
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "provider": "error",
            "model": "error"
        }
    except Exception as e:
        logger.error(f"❌ Erro no chat: {e}")
        # Fallback para resposta básica usando OpenAIService
        try:
            fallback_response = await openai_service._fallback_response(user_message, username, conversation_history)
            return {
                "response": fallback_response["response"],
                "service": "ai-service",
                "status": "active",
                "session_id": session_id,
                "username": username,
                "timestamp": datetime.now().isoformat(),
                "provider": "fallback_emergency",
                "model": "fallback"
            }
        except Exception as fallback_error:
            logger.error(f"❌ Erro no fallback: {fallback_error}")
            return {
                "response": "Estou aqui para ajudar. Pode me contar mais sobre o que está sentindo?",
                "service": "ai-service",
                "status": "active",
                "session_id": session_id,
                "username": username,
                "timestamp": datetime.now().isoformat(),
                "provider": "hardcoded_fallback",
                "model": "fallback"
            }

# Endpoint de completação direta (sem persona terapêutica) — usado por serviços internos
@app.post("/util/complete")
async def util_complete(body: dict):
    """
    Completação LLM sem pipeline terapêutico.
    Aceita { "prompt": str, "system": str (opcional), "max_tokens": int (opcional) }.
    Retorna { "text": str, "success": bool }.
    Uso interno: gateway usa para gerar títulos de sessão.
    """
    prompt = body.get("prompt", "").strip()
    if not prompt:
        return {"success": False, "text": ""}

    system = body.get("system", "Você é um assistente que responde de forma concisa e objetiva.")
    max_tokens = int(body.get("max_tokens", 256))

    try:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        text = await openai_service._call_llm(messages, max_tokens=max_tokens, temperature=0.3)
        return {"success": bool(text), "text": text or ""}
    except Exception as e:
        logger.error(f"❌ util/complete error: {e}")
        return {"success": False, "text": ""}


# Endpoint para configurações
@app.get("/config")
async def get_config():
    """Retorna configurações do serviço"""
    openai_status = openai_service.get_service_status()
    
    return {
        "openai_configured": openai_status["openai_configured"],
        "model": openai_status["active_model"],
        "active_model": openai_status["active_model"],
        "active_provider": openai_status["active_provider"],
        "active_mode": openai_status["active_mode"],
        "primary_provider": openai_status["primary_provider"],
        "fallback_provider": openai_status["fallback_provider"],
        "provider_order": openai_status["provider_order"],
        "local_available": openai_status["local_available"],
        "local_file_available": openai_status["local_file_available"],
        "local_runtime_loadable": openai_status["local_runtime_loadable"],
        "local_load_error": openai_status["local_load_error"],
        "openai_available": openai_status["openai_available"],
        "local_model_path": openai_status["local_model_path"],
        "local_llm": openai_status["local_llm"],
        "service_port": os.getenv("AI_SERVICE_PORT", "8001"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "provider": openai_status["active_provider"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 
