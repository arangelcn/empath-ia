from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import httpx
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

# Importar modelos e serviços
from .models.database import init_mongodb, close_mongodb, get_collection
from .services.chat_service import ChatService
from .services.user_service import UserService
from .services.therapeutic_session_service import TherapeuticSessionService
from .services.user_therapeutic_session_service import UserTherapeuticSessionService
from .services.user_emotion_service import UserEmotionService
from .services.prompt_service import PromptService
from .api.admin import router as admin_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Modelos Pydantic para requests
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    session_objective: Optional[Dict[str, Any]] = None
    is_voice_mode: Optional[bool] = False  # ✅ NOVO: Indicador de modo de voz

class ConversationRequest(BaseModel):
    session_id: str

class UserPreferencesRequest(BaseModel):
    session_id: str
    username: str
    selected_voice: str
    voice_enabled: bool = True

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

# URLs dos serviços (serão configurados via variáveis de ambiente)
SERVICE_URLS = {
    "ai": os.getenv("AI_SERVICE_URL", "http://ai-service:8001"),
    "avatar": os.getenv("AVATAR_SERVICE_URL", "http://avatar-service:8002"),
    "emotion": os.getenv("EMOTION_SERVICE_URL", "http://emotion-service:8003"),
    "voice": os.getenv("VOICE_SERVICE_URL", "http://voice-service:8004")
}

# Instâncias dos serviços
chat_service = ChatService()
user_service = UserService()
therapeutic_session_service = TherapeuticSessionService()
user_therapeutic_session_service = UserTherapeuticSessionService()
user_emotion_service = UserEmotionService()
prompt_service = PromptService()

# Incluir rotas de administração
app.include_router(admin_router)

# Eventos de startup e shutdown
@app.on_event("startup")
async def startup_event():
    """Inicializar conexões na startup"""
    try:
        init_mongodb()
        logger.info("✅ Gateway Service iniciado com sucesso")
        logger.info("✅ MongoDB conectado")
    except Exception as e:
        logger.error(f"❌ Erro na startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Fechar conexões no shutdown"""
    try:
        close_mongodb()
        logger.info("✅ Conexões fechadas com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro no shutdown: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "gateway-service",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "features": ["chat_persistence", "mongodb", "conversation_history"],
        "services": SERVICE_URLS
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "empatIA Gateway Service v2.0",
        "description": "API Gateway com persistência MongoDB",
        "docs": "/docs",
        "services": list(SERVICE_URLS.keys()),
        "new_features": [
            "Persistência de conversas",
            "Histórico de mensagens", 
            "MongoDB integrado",
            "Session management"
        ]
    }

# ===== NOVOS ENDPOINTS DE CHAT COM PERSISTÊNCIA =====

@app.post("/api/chat/send")
async def send_message(request: ChatRequest):
    """
    Enviar mensagem e receber resposta com persistência
    """
    try:
        logger.info(f"🌐 GATEWAY: Recebendo mensagem para session_id={request.session_id}, VoiceMode={request.is_voice_mode}")
        
        result = await chat_service.process_user_message(
            session_id=request.session_id or "default",
            user_message=request.message,
            session_objective=request.session_objective,
            is_voice_mode=request.is_voice_mode  # ✅ NOVO: Passar indicador de VoiceMode
        )
        
        logger.info(f"✅ GATEWAY: Processamento concluído com sucesso para session_id={request.session_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ GATEWAY: Erro ao processar mensagem: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Obter histórico completo de uma conversa
    """
    try:
        history = await chat_service.get_conversation_history(session_id)
        
        return {
            "success": True,
            "data": history
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/api/chat/start")
async def start_conversation(request: ConversationRequest):
    """
    Iniciar ou recuperar conversa existente
    """
    try:
        conversation = await chat_service.start_or_get_conversation(request.session_id)
        
        return {
            "success": True,
            "data": conversation
        }
        
    except Exception as e:
        logger.error(f"Erro ao iniciar conversa: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/api/user/preferences")
async def save_user_preferences(request: UserPreferencesRequest):
    """Salva as preferências do usuário (nome, voz, voz habilitada) para uma sessão."""
    try:
        # Garante que a conversa exista antes de tentar atualizá-la
        await chat_service.start_or_get_conversation(request.session_id)

        updated_data = {
            "user_preferences": {
                "username": request.username,
                "selected_voice": request.selected_voice,
                "voice_enabled": request.voice_enabled,
                "completed_welcome": True
            }
        }
        
        result = await chat_service.update_conversation_data(request.session_id, updated_data)
        
        if result:
            return {"success": True, "message": "Preferências salvas com sucesso."}
        else:
            return {"success": False, "message": "Erro ao salvar preferências."}
            
    except Exception as e:
        logger.error(f"Erro ao salvar preferências: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/user/status/{session_id}")
async def get_user_status(session_id: str):
    """Obtém o status de onboarding do usuário para uma sessão."""
    try:
        conversation = await chat_service.get_conversation_by_session_id(session_id)
        
        if not conversation:
            return {
                "success": True,
                "data": {
                    "is_onboarded": False,
                    "username": None,
                    "selected_voice": None
                }
            }
        
        user_prefs = conversation.get("user_preferences", {})
        
        return {
            "success": True,
            "data": {
                "is_onboarded": user_prefs.get("completed_welcome", False),
                "username": user_prefs.get("username"),
                "selected_voice": user_prefs.get("selected_voice")
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter status do usuário: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ===== ENDPOINTS DE SESSÕES TERAPÊUTICAS =====

@app.get("/api/sessions")
async def get_therapeutic_sessions(active_only: bool = True, limit: int = 50):
    """
    Obter sessões terapêuticas ativas (endpoint público)
    """
    try:
        result = await therapeutic_session_service.list_sessions(
            limit=limit,
            offset=0,
            active_only=active_only
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao buscar sessões terapêuticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/sessions/{session_id}")
async def get_therapeutic_session(session_id: str):
    """
    Obter detalhes de uma sessão terapêutica específica
    """
    try:
        session = await therapeutic_session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Sessão terapêutica não encontrada")
        
        return {
            "success": True,
            "data": {
                "id": str(session["_id"]),
                "session_id": session["session_id"],
                "title": session["title"],
                "subtitle": session["subtitle"],
                "objective": session["objective"],
                "initial_prompt": session["initial_prompt"],
                "is_active": session["is_active"],
                "created_at": session["created_at"].isoformat(),
                "updated_at": session["updated_at"].isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter sessão terapêutica: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/api/session/complete")
async def complete_session(request: Request):
    """
    Marcar uma sessão como concluída para um usuário
    """
    try:
        data = await request.json()
        session_id = data.get("session_id")
        user_id = data.get("user_id")
        
        if not session_id or not user_id:
            raise HTTPException(status_code=400, detail="session_id e user_id são obrigatórios")
        
        # Aqui você pode implementar a lógica para marcar a sessão como concluída
        # Por exemplo, salvar no banco de dados o progresso do usuário
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "user_id": user_id,
                "completed_at": datetime.now().isoformat(),
                "message": "Sessão marcada como concluída"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao marcar sessão como concluída: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ===== ENDPOINTS DE SESSÕES TERAPÊUTICAS DOS USUÁRIOS =====

@app.get("/api/user/{username}/sessions")
async def get_user_sessions(username: str, status: Optional[str] = None):
    """Obter sessões terapêuticas de um usuário"""
    try:
        sessions = await user_therapeutic_session_service.get_user_sessions(username, status)
        
        return {
            "success": True,
            "data": {
                "username": username,
                "sessions": sessions,
                "total": len(sessions)
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter sessões do usuário {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/user/{username}/sessions/{session_id}")
async def get_user_session(username: str, session_id: str):
    """Obter uma sessão específica de um usuário"""
    try:
        session = await user_therapeutic_session_service.get_user_session(username, session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        return {
            "success": True,
            "data": session
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter sessão {session_id} do usuário {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/user/{username}/sessions/{session_id}/sequence")
async def get_user_session_sequence(username: str):
    """Obter sequência ordenada de sessões do usuário (incluindo sessões dinâmicas)"""
    try:
        sessions = await user_therapeutic_session_service.get_user_session_sequence(username)
        
        return {
            "success": True,
            "data": {
                "username": username,
                "sessions": sessions,
                "total": len(sessions),
                "sequence_info": {
                    "dynamic_sessions": len([s for s in sessions if s.get("personalized", False)]),
                    "template_sessions": len([s for s in sessions if not s.get("personalized", False)]),
                    "completed_sessions": len([s for s in sessions if s.get("status") == "completed"]),
                    "available_sessions": len([s for s in sessions if s.get("status") == "unlocked"])
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter sequência de sessões do usuário {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/api/user/{username}/sessions/create-dynamic")
async def create_dynamic_session_manually(username: str, request: Request):
    """Criar sessão dinâmica manualmente (para testes)"""
    try:
        data = await request.json()
        
        # Verificar se pode criar nova sessão
        can_create = await user_therapeutic_session_service.can_create_next_session(username)
        if not can_create:
            return {
                "success": False,
                "error": "Usuário possui sessões pendentes. Complete as sessões existentes primeiro."
            }
        
        # Criar sessão dinâmica
        success = await user_therapeutic_session_service.create_dynamic_session(username, data)
        
        if success:
            return {
                "success": True,
                "message": "Sessão dinâmica criada com sucesso",
                "session_id": data.get("session_id")
            }
        else:
            return {
                "success": False,
                "error": "Falha ao criar sessão dinâmica"
            }
            
    except Exception as e:
        logger.error(f"Erro ao criar sessão dinâmica para {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/user/{username}/sessions/info")
async def get_user_sessions_info(username: str):
    """Obter informações detalhadas sobre as sessões do usuário"""
    try:
        sessions = await user_therapeutic_session_service.get_user_sessions(username)
        latest_completed = await user_therapeutic_session_service.get_latest_completed_session(username)
        can_create_next = await user_therapeutic_session_service.can_create_next_session(username)
        
        return {
            "success": True,
            "data": {
                "username": username,
                "total_sessions": len(sessions),
                "latest_completed_session": latest_completed,
                "can_create_next_session": can_create_next,
                "session_statistics": {
                    "locked": len([s for s in sessions if s.get("status") == "locked"]),
                    "unlocked": len([s for s in sessions if s.get("status") == "unlocked"]),
                    "in_progress": len([s for s in sessions if s.get("status") == "in_progress"]),
                    "completed": len([s for s in sessions if s.get("status") == "completed"]),
                    "dynamic_sessions": len([s for s in sessions if s.get("personalized", False)]),
                    "template_sessions": len([s for s in sessions if not s.get("personalized", False)])
                },
                "dynamic_session_behavior": {
                    "description": "Sistema dinâmico: ao finalizar uma sessão, uma nova sessão personalizada é criada automaticamente baseada no contexto da sessão anterior",
                    "sequence": "session-1 (cadastro) -> session-2 (personalizada) -> session-3 (personalizada) -> ...",
                    "ai_generation": "Cada nova sessão é gerada pelo AI Service com base no perfil do usuário e contexto da sessão anterior",
                    "auto_unlock": "Novas sessões são automaticamente desbloqueadas após criação"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter informações das sessões do usuário {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/api/user/{username}/sessions/{session_id}/unlock")
async def unlock_user_session(username: str, session_id: str):
    """Desbloquear uma sessão para o usuário"""
    try:
        success = await user_therapeutic_session_service.unlock_session(username, session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        return {
            "success": True,
            "message": f"Sessão {session_id} desbloqueada com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao desbloquear sessão {session_id} para usuário {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/api/user/{username}/sessions/{session_id}/start")
async def start_user_session(username: str, session_id: str):
    """Iniciar uma sessão para o usuário"""
    try:
        success = await user_therapeutic_session_service.start_session(username, session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        return {
            "success": True,
            "message": f"Sessão {session_id} iniciada com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao iniciar sessão {session_id} para usuário {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/api/user/{username}/sessions/{session_id}/complete")
async def complete_user_session(username: str, session_id: str, request: Request):
    """Marcar uma sessão como concluída para o usuário"""
    try:
        data = await request.json()
        progress = data.get("progress", 100)
        
        success = await user_therapeutic_session_service.complete_session(username, session_id, progress)
        
        if not success:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        return {
            "success": True,
            "message": f"Sessão {session_id} concluída com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao concluir sessão {session_id} para usuário {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/user/{username}/progress")
async def get_user_progress(username: str):
    """Obter progresso geral do usuário"""
    try:
        progress = await user_therapeutic_session_service.get_user_progress(username)
        
        return {
            "success": True,
            "data": progress
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter progresso do usuário {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ===== ENDPOINTS DE USUÁRIO =====

class UserCreateRequest(BaseModel):
    username: str
    email: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

@app.post("/api/user/create")
async def create_user(request: UserCreateRequest):
    """Criar novo usuário"""
    try:
        result = await user_service.create_user(
            username=request.username,
            email=request.email,
            preferences=request.preferences
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{username}")
async def get_user(username: str):
    """Obter detalhes de um usuário"""
    try:
        user = await user_service.get_user(username)
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return {
            "success": True,
            "data": user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/user/{username}/preferences")
async def update_user_preferences(username: str, preferences: Dict[str, Any]):
    """Atualizar preferências do usuário"""
    try:
        success = await user_service.update_user_preferences(username, preferences)
        
        if not success:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return {
            "success": True,
            "message": "Preferências atualizadas com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar preferências: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/{username}/login")
async def user_login(username: str):
    """Registrar login do usuário e criar session-1 automaticamente"""
    try:
        success = await user_service.update_last_login(username)
        
        if not success:
            # Se o usuário não existe, criar automaticamente
            await user_service.create_user(username=username)
            await user_service.update_last_login(username)
        
        # ✅ NOVO: Criar apenas session-1 automaticamente
        session_1_result = await user_therapeutic_session_service.create_session_1_for_user(username)
        
        # ✅ NOVO: Desbloquear session-1 se for necessário
        unlock_result = await user_therapeutic_session_service.unlock_first_session(username)
        
        return {
            "success": True,
            "message": "Login registrado com sucesso",
            "session_1_creation": session_1_result,
            "unlock_result": unlock_result,
            "system_info": "Sistema de criação gradual (1 a 1) ativado - próximas sessões são criadas automaticamente"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no login do usuário {username}: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/user/{username}/stats")
async def get_user_stats(username: str):
    """Obter estatísticas do usuário"""
    try:
        stats = await user_service.get_user_stats(username)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return {
            "success": True,
            "data": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/conversations")
async def list_conversations(limit: int = 10):
    """
    Listar conversas recentes
    """
    try:
        conversations = await chat_service.list_recent_conversations(limit)
        
        return {
            "success": True,
            "data": {
                "conversations": conversations,
                "total": len(conversations)
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar conversas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ===== ENDPOINTS LEGADOS (mantidos para compatibilidade) =====

# Health check de todos os serviços
@app.get("/health/all")
async def health_all():
    """Verificar saúde de todos os serviços"""
    results = {}
    
    async with httpx.AsyncClient() as client:
        for service_name, service_url in SERVICE_URLS.items():
            try:
                response = await client.get(f"{service_url}/health", timeout=5)
                results[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response": response.json() if response.status_code == 200 else None
                }
            except Exception as e:
                results[service_name] = {
                    "status": "unreachable",
                    "error": str(e)
                }
    
    return {
        "gateway": "healthy",
        "database": "connected",
        "services": results,
        "timestamp": datetime.now().isoformat()
    }

# Proxy para AI Service (LEGADO - mantido para compatibilidade)
@app.post("/api/ai/chat")
async def ai_chat(request: Request):
    """Proxy para o serviço de IA (LEGADO)"""
    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['ai']}/chat",
                json=body,
                timeout=30
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Serviço AI indisponível: {str(e)}")

# Proxy para Avatar Service
@app.post("/api/avatar/generate")
async def avatar_generate(request: Request):
    """Proxy para geração de avatar"""
    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['avatar']}/generate-avatar",
                json=body,
                timeout=60
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Serviço Avatar indisponível: {str(e)}")

@app.get("/api/avatar/list")
async def avatar_list():
    """Listar avatares disponíveis"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICE_URLS['avatar']}/avatars", timeout=10)
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Serviço Avatar indisponível: {str(e)}")

# Proxy para Emotion Service
@app.post("/api/emotion/analyze-face")
async def emotion_analyze_face(file: UploadFile = File(...)):
    """Proxy para análise facial"""
    async with httpx.AsyncClient() as client:
        try:
            files = {"file": (file.filename, await file.read(), file.content_type)}
            response = await client.post(
                f"{SERVICE_URLS['emotion']}/analyze-facial-expression",
                files=files,
                timeout=30
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Serviço Emotion indisponível: {str(e)}")

@app.post("/api/emotion/analyze-video")
async def emotion_analyze_video(file: UploadFile = File(...)):
    """Proxy para análise de vídeo emocional"""
    async with httpx.AsyncClient() as client:
        try:
            files = {"file": (file.filename, await file.read(), file.content_type)}
            response = await client.post(
                f"{SERVICE_URLS['emotion']}/analyze-video",
                files=files,
                timeout=60
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Serviço Emotion indisponível: {str(e)}")

@app.post("/api/emotion/analyze-realtime")
async def emotion_analyze_realtime(request: Request):
    """Proxy para análise emocional em tempo real (Base64) com salvamento assíncrono"""
    body = await request.json()
    
    # Extrair informações do usuário da request
    username = body.get("username")
    session_id = body.get("session_id") 
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['emotion']}/analyze-realtime",
                json=body,
                timeout=30
            )
            
            emotion_result = response.json()
            
            # Salvar emoção detectada de forma assíncrona (não bloqueia resposta)
            if emotion_result.get("status") == "success" and username and session_id:
                emotion_data = {
                    "username": username,
                    "session_id": session_id,
                    "dominant_emotion": emotion_result.get("dominant_emotion"),
                    "emotions": emotion_result.get("emotions", {}),
                    "confidence": emotion_result.get("confidence", 0),
                    "face_detected": emotion_result.get("face_detected", False)
                }
                
                # Salvar em background sem aguardar
                await user_emotion_service.save_emotion_async(emotion_data)
                
                logger.info(f"🎭 Emoção detectada e agendada para salvamento: {username} - {emotion_result.get('dominant_emotion')}")
            
            return emotion_result
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Serviço Emotion indisponível: {str(e)}")

# Proxy para Voice Service - F5-TTS
@app.post("/api/voice/speak")
async def voice_speak(request: Request):
    """Text-to-speech através do voice service (LEGADO - usar /synthesize)"""
    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        try:
            # Redirecionar para o novo endpoint /synthesize
            response = await client.post(
                f"{SERVICE_URLS['voice']}/api/v1/synthesize",
                json=body,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Serviço Voice indisponível: {str(e)}")

@app.post("/api/voice/synthesize")
async def voice_synthesize(request: Request):
    """Text-to-speech com F5-TTS (NOVO)"""
    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['voice']}/api/v1/synthesize",
                json=body,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Serviço Voice indisponível: {str(e)}")

@app.get("/api/voice/health")
async def voice_health():
    """Status do voice service F5-TTS"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICE_URLS['voice']}/health", timeout=10)
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Serviço Voice indisponível: {str(e)}")

@app.get("/api/voice/config")
async def voice_config():
    """Obter configurações do voice service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICE_URLS['voice']}/api/v1/model-info", timeout=10)
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Serviço Voice indisponível: {str(e)}")

@app.get("/api/voice/models")
async def voice_models():
    """Listar modelos de TTS disponíveis (F5-TTS)"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICE_URLS['voice']}/api/v1/model-info", timeout=10)
            model_info = response.json()
            # Formatar resposta para compatibilidade
            return {
                "available_models": {
                    model_info.get("model_name", "F5-TTS-pt-br"): model_info
                },
                "current_model": model_info.get("model_name", "F5-TTS-pt-br"),
                "descriptions": {
                    model_info.get("model_name", "F5-TTS-pt-br"): "F5-TTS Português Brasileiro"
                }
            }
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Serviço Voice indisponível: {str(e)}")

# Proxy para servir arquivos de áudio
@app.get("/api/voice/audio/{filename}")
async def voice_audio(filename: str):
    """Servir arquivos de áudio gerados pelo voice service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICE_URLS['voice']}/api/v1/audio/{filename}", timeout=30)
            
            if response.status_code == 200:
                return Response(
                    content=response.content,
                    media_type="audio/mpeg",
                    headers={"Content-Disposition": f"inline; filename={filename}"}
                )
            else:
                raise HTTPException(status_code=response.status_code, detail="Arquivo não encontrado")
                
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Serviço Voice indisponível: {str(e)}")

# Configurações do gateway
# ===== ENDPOINTS PARA CONSULTAR EMOÇÕES =====

@app.get("/api/emotions/{username}")
async def get_user_emotions(username: str, session_id: Optional[str] = None, 
                           limit: int = 100, hours_back: int = 24):
    """Obter emoções de um usuário"""
    try:
        emotions = await user_emotion_service.get_user_emotions(
            username=username,
            session_id=session_id,
            limit=limit,
            hours_back=hours_back
        )
        
        return {
            "success": True,
            "data": {
                "username": username,
                "session_id": session_id,
                "emotions": emotions,
                "total": len(emotions),
                "hours_back": hours_back
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar emoções: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emotions/{username}/summary")
async def get_user_emotion_summary(username: str, session_id: Optional[str] = None, 
                                  hours_back: int = 24):
    """Obter resumo das emoções de um usuário"""
    try:
        summary = await user_emotion_service.get_emotion_summary(
            username=username,
            session_id=session_id,
            hours_back=hours_back
        )
        
        return {
            "success": True,
            "data": {
                "username": username,
                "session_id": session_id,
                **summary
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao calcular resumo de emoções: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emotions/{username}/timeline")
async def get_user_emotion_timeline(username: str, session_id: Optional[str] = None, 
                                   hours_back: int = 24, interval_minutes: int = 5):
    """Obter timeline de emoções de um usuário"""
    try:
        timeline = await user_emotion_service.get_emotion_timeline(
            username=username,
            session_id=session_id,
            hours_back=hours_back,
            interval_minutes=interval_minutes
        )
        
        return {
            "success": True,
            "data": {
                "username": username,
                "session_id": session_id,
                "timeline": timeline,
                "hours_back": hours_back,
                "interval_minutes": interval_minutes
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar timeline de emoções: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS DE CONTEXTO DE SESSÃO =====

@app.post("/api/chat/finalize/{session_id}")
async def finalize_session(session_id: str):
    """
    Finalizar sessão manualmente e gerar contexto
    """
    try:
        # ✅ NOVA LÓGICA: Finalizar sessão completa (contexto + status completed)
        result = await chat_service.finalize_session_context(session_id, manual_termination=True)
        
        # ✅ NOVO: Extrair username e session_id original para marcar como completed
        # session_id formato: "username_session-N"
        if "_session-" in session_id:
            # Encontrar a última ocorrência de "_session-" para extrair corretamente
            session_separator_index = session_id.rfind("_session-")
            if session_separator_index != -1:
                username = session_id[:session_separator_index]
                original_session_id = session_id[session_separator_index + 1:]  # session-1, session-2, etc.
                
                logger.info(f"🏁 Finalizando sessão: username={username}, session_id={original_session_id}")
                
                try:
                    # Marcar sessão como completed no banco
                    completion_result = await user_therapeutic_session_service.complete_session(
                        username=username,
                        session_id=original_session_id,
                        progress=100,
                        status="completed"
                    )
                    
                    if completion_result:
                        logger.info(f"✅ Sessão {original_session_id} marcada como completed para {username}")
                        result["session_completed"] = True
                        result["completion_message"] = f"Sessão {original_session_id} finalizada com sucesso!"
                    else:
                        logger.warning(f"⚠️ Não foi possível marcar sessão {original_session_id} como completed")
                        result["session_completed"] = False
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao marcar sessão como completed: {e}")
                    result["session_completed"] = False
                    result["completion_error"] = str(e)
            else:
                logger.warning(f"⚠️ Formato de session_id inválido: {session_id}")
        else:
            logger.warning(f"⚠️ Session_id sem padrão '_session-': {session_id}")
        
        return {
            "success": result.get("success", False),
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao finalizar sessão {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/context/{session_id}")
async def get_session_context(session_id: str):
    """
    Obter contexto salvo de uma sessão
    """
    try:
        context = await chat_service.get_session_context(session_id)
        
        if context:
            return {
                "success": True,
                "data": {
                    "session_id": session_id,
                    "context": context
                }
            }
        else:
            raise HTTPException(status_code=404, detail="Contexto não encontrado para esta sessão")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao obter contexto da sessão {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/conversations-with-context")
async def list_conversations_with_context(limit: int = 10):
    """
    Listar conversas que possuem contexto gerado
    """
    try:
        from .models.database import get_collection
        conversations = get_collection("conversations")
        
        # Buscar conversas que têm contexto
        cursor = conversations.find(
            {"session_context": {"$exists": True}},
            sort=[("context_generated_at", -1)],
            limit=limit
        )
        
        result = []
        async for conv in cursor:
            context = conv.get("session_context", {})
            result.append({
                "session_id": conv["session_id"],
                "username": conv.get("username"),
                "created_at": conv["created_at"].isoformat(),
                "context_generated_at": conv.get("context_generated_at", conv["updated_at"]).isoformat(),
                "manual_termination": conv.get("manual_termination", False),
                "summary": context.get("summary", ""),
                "main_themes": context.get("main_themes", []),
                "emotional_state": context.get("emotional_state", {}),
                "message_count": conv.get("message_count", 0)
            })
        
        return {
            "success": True,
            "data": {
                "conversations": result,
                "total": len(result)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar conversas com contexto: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
async def get_config():
    """Retorna configurações do gateway"""
    return {
        "services": SERVICE_URLS,
        "database": {
            "type": "mongodb",
            "url": os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
            "database": os.getenv("DATABASE_NAME", "empatia_db")
        },
        "timeout_settings": {
            "ai_chat": 30,
            "avatar_generation": 60,
            "emotion_analysis": 30
        },
        "gateway_port": os.getenv("GATEWAY_PORT", "8000"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "version": "2.0.0",
        "features": ["mongodb", "chat_persistence", "session_management", "emotion_tracking", "session_context"]
    }

@app.get("/api/chat/initial-message/{session_id}")
async def get_initial_message(session_id: str):
    """
    Obter mensagem inicial para uma sessão (sem esperar input do usuário)
    """
    try:
        logger.info(f"🎯 Gerando mensagem inicial para sessão: {session_id}")
        
        # Extrair session_id original e username
        username = session_id.split('_')[0] if '_' in session_id else None
        original_session_id = session_id.split('_')[-1] if '_' in session_id else session_id
        
        if not username:
            return {
                "success": False,
                "error": "Username não encontrado no session_id"
            }
        
        # Verificar se já tem mensagens (não é primeira entrada)
        history = await chat_service.get_conversation_history(session_id)
        
        if history.get("history") and len(history["history"]) > 0:
            return {
                "success": False,
                "error": "Sessão já possui mensagens, não precisa de mensagem inicial"
            }
        
        # Gerar mensagem inicial específica para cada tipo de sessão
        if original_session_id == "session-1":
            # Sessão 1: Mensagem de boas-vindas e primeira pergunta
            initial_message = f"""Olá, {username}! 

Eu sou sua assistente terapêutica. É um prazer te conhecer! Para personalizar nossa conversa, vou fazer algumas perguntas sobre você. 

Primeiro, me conta: qual é a sua idade?"""
            
        else:
            # Sessões 2+: Mensagem baseada no contexto da sessão anterior OU perfil do usuário
            try:
                # ✅ CORREÇÃO: Extrair número da sessão de forma mais robusta
                session_number_str = original_session_id.split('-')[1] if '-' in original_session_id else "1"
                current_session_number = int(session_number_str)
                previous_session_number = current_session_number - 1
                previous_session_id = f"{username}_session-{previous_session_number}"
                
                logger.info(f"🔍 DEBUG SESSÃO 2+: current={original_session_id}, previous={previous_session_id}, username={username}")
                
                # ✅ NOVO: Buscar perfil do usuário PRIMEIRO para personalização
                users_collection = get_collection("users")
                user_profile = await users_collection.find_one({"username": username})
                
                # Buscar contexto da sessão anterior
                previous_context = await chat_service.get_session_context(previous_session_id)
                
                logger.info(f"🔍 DEBUG: previous_context encontrado? {previous_context is not None}, user_profile encontrado? {user_profile is not None}")
                
                # ✅ MELHORADO: Usar contexto da sessão anterior + dados do perfil do usuário
                if previous_context:
                    # Extrair temas principais da sessão anterior
                    main_themes = previous_context.get("main_themes", [])
                    emotional_state = previous_context.get("emotional_state", {})
                    key_insights = previous_context.get("key_insights", [])
                    
                    logger.info(f"🔍 DEBUG CONTEXTO ANTERIOR - Temas: {main_themes}, Estado emocional: {emotional_state}")
                    
                    # Gerar mensagem personalizada baseada no contexto anterior
                    if main_themes:
                        themes_text = ", ".join(main_themes[:2])  # Pegar os 2 principais temas
                        initial_message = f"""Olá, {username}! É bom te ver novamente.

Como você está se sentindo desde nossa última conversa? 

Na nossa sessão anterior, conversamos sobre {themes_text}. Gostaria de continuar explorando esses temas ou há algo específico que te trouxe aqui hoje?"""
                    else:
                        initial_message = f"""Olá, {username}! É bom te ver novamente.

Como você está se sentindo desde nossa última conversa? O que te trouxe aqui hoje?"""
                        
                    logger.info(f"✅ Mensagem baseada em contexto anterior gerada para {username} sessão {current_session_number}")
                    
                elif user_profile and user_profile.get("user_profile"):
                    # ✅ NOVO: Usar dados do perfil do usuário para personalização
                    profile = user_profile["user_profile"]
                    personal_info = profile.get("personal_info", {})
                    therapeutic_info = profile.get("therapeutic_info", {})
                    
                    # Extrair informações relevantes para personalização
                    age_info = personal_info.get("idade", {})
                    objectives = therapeutic_info.get("objetivos_identificados", [])
                    motivation = therapeutic_info.get("motivacao_terapia", {})
                    
                    logger.info(f"🔍 DEBUG PERFIL - Objetivos: {objectives}, Motivação: {motivation}")
                    
                    # Criar mensagem personalizada baseada no perfil
                    if current_session_number == 2:
                        if objectives:
                            objectives_text = ", ".join(objectives[:2])
                            initial_message = f"""Olá, {username}! É bom te ver novamente.

Agora que nos conhecemos melhor, esta é nossa segunda sessão terapêutica. 

Lembro que você mencionou interesse em trabalhar com {objectives_text}. Como você está se sentindo desde nossa conversa anterior? Gostaria de explorar esses temas ou há algo específico que te trouxe aqui hoje?"""
                        else:
                            initial_message = f"""Olá, {username}! É bom te ver novamente.

Agora que nos conhecemos melhor, esta é nossa segunda sessão terapêutica. 

Como você está se sentindo desde nossa conversa anterior? Há algo específico que gostaria de explorar hoje, ou prefere que conversemos sobre como você tem se sentido recentemente?"""
                    else:
                        initial_message = f"""Olá, {username}! É bom te ver novamente.

Esta é nossa sessão {current_session_number}. Como você está se sentindo desde nossa última conversa? 

O que te trouxe aqui hoje? Há algo específico que gostaria de conversar comigo?"""
                    
                    logger.info(f"✅ Mensagem personalizada baseada no perfil gerada para {username} sessão {current_session_number}")
                    
                else:
                    # ✅ MELHORADO: Fallback mais inteligente baseado no número da sessão E username
                    import hashlib
                    
                    # Gerar variação baseada no username para mensagens diferentes por usuário
                    username_hash = int(hashlib.md5(username.encode()).hexdigest(), 16) % 3
                    
                    session_2_variations = [
                        f"""Olá, {username}! É bom te ver novamente.

Agora que nos conhecemos melhor, esta é nossa segunda sessão terapêutica. 

Como você está se sentindo desde nossa conversa anterior? Há algo específico que gostaria de explorar hoje?""",
                        
                        f"""Oi, {username}! Que bom que você voltou.

Esta é nossa segunda sessão juntas. Como você tem estado desde que conversamos?

O que você gostaria de compartilhar comigo hoje? Há algo que tem estado em sua mente?""",
                        
                        f"""Olá, {username}! É um prazer te ver novamente.

Agora que já nos conhecemos um pouco, como você está se sentindo hoje?

Há alguma reflexão da nossa primeira conversa que gostaria de continuar explorando, ou algo novo que te trouxe aqui?"""
                    ]
                    
                    other_session_variations = [
                        f"""Olá, {username}! É bom te ver novamente.

Esta é nossa sessão {current_session_number}. Como você está se sentindo hoje?

O que te trouxe aqui? Há algo específico que gostaria de conversar comigo?""",
                        
                        f"""Oi, {username}! Que bom que você voltou.

Como você tem estado desde nossa última conversa? 

O que você gostaria de compartilhar comigo hoje nesta sessão {current_session_number}?""",
                        
                        f"""Olá, {username}! É um prazer te ver novamente.

Como você está se sentindo hoje? Há algo em particular que gostaria de explorar em nossa sessão {current_session_number}?"""
                    ]
                    
                    if current_session_number == 2:
                        initial_message = session_2_variations[username_hash]
                    else:
                        initial_message = other_session_variations[username_hash]
                    
                    logger.warning(f"⚠️ Contexto e perfil não encontrados para {username}. Usando fallback variado para sessão {current_session_number} (variação {username_hash})")
                    
            except Exception as session_error:
                logger.error(f"❌ Erro ao processar sessão 2+ para {username}: {session_error}")
                
                # Fallback em caso de erro (ainda personalizado)
                initial_message = f"""Olá, {username}! É bom te ver novamente.

Como você está se sentindo hoje? O que gostaria de conversar comigo?"""
        
        # Salvar mensagem inicial no histórico
        await chat_service.start_or_get_conversation(session_id)
        message_id = await chat_service._save_message(session_id, "ai", initial_message)
        
        # ✅ DEBUG: Verificar se mensagem foi salva
        logger.info(f"🔍 DEBUG: Mensagem inicial salva com ID: {message_id}")
        
        # ✅ DEBUG: Verificar se consegue recuperar o histórico
        debug_history = await chat_service.get_conversation_history(session_id)
        logger.info(f"🔍 DEBUG: Histórico após salvar - {len(debug_history.get('history', []))} mensagens")
        
        if debug_history.get('history'):
            for i, msg in enumerate(debug_history['history']):
                logger.info(f"🔍 DEBUG: Mensagem {i+1}: type={msg['type']}, content={msg['content'][:50]}...")
        
        # Gerar áudio se necessário
        audio_url = None
        try:
            # Buscar preferências do usuário para áudio
            users_collection = get_collection("users")
            user = await users_collection.find_one({"username": username})
            
            if user and user.get("preferences", {}).get("voice_enabled", True):
                selected_voice = user.get("preferences", {}).get("selected_voice", "pt-BR-Neural2-A")
                audio_url = await chat_service._generate_audio_if_available(initial_message, session_id, selected_voice)
        except Exception as audio_error:
            logger.warning(f"⚠️ Erro ao gerar áudio para mensagem inicial: {audio_error}")
        
        return {
            "success": True,
            "data": {
                "message": {
                    "id": message_id,
                    "type": "ai",
                    "content": initial_message,
                    "audioUrl": audio_url,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "session_id": session_id,
                "is_initial_message": True
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar mensagem inicial: {e}")
        return {
            "success": False,
            "error": f"Erro ao gerar mensagem inicial: {str(e)}"
        }

# === ENDPOINTS DE GERENCIAMENTO DE PROMPTS ===

@app.post("/api/prompts")
async def create_prompt(prompt_data: dict):
    """Criar novo prompt"""
    try:
        result = await prompt_service.create_prompt(prompt_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erro ao criar prompt: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/prompts/{prompt_key}")
async def get_prompt(prompt_key: str):
    """Buscar prompt por chave"""
    try:
        prompt = await prompt_service.get_prompt(prompt_key)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt não encontrado")
        return prompt
    except Exception as e:
        logger.error(f"❌ Erro ao buscar prompt: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/prompts/active/{prompt_key}")
async def get_active_prompt(prompt_key: str):
    """Buscar prompt ativo por chave"""
    try:
        prompt = await prompt_service.get_active_prompt(prompt_key)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt ativo não encontrado")
        return prompt
    except Exception as e:
        logger.error(f"❌ Erro ao buscar prompt ativo: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.put("/api/prompts/{prompt_key}")
async def update_prompt(prompt_key: str, update_data: dict):
    """Atualizar prompt"""
    try:
        result = await prompt_service.update_prompt(prompt_key, update_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar prompt: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.delete("/api/prompts/{prompt_key}")
async def delete_prompt(prompt_key: str):
    """Deletar prompt (soft delete)"""
    try:
        result = await prompt_service.delete_prompt(prompt_key)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erro ao deletar prompt: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/prompts")
async def list_prompts(prompt_type: Optional[str] = None, active_only: bool = True):
    """Listar prompts com filtros"""
    try:
        prompts = await prompt_service.list_prompts(prompt_type=prompt_type, active_only=active_only)
        return {"prompts": prompts}
    except Exception as e:
        logger.error(f"❌ Erro ao listar prompts: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/prompts/type/{prompt_type}")
async def get_prompts_by_type(prompt_type: str):
    """Buscar prompts por tipo"""
    try:
        prompts = await prompt_service.get_prompts_by_type(prompt_type)
        return {"prompts": prompts}
    except Exception as e:
        logger.error(f"❌ Erro ao buscar prompts por tipo: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/prompts/render/{prompt_key}")
async def render_prompt(prompt_key: str, variables: dict):
    """Renderizar prompt com variáveis"""
    try:
        rendered = await prompt_service.render_prompt(prompt_key, variables)
        if not rendered:
            raise HTTPException(status_code=404, detail="Prompt não encontrado ou não pôde ser renderizado")
        return {"rendered_content": rendered}
    except Exception as e:
        logger.error(f"❌ Erro ao renderizar prompt: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/prompts/stats")
async def get_prompt_stats():
    """Obter estatísticas dos prompts"""
    try:
        stats = await prompt_service.get_prompt_stats()
        return stats
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas de prompts: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/prompts/initialize")
async def initialize_default_prompts():
    """Inicializar prompts padrão do sistema"""
    try:
        result = await prompt_service.create_default_prompts()
        return result
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar prompts padrão: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 