from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime
import re
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
from .api.openai_routes import router as openai_router
app.include_router(openai_router)

def generate_therapeutic_response(user_message: str, last_ai_response: str = "") -> str:
    """
    Gera resposta terapêutica de emergência baseada na mensagem do usuário.
    Evita repetir a última resposta da IA quando possível.
    """
    message_lower = user_message.lower()
    
    # Padrões de reconhecimento
    greeting_patterns = ['oi', 'olá', 'hello', 'hi', 'bom dia', 'boa tarde', 'boa noite']
    sadness_patterns = ['triste', 'deprimido', 'depressão', 'mal', 'ruim', 'pessimo', 'horrível']
    anxiety_patterns = ['ansioso', 'ansiedade', 'nervoso', 'preocupado', 'estressado', 'tenso']
    anger_patterns = ['raiva', 'irritado', 'bravo', 'furioso', 'chateado']
    gratitude_patterns = ['obrigado', 'obrigada', 'valeu', 'thanks', 'thank you']
    goodbye_patterns = ['tchau', 'bye', 'adeus', 'até logo', 'até mais']
    
    candidates = []
    
    if any(pattern in message_lower for pattern in greeting_patterns):
        candidates = ["Olá! Sou o Dr. Rogers, seu psicólogo virtual. É um prazer conhecê-lo. Como posso ajudá-lo hoje? Sinta-se à vontade para compartilhar o que está sentindo."]
    
    elif any(pattern in message_lower for pattern in sadness_patterns):
        candidates = ["Entendo que você está passando por um momento difícil. É muito corajoso buscar ajuda e compartilhar seus sentimentos. Pode me contar mais sobre o que está sentindo?"]
    
    elif any(pattern in message_lower for pattern in anxiety_patterns):
        candidates = ["A ansiedade é algo muito comum e tratável. Vamos trabalhar juntos para encontrar estratégias que funcionem para você. Que situações costumam despertar essa ansiedade?"]
    
    elif any(pattern in message_lower for pattern in anger_patterns):
        candidates = [
            "Vejo que você está se sentindo irritado. É importante reconhecer e validar esses sentimentos. Pode me contar o que aconteceu?",
            "Parece que algo te incomodou bastante. Falar sobre isso pode ajudar a processar melhor essas emoções. O que aconteceu?",
            "Entendo que você está frustrado. Às vezes precisamos de um espaço para expressar o que sentimos. Conte-me mais sobre o que está passando.",
        ]
    
    elif any(pattern in message_lower for pattern in gratitude_patterns):
        candidates = ["Fico muito feliz em poder ajudar! É um prazer acompanhá-lo nessa jornada. Como você está se sentindo agora?"]
    
    elif any(pattern in message_lower for pattern in goodbye_patterns):
        candidates = ["Foi um prazer conversar com você hoje. Cuide-se bem e continue cuidando da sua saúde mental. Até a próxima!"]
    
    else:
        candidates = ["Obrigado por compartilhar isso comigo. Pode me contar mais sobre como isso afeta seu dia a dia? Juntos podemos explorar formas de lidar melhor com essa situação."]
    
    # Evitar repetir a última resposta quando há mais de uma opção disponível
    if last_ai_response and len(candidates) > 1:
        alternatives = [r for r in candidates if r.strip() != last_ai_response.strip()]
        if alternatives:
            return alternatives[0]
    
    return candidates[0]

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

# Importar serviços
from .services.openai_service import OpenAIService

# Inicializar serviços
openai_service = OpenAIService()
token_economy_service = None  # Será inicializado na startup

# Evento de startup para inicializar nova arquitetura
@app.on_event("startup")
async def startup_event():
    """Inicializar nova arquitetura MongoDB + Redis na startup"""
    await openai_service.ensure_local_model_ready()
    from .api import openai_routes
    await openai_routes.openai_service.ensure_local_model_ready()

    try:
        from .services.token_economy_service import TokenEconomyService
        token_economy_service = TokenEconomyService()
        await token_economy_service.initialize()
        logger.info("✅ TokenEconomyService inicializado com sucesso")
        logger.info("✅ Nova arquitetura MongoDB (repositório) + Redis (performance) inicializada")
        
        # ✅ NOVO: Verificar e inicializar prompts do banco de dados
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
            # Último recurso - resposta hardcoded
            last_ai = ""
            if conversation_history:
                ai_msgs = [m.get("content", "") for m in conversation_history if m.get("type") in ("ai", "assistant")]
                last_ai = ai_msgs[-1] if ai_msgs else ""
            response_text = generate_therapeutic_response(user_message, last_ai)
            return {
                "response": response_text,
                "service": "ai-service",
                "status": "active",
                "session_id": session_id,
                "username": username,
                "timestamp": datetime.now().isoformat(),
                "provider": "hardcoded_fallback",
                "model": "fallback"
            }

# Endpoint para configurações
@app.get("/config")
async def get_config():
    """Retorna configurações do serviço"""
    openai_status = openai_service.get_service_status()
    
    return {
        "openai_configured": openai_status["openai_configured"],
        "model": openai_status["active_model"],
        "active_model": openai_status["active_model"],
        "primary_provider": openai_status["primary_provider"],
        "fallback_provider": openai_status["fallback_provider"],
        "provider_order": openai_status["provider_order"],
        "local_available": openai_status["local_available"],
        "openai_available": openai_status["openai_available"],
        "local_model_path": openai_status["local_model_path"],
        "service_port": os.getenv("AI_SERVICE_PORT", "8001"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "provider": openai_status["primary_provider"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 
