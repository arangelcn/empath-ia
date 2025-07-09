"""
API endpoints para o painel administrativo
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from ..models.database import get_collection, get_therapeutic_sessions_collection
from ..services.chat_service import ChatService
from ..services.user_service import UserService
from ..services.therapeutic_session_service import TherapeuticSessionService
from ..services.user_emotion_service import UserEmotionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Instâncias dos serviços
chat_service = ChatService()
user_service = UserService()
therapeutic_session_service = TherapeuticSessionService()
user_emotion_service = UserEmotionService()

# Modelos Pydantic para sessões terapêuticas
class TherapeuticSessionCreate(BaseModel):
    session_id: str
    title: str
    subtitle: str
    objective: str
    initial_prompt: str
    is_active: bool = True

class TherapeuticSessionUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    objective: Optional[str] = None
    initial_prompt: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("/stats")
async def get_dashboard_stats():
    """
    Obter estatísticas gerais para o dashboard
    """
    try:
        conversations_collection = get_collection("conversations")
        messages_collection = get_collection("messages")
        
        # Estatísticas básicas
        total_conversations = await conversations_collection.count_documents({})
        total_messages = await messages_collection.count_documents({})
        
        # Conversas ativas (últimas 24h)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        active_conversations = await conversations_collection.count_documents({
            "updated_at": {"$gte": last_24h}
        })
        
        # Estatísticas reais de emoções
        user_emotions_collection = get_collection("user_emotions")
        emotions_analyzed = await user_emotions_collection.count_documents({
            "timestamp": {"$gte": last_24h}
        })
        
        return {
            "success": True,
            "data": {
                "total_users": total_conversations,
                "active_sessions": active_conversations,
                "emotions_analyzed": int(emotions_analyzed),
                "system_alerts": 0,  # Mockado por enquanto
                "total_messages": total_messages,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations")
async def get_conversations_list(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None
):
    """
    Listar conversas com paginação e busca
    """
    try:
        conversations_collection = get_collection("conversations")
        
        # Filtro de busca
        filter_query = {}
        if search:
            filter_query = {
                "$or": [
                    {"session_id": {"$regex": search, "$options": "i"}},
                    {"user_preferences.username": {"$regex": search, "$options": "i"}}
                ]
            }
        
        # Obter conversas com paginação
        cursor = conversations_collection.find(filter_query).sort("updated_at", -1).skip(offset).limit(limit)
        conversations = await cursor.to_list(length=limit)
        
        # Contar total para paginação
        total = await conversations_collection.count_documents(filter_query)
        
        # Formatar dados
        formatted_conversations = []
        for conv in conversations:
            formatted_conversations.append({
                "id": str(conv["_id"]),
                "session_id": conv["session_id"],
                "username": conv.get("user_preferences", {}).get("username", "Usuário Anônimo"),
                "created_at": conv["created_at"].isoformat(),
                "updated_at": conv["updated_at"].isoformat(),
                "message_count": len(conv.get("messages", [])),
                "status": "active" if (datetime.utcnow() - conv["updated_at"]).days < 1 else "inactive"
            })
        
        return {
            "success": True,
            "data": {
                "conversations": formatted_conversations,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_next": offset + limit < total
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar conversas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{session_id}")
async def get_conversation_details(session_id: str):
    """
    Obter detalhes completos de uma conversa
    """
    try:
        conversation = await chat_service.get_conversation_by_session_id(session_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversa não encontrada")
        
        # Obter estatísticas da conversa
        messages = conversation.get("messages", [])
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        ai_messages = [msg for msg in messages if msg["role"] == "assistant"]
        
        # Mock de análise de emoções baseado no conteúdo
        emotion_analysis = analyze_conversation_emotions(messages)
        
        return {
            "success": True,
            "data": {
                "session_id": conversation["session_id"],
                "username": conversation.get("user_preferences", {}).get("username", "Usuário Anônimo"),
                "created_at": conversation["created_at"].isoformat(),
                "updated_at": conversation["updated_at"].isoformat(),
                "messages": messages,
                "statistics": {
                    "total_messages": len(messages),
                    "user_messages": len(user_messages),
                    "ai_messages": len(ai_messages),
                    "duration_minutes": calculate_conversation_duration(conversation),
                    "emotion_analysis": emotion_analysis
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter detalhes da conversa: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emotions/analysis")
async def get_emotions_analysis(
    days: int = Query(7, ge=1, le=90)
):
    """
    Obter análise de emoções dos últimos dias
    """
    try:
        conversations_collection = get_collection("conversations")
        
        # Período de análise
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Obter conversas do período
        cursor = conversations_collection.find({
            "updated_at": {"$gte": start_date}
        })
        
        conversations = await cursor.to_list(length=None)
        
        # Analisar emoções (mockado por enquanto)
        emotion_distribution = {
            "alegria": 0,
            "tristeza": 0,
            "ansiedade": 0,
            "raiva": 0,
            "neutro": 0
        }
        
        total_analyzed = 0
        for conv in conversations:
            messages = conv.get("messages", [])
            for msg in messages:
                if msg["role"] == "user":
                    # Mock baseado em palavras-chave
                    emotion = detect_emotion_from_text(msg.get("content", ""))
                    emotion_distribution[emotion] += 1
                    total_analyzed += 1
        
        # Converter para percentuais
        if total_analyzed > 0:
            for emotion in emotion_distribution:
                emotion_distribution[emotion] = round((emotion_distribution[emotion] / total_analyzed) * 100, 1)
        
        return {
            "success": True,
            "data": {
                "period_days": days,
                "total_analyzed": total_analyzed,
                "distribution": emotion_distribution,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao analisar emoções: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emotions/realtime-stats")
async def get_realtime_emotion_stats():
    """
    Obter estatísticas em tempo real das emoções detectadas
    """
    try:
        user_emotions_collection = get_collection("user_emotions")
        
        # Últimas 24 horas
        last_24h = datetime.utcnow() - timedelta(hours=24)
        
        # Total de detecções
        total_detections = await user_emotions_collection.count_documents({
            "timestamp": {"$gte": last_24h}
        })
        
        # Emoções por tipo (agregação)
        pipeline = [
            {"$match": {"timestamp": {"$gte": last_24h}}},
            {"$group": {
                "_id": "$dominant_emotion",
                "count": {"$sum": 1},
                "avg_confidence": {"$avg": "$confidence"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        emotion_stats = []
        async for result in user_emotions_collection.aggregate(pipeline):
            emotion_stats.append({
                "emotion": result["_id"],
                "count": result["count"],
                "avg_confidence": round(result["avg_confidence"], 2),
                "percentage": round((result["count"] / total_detections) * 100, 2) if total_detections > 0 else 0
            })
        
        # Usuários únicos com detecção
        unique_users = len(await user_emotions_collection.distinct("username", {
            "timestamp": {"$gte": last_24h}
        }))
        
        # Taxa de detecção facial
        face_detections = await user_emotions_collection.count_documents({
            "timestamp": {"$gte": last_24h},
            "face_detected": True
        })
        
        face_detection_rate = round((face_detections / total_detections) * 100, 2) if total_detections > 0 else 0
        
        return {
            "success": True,
            "data": {
                "total_detections": total_detections,
                "unique_users": unique_users,
                "face_detection_rate": face_detection_rate,
                "emotion_distribution": emotion_stats,
                "period": "last_24h",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de emoções: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity/realtime")
async def get_realtime_activity():
    """
    Obter atividade em tempo real
    """
    try:
        conversations_collection = get_collection("conversations")
        
        # Últimas 5 atividades
        last_hour = datetime.utcnow() - timedelta(hours=1)
        cursor = conversations_collection.find({
            "updated_at": {"$gte": last_hour}
        }).sort("updated_at", -1).limit(5)
        
        recent_activities = await cursor.to_list(length=5)
        
        activities = []
        for conv in recent_activities:
            last_message = conv.get("messages", [])[-1] if conv.get("messages") else None
            if last_message:
                emotion = detect_emotion_from_text(last_message.get("content", ""))
                activities.append({
                    "time": conv["updated_at"].strftime("%H:%M"),
                    "user": conv.get("user_preferences", {}).get("username", f"Usuário #{conv['session_id'][:8]}"),
                    "emotion": emotion.capitalize(),
                    "confidence": 75 + (hash(conv["session_id"]) % 25)  # Mock confidence
                })
        
        return {
            "success": True,
            "data": {
                "activities": activities,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter atividade em tempo real: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def analyze_conversation_emotions(messages: List[Dict]) -> Dict[str, Any]:
    """
    Analisar emoções de uma conversa (mockado)
    """
    user_messages = [msg for msg in messages if msg["role"] == "user"]
    
    if not user_messages:
        return {"dominant_emotion": "neutro", "confidence": 0, "distribution": {}}
    
    emotions = []
    for msg in user_messages:
        emotion = detect_emotion_from_text(msg.get("content", ""))
        emotions.append(emotion)
    
    # Calcular emoção dominante
    emotion_counts = {}
    for emotion in emotions:
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutro"
    
    return {
        "dominant_emotion": dominant_emotion,
        "confidence": 85,  # Mock confidence
        "distribution": emotion_counts
    }

def detect_emotion_from_text(text: str) -> str:
    """
    Detectar emoção baseada em palavras-chave (mock simples)
    """
    text_lower = text.lower()
    
    # Palavras-chave para cada emoção
    keywords = {
        "alegria": ["feliz", "contente", "alegre", "otimista", "bem", "bom", "ótimo"],
        "tristeza": ["triste", "deprimido", "chateado", "mal", "péssimo", "ruim"],
        "ansiedade": ["ansioso", "preocupado", "nervoso", "estressado", "medo"],
        "raiva": ["irritado", "com raiva", "bravo", "furioso", "ódio"]
    }
    
    for emotion, words in keywords.items():
        if any(word in text_lower for word in words):
            return emotion
    
    return "neutro"

def calculate_conversation_duration(conversation: Dict) -> int:
    """
    Calcular duração da conversa em minutos
    """
    created_at = conversation["created_at"]
    updated_at = conversation["updated_at"]
    duration = updated_at - created_at
    return int(duration.total_seconds() / 60)

# ===== ENDPOINTS PARA SESSÕES TERAPÊUTICAS =====

@router.post("/therapeutic-sessions")
async def create_therapeutic_session(session: TherapeuticSessionCreate):
    """
    Criar nova sessão terapêutica
    """
    try:
        session_data = {
            "session_id": session.session_id,
            "title": session.title,
            "subtitle": session.subtitle,
            "objective": session.objective,
            "initial_prompt": session.initial_prompt,
            "is_active": session.is_active
        }
        
        result = await therapeutic_session_service.create_session(session_data)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao criar sessão terapêutica: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/therapeutic-sessions")
async def list_therapeutic_sessions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(False),
    search: Optional[str] = None
):
    """
    Listar sessões terapêuticas com paginação e filtros
    """
    try:
        result = await therapeutic_session_service.list_sessions(
            limit=limit,
            offset=offset,
            active_only=active_only,
            search=search
        )
        return result
        
    except Exception as e:
        logger.error(f"Erro ao listar sessões terapêuticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/therapeutic-sessions/{session_id}")
async def get_therapeutic_session(session_id: str):
    """
    Obter detalhes de uma sessão terapêutica
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
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/therapeutic-sessions/{session_id}")
async def update_therapeutic_session(session_id: str, session_update: TherapeuticSessionUpdate):
    """
    Atualizar uma sessão terapêutica
    """
    try:
        # Preparar dados para atualização
        update_data = {}
        
        if session_update.title is not None:
            update_data["title"] = session_update.title
        if session_update.subtitle is not None:
            update_data["subtitle"] = session_update.subtitle
        if session_update.objective is not None:
            update_data["objective"] = session_update.objective
        if session_update.initial_prompt is not None:
            update_data["initial_prompt"] = session_update.initial_prompt
        if session_update.is_active is not None:
            update_data["is_active"] = session_update.is_active
        
        success = await therapeutic_session_service.update_session(session_id, update_data)
        
        if not success:
            raise HTTPException(status_code=400, detail="Nenhuma alteração foi feita")
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "message": "Sessão terapêutica atualizada com sucesso"
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao atualizar sessão terapêutica: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/therapeutic-sessions/{session_id}")
async def delete_therapeutic_session(session_id: str):
    """
    Deletar uma sessão terapêutica
    """
    try:
        success = await therapeutic_session_service.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Erro ao deletar sessão")
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "message": "Sessão terapêutica deletada com sucesso"
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao deletar sessão terapêutica: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS PARA USUÁRIOS =====

# Instância do serviço de usuários
user_service = UserService()

# Modelos Pydantic para usuários
class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

@router.post("/users")
async def create_user(user: UserCreate):
    """
    Criar novo usuário
    """
    try:
        result = await user_service.create_user(
            username=user.username,
            email=user.email,
            preferences=user.preferences
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users")
async def list_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(True),
    search: Optional[str] = None
):
    """
    Listar usuários com paginação e busca
    """
    try:
        users = await user_service.list_users(
            limit=limit,
            offset=offset,
            active_only=active_only
        )
        
        # Filtrar por busca se especificado
        if search:
            users = [u for u in users if search.lower() in u["username"].lower()]
        
        # Contar total para paginação
        total_users = await user_service.list_users(limit=1000, active_only=active_only)
        if search:
            total_users = [u for u in total_users if search.lower() in u["username"].lower()]
        
        return {
            "success": True,
            "data": {
                "users": users,
                "pagination": {
                    "total": len(total_users),
                    "limit": limit,
                    "offset": offset,
                    "has_next": offset + limit < len(total_users)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{username}")
async def get_user(username: str):
    """
    Obter detalhes de um usuário
    """
    try:
        user = await user_service.get_user(username)
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Obter estatísticas do usuário
        stats = await user_service.get_user_stats(username)
        
        return {
            "success": True,
            "data": {
                "user": user,
                "stats": stats
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{username}")
async def update_user(username: str, user_update: UserUpdate):
    """
    Atualizar usuário
    """
    try:
        user = await user_service.get_user(username)
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Atualizar preferências se fornecidas
        if user_update.preferences is not None:
            await user_service.update_user_preferences(username, user_update.preferences)
        
        # Atualizar outros campos se necessário
        if user_update.is_active is not None and not user_update.is_active:
            await user_service.deactivate_user(username)
        
        return {
            "success": True,
            "message": "Usuário atualizado com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{username}")
async def deactivate_user(username: str):
    """
    Desativar usuário
    """
    try:
        success = await user_service.deactivate_user(username)
        
        if not success:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return {
            "success": True,
            "message": "Usuário desativado com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao desativar usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{username}/stats")
async def get_user_statistics(username: str):
    """
    Obter estatísticas detalhadas de um usuário
    """
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