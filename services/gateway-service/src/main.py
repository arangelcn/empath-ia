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

# Instância do serviço de chat
chat_service = ChatService()

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
            "data": result
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
    """Salva as preferências do usuário (nome, voz) para uma sessão."""
    try:
        # Garante que a conversa exista antes de tentar atualizá-la
        await chat_service.start_or_get_conversation(request.session_id)

        updated_data = {
            "user_preferences": {
                "username": request.username,
                "selected_voice": request.selected_voice,
                "completed_welcome": True
            }
        }
        
        result = await chat_service.update_conversation_data(request.session_id, updated_data)
        
        if result:
            return {"success": True, "message": "Preferências salvas com sucesso."}
        else:
            raise HTTPException(status_code=404, detail="Sessão não encontrada após a criação.")
            
    except Exception as e:
        logger.error(f"Erro ao salvar preferências: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/status/{session_id}")
async def get_user_status(session_id: str):
    """Verifica se o usuário já completou a tela de boas-vindas."""
    try:
        conversation = await chat_service.get_conversation_by_session_id(session_id)
        
        if conversation:
            preferences = conversation.get("user_preferences", {})
            completed_welcome = preferences.get("completed_welcome", False)
            username = preferences.get("username")
            return {"success": True, "data": {"is_onboarded": completed_welcome, "username": username}}
        else:
            return {"success": True, "data": {"is_onboarded": False, "username": None}}
            
    except Exception as e:
        logger.error(f"Erro ao verificar status do usuário: {e}")
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

# Endpoint para sessão completa
@app.post("/api/session/complete")
async def complete_session(request: Request):
    """
    Endpoint orquestrado que combina análise emocional + resposta IA + avatar
    TODO: Implementar orquestração completa
    """
    body = await request.json()
    
    return {
        "session_id": "session-123",
        "status": "development",
        "message": "Orquestração completa em desenvolvimento",
        "note": "Use /api/chat/send para chat com persistência",
        "steps": [
            "1. Análise emocional (emotion-service)",
            "2. Processamento IA (ai-service)", 
            "3. Geração avatar (avatar-service)"
        ],
        "input": body
    }

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