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
from .models.database import init_mongodb, close_mongodb
from .services.chat_service import ChatService
from .services.user_service import UserService
from .services.therapeutic_session_service import TherapeuticSessionService
from .services.user_therapeutic_session_service import UserTherapeuticSessionService
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
        result = await chat_service.process_user_message(
            session_id=request.session_id or "default",
            user_message=request.message
        )
        
        return {
            "success": True,
            "data": {
                "ai_response": result
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
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
    """Registrar login do usuário e clonar sessões terapêuticas"""
    try:
        success = await user_service.update_last_login(username)
        
        if not success:
            # Se o usuário não existe, criar automaticamente
            await user_service.create_user(username=username)
            await user_service.update_last_login(username)
        
        # Clonar sessões terapêuticas para o usuário
        clone_result = await user_therapeutic_session_service.clone_sessions_for_user(username)
        
        # Desbloquear a primeira sessão se não houver nenhuma desbloqueada
        unlock_result = await user_therapeutic_session_service.unlock_first_session(username)
        
        return {
            "success": True,
            "message": "Login registrado com sucesso",
            "sessions_cloned": clone_result["cloned_count"],
            "total_templates": clone_result["total_templates"],
            "first_session_unlocked": unlock_result
        }
        
    except Exception as e:
        logger.error(f"Erro ao registrar login: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    """Proxy para análise emocional em tempo real (Base64)"""
    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['emotion']}/analyze-realtime",
                json=body,
                timeout=30
            )
            return response.json()
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
        "features": ["mongodb", "chat_persistence", "session_management"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 