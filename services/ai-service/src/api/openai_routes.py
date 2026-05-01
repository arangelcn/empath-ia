"""
Endpoints para integração com OpenAI
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime

from ..services.openai_service import OpenAIService
from ..services.token_economy_service import TokenEconomyService
from ..services.session_context_service import SessionContextService
from ..services.redis_performance_service import RedisPerformanceService

# Configurar logging
logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(prefix="/openai", tags=["OpenAI"])

# Inicializar serviços
openai_service = OpenAIService()
token_economy_service = TokenEconomyService()
session_context_service = SessionContextService()
redis_performance_service = RedisPerformanceService()

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    username: str  # ✅ NOVO: Username obrigatório
    user_profile: Optional[Dict[str, Any]] = None  # ✅ NOVO: Perfil completo do usuário
    conversation_history: Optional[List[Dict[str, Any]]] = None
    session_objective: Optional[Dict[str, Any]] = None
    initial_prompt: Optional[str] = None
    previous_session_context: Optional[Dict[str, Any]] = None  # ✅ NOVO: Contexto da sessão anterior
    is_voice_mode: Optional[bool] = False
    trace_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model: str
    session_id: str
    username: str  # ✅ NOVO: Username na resposta
    timestamp: str
    provider: str
    success: bool

@router.post("/chat", response_model=ChatResponse)
async def chat_with_openai(request: ChatRequest):
    """
    Endpoint para conversa com OpenAI com contexto isolado por usuário
    """
    try:
        # ✅ NOVO: Validar parâmetros obrigatórios
        if not request.username or not request.username.strip():
            raise HTTPException(status_code=400, detail="Username é obrigatório")
        
        if not request.session_id or not request.session_id.strip():
            raise HTTPException(status_code=400, detail="Session ID é obrigatório")
        
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Mensagem é obrigatória")
        
        logger.info(f"🔗 Requisição de chat: {request.username} -> {request.session_id}")
        
        # ✅ NOVO: Cachear perfil do usuário se fornecido
        if request.user_profile:
            openai_service.cache_user_profile(request.username, request.user_profile)
            logger.info(f"💾 Perfil do usuário {request.username} cacheado no AI Service")
        
        result = await openai_service.generate_therapeutic_response(
            user_message=request.message,
            session_id=request.session_id,
            username=request.username,  # ✅ NOVO: Passar username
            conversation_history=request.conversation_history,
            session_objective=request.session_objective,
            initial_prompt=request.initial_prompt,
            previous_session_context=request.previous_session_context  # ✅ NOVO: Contexto da sessão anterior
        )
        
        return ChatResponse(**result)
        
    except ValueError as e:
        # ✅ NOVO: Capturar erros de validação específicos
        logger.error(f"❌ Erro de validação no endpoint OpenAI chat: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erro no endpoint OpenAI chat: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.post("/chat/stream")
async def stream_chat_with_openai(request: ChatRequest):
    """
    Streaming de resposta terapêutica para modo de voz.
    Emite eventos SSE: text_delta, done e error.
    """
    try:
        if not request.username or not request.username.strip():
            raise HTTPException(status_code=400, detail="Username é obrigatório")
        if not request.session_id or not request.session_id.strip():
            raise HTTPException(status_code=400, detail="Session ID é obrigatório")
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Mensagem é obrigatória")

        if request.user_profile:
            openai_service.cache_user_profile(request.username, request.user_profile)

        async def event_stream():
            try:
                async for item in openai_service.generate_therapeutic_response_stream(
                    user_message=request.message,
                    session_id=request.session_id,
                    username=request.username,
                    conversation_history=request.conversation_history,
                    session_objective=request.session_objective,
                    initial_prompt=request.initial_prompt,
                    previous_session_context=request.previous_session_context,
                    trace_id=request.trace_id,
                    is_voice_mode=bool(request.is_voice_mode),
                ):
                    yield _sse(item["event"], item["data"])
            except Exception as exc:
                logger.error("❌ Erro no stream /openai/chat/stream: %s", exc, exc_info=True)
                yield _sse("error", {"error": "Erro interno no stream", "trace_id": request.trace_id})

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar streaming OpenAI: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

def _sse(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"

@router.get("/cache/stats")
async def get_cache_stats():
    """
    Obter estatísticas do cache de contexto por usuário
    """
    try:
        stats = openai_service.get_cache_stats()
        return {
            "success": True,
            "cache_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas do cache: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.post("/user/{username}/profile")
async def cache_user_profile(username: str, profile: dict):
    """
    Cachear perfil do usuário para personalização
    """
    try:
        if not username or not username.strip():
            raise HTTPException(status_code=400, detail="Username é obrigatório")
        
        if not profile:
            raise HTTPException(status_code=400, detail="Perfil é obrigatório")
        
        # Cachear perfil do usuário
        openai_service.cache_user_profile(username, profile)
        
        return {
            "success": True,
            "message": f"Perfil do usuário {username} cacheado com sucesso",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao cachear perfil do usuário {username}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.get("/user/{username}/profile")
async def get_cached_user_profile(username: str):
    """
    Obter perfil do usuário do cache
    """
    try:
        if not username or not username.strip():
            raise HTTPException(status_code=400, detail="Username é obrigatório")
        
        # Buscar perfil do usuário no cache
        cached_profile = openai_service._get_cached_user_profile(username)
        
        if cached_profile:
            return {
                "success": True,
                "profile": cached_profile,
                "cached": True,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "profile": None,
                "cached": False,
                "message": "Perfil não encontrado no cache",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter perfil do usuário {username}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.delete("/cache/user/{username}")
async def clear_user_cache(username: str):
    """
    Limpar cache específico de um usuário
    """
    try:
        if not username or not username.strip():
            raise HTTPException(status_code=400, detail="Username é obrigatório")
        
        openai_service._clear_user_cache(username)
        
        return {
            "success": True,
            "message": f"Cache do usuário {username} limpo com sucesso",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erro ao limpar cache do usuário {username}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.get("/tracking/stats")
async def get_tracking_stats():
    """
    Obter estatísticas gerais de tracking de todos os usuários
    """
    try:
        stats = openai_service._get_all_users_tracking_stats()
        return {
            "success": True,
            "tracking_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas de tracking: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.get("/tracking/user/{username}")
async def get_user_tracking_stats(username: str):
    """
    Obter estatísticas de tracking específicas de um usuário
    """
    try:
        if not username or not username.strip():
            raise HTTPException(status_code=400, detail="Username é obrigatório")
        
        stats = openai_service._get_user_session_stats(username)
        return {
            "success": True,
            "user_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas de tracking do usuário {username}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.post("/tracking/cleanup")
async def cleanup_tracking_data():
    """
    Limpar dados de tracking antigos manualmente
    """
    try:
        openai_service._cleanup_old_tracking_data()
        return {
            "success": True,
            "message": "Limpeza de dados de tracking executada com sucesso",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erro ao limpar dados de tracking: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.get("/status")
async def get_openai_status():
    """
    Verificar status do serviço OpenAI com informações de cache
    """
    try:
        service_status = openai_service.get_service_status()
        cache_stats = openai_service.get_cache_stats()
        
        return {
            "success": True,
            "service_status": service_status,
            "cache_stats": cache_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erro ao obter status do serviço: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.post("/test")
async def test_openai_connection():
    """
    Teste simples de conexão com a cadeia LLM configurada
    """
    try:
        # Teste com mensagem simples
        test_message = "Olá, como você está?"
        result = await openai_service.generate_therapeutic_response(
            user_message=test_message,
            session_id="test",
            username="test"
        )
        service_status = openai_service.get_service_status()
        
        return {
            "status": "success",
            "test_message": test_message,
            "result": result,
            "openai_available": service_status["openai_available"],
            "local_available": service_status["local_available"],
            "primary_provider": service_status["primary_provider"],
            "fallback_provider": service_status["fallback_provider"]
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no teste OpenAI: {e}")
        service_status = openai_service.get_service_status()
        return {
            "status": "error",
            "error": str(e),
            "openai_available": service_status["openai_available"],
            "local_available": service_status["local_available"]
        }

@router.post("/generate-session-context")
async def generate_session_context(request: dict):
    """
    Gerar contexto de uma sessão terapêutica baseado na conversa
    Usa MongoDB como repositório principal e Redis para performance
    """
    try:
        conversation_text = request.get("conversation_text", "")
        emotions_data = request.get("emotions_data", [])
        session_id = request.get("session_id", "")
        username = request.get("username", "")
        
        if not conversation_text:
            raise HTTPException(status_code=400, detail="conversation_text é obrigatório")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id é obrigatório")
        
        if not username:
            raise HTTPException(status_code=400, detail="username é obrigatório")
        
        # ✅ NOVO: Usar TokenEconomyService para economia de tokens
        logger.info(f"🚀 Processando contexto da sessão {session_id} (usuário: {username})")
        
        context_data, source, tokens_saved = await token_economy_service.get_or_generate_session_context(
            conversation_text, 
            session_id, 
            username, 
            emotions_data
        )
        
        if not context_data:
            raise HTTPException(status_code=500, detail="Falha ao gerar contexto da sessão")
        
        return {
            "success": True,
            "context": context_data,
            "cached": tokens_saved,
            "source": source,
            "tokens_saved": tokens_saved,
            "timestamp": datetime.now().isoformat(),
            "explanation": {
                "mongodb_reuse": "Contexto reutilizado do repositório principal MongoDB",
                "redis_performance": "Contexto obtido do cache de performance Redis",
                "openai_generated": "Contexto gerado pelo OpenAI e salvo no repositório"
            }.get(source, "Fonte desconhecida")
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar contexto da sessão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/generate-next-session")
async def generate_next_session(request: dict):
    """
    Gerar próxima sessão terapêutica personalizada baseada no contexto do usuário
    Usa MongoDB como repositório principal e Redis para performance
    """
    try:
        user_profile = request.get("user_profile", {})
        session_context = request.get("session_context", {})
        current_session_id = request.get("current_session_id", "")
        username = request.get("username", "")
        
        if not session_context:
            raise HTTPException(status_code=400, detail="session_context é obrigatório")
        
        if not current_session_id:
            raise HTTPException(status_code=400, detail="current_session_id é obrigatório")
        
        if not username:
            raise HTTPException(status_code=400, detail="username é obrigatório")
        
        # ✅ NOVO: Usar TokenEconomyService para economia de tokens
        logger.info(f"🚀 Processando próxima sessão para {username} (sessão atual: {current_session_id})")
        
        next_session_data, source, tokens_saved = await token_economy_service.get_or_generate_next_session(
            user_profile, 
            session_context, 
            current_session_id, 
            username
        )
        
        if not next_session_data:
            raise HTTPException(status_code=500, detail="Falha ao gerar próxima sessão")
        
        return {
            "success": True,
            "next_session": next_session_data,
            "cached": tokens_saved,
            "source": source,
            "tokens_saved": tokens_saved,
            "timestamp": datetime.now().isoformat(),
            "explanation": {
                "mongodb_reuse": "Próxima sessão reutilizada do repositório principal MongoDB",
                "redis_performance": "Próxima sessão obtida do cache de performance Redis",
                "openai_generated": "Próxima sessão gerada pelo OpenAI e salva no repositório"
            }.get(source, "Fonte desconhecida")
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar próxima sessão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ✅ NOVOS ENDPOINTS PARA NOVA ARQUITETURA

@router.post("/session/start")
async def start_session_with_economy(request: dict):
    """
    Iniciar sessão com economia de tokens
    """
    try:
        session_id = request.get("session_id", "")
        username = request.get("username", "")
        initial_data = request.get("initial_data", {})
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id é obrigatório")
        
        if not username:
            raise HTTPException(status_code=400, detail="username é obrigatório")
        
        # Iniciar sessão com economia de tokens
        success = await token_economy_service.start_session_with_economy(session_id, username, initial_data)
        
        return {
            "success": success,
            "session_id": session_id,
            "username": username,
            "message": "Sessão iniciada com otimização de economia de tokens",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao iniciar sessão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/session/end")
async def end_session_with_economy(request: dict):
    """
    Encerrar sessão com persistência no MongoDB
    """
    try:
        session_id = request.get("session_id", "")
        username = request.get("username", "")
        final_context = request.get("final_context", {})
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id é obrigatório")
        
        if not username:
            raise HTTPException(status_code=400, detail="username é obrigatório")
        
        # Encerrar sessão com persistência
        success = await token_economy_service.end_session_with_economy(session_id, username, final_context)
        
        return {
            "success": success,
            "session_id": session_id,
            "username": username,
            "message": "Sessão encerrada e contexto persistido no MongoDB",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao encerrar sessão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/economy/statistics")
async def get_economy_statistics():
    """
    Obter estatísticas de economia de tokens
    """
    try:
        stats = token_economy_service.get_economy_statistics()
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de economia: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/economy/user/{username}")
async def get_user_economy_stats(username: str):
    """
    Obter estatísticas de economia específicas do usuário
    """
    try:
        stats = await token_economy_service.get_user_economy_stats(username)
        return {
            "success": True,
            "user_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do usuário {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/repository/user/{username}/sessions")
async def get_user_sessions(username: str, limit: int = 50, include_inactive: bool = False):
    """
    Listar sessões do usuário no repositório MongoDB
    """
    try:
        sessions = await session_context_service.list_user_sessions(username, limit, include_inactive)
        return {
            "success": True,
            "username": username,
            "sessions": sessions,
            "total_found": len(sessions),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter sessões do usuário {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/repository/statistics")
async def get_repository_statistics():
    """
    Obter estatísticas do repositório MongoDB
    """
    try:
        stats = await session_context_service.get_session_statistics()
        return {
            "success": True,
            "mongodb_repository_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do repositório: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/performance/statistics")
async def get_performance_statistics():
    """
    Obter estatísticas de performance do Redis
    """
    try:
        stats = redis_performance_service.get_performance_stats()
        return {
            "success": True,
            "redis_performance_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de performance: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/performance/active-sessions")
async def get_active_sessions():
    """
    Obter sessões ativas no Redis
    """
    try:
        active_sessions = redis_performance_service.get_active_sessions()
        return {
            "success": True,
            "active_sessions": active_sessions,
            "total_active": len(active_sessions),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter sessões ativas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.delete("/performance/user/{username}")
async def clear_user_performance_cache(username: str):
    """
    Limpar cache de performance de um usuário
    """
    try:
        success = redis_performance_service.clear_user_performance_cache(username)
        return {
            "success": success,
            "username": username,
            "message": "Cache de performance limpo para o usuário",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao limpar cache de performance do usuário {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
