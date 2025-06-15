"""
API endpoints para o painel administrativo
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any
from ..models.database import get_async_collection
from ..services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Instância do serviço de chat
chat_service = ChatService()

@router.get("/stats")
async def get_dashboard_stats():
    """
    Obter estatísticas gerais para o dashboard
    """
    try:
        conversations_collection = await get_async_collection("conversations")
        messages_collection = await get_async_collection("messages")
        
        # Estatísticas básicas
        total_conversations = await conversations_collection.count_documents({})
        total_messages = await messages_collection.count_documents({})
        
        # Conversas ativas (últimas 24h)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        active_conversations = await conversations_collection.count_documents({
            "updated_at": {"$gte": last_24h}
        })
        
        # Dados mockados para emoções (até implementar análise real)
        emotions_analyzed = total_messages * 0.8  # Assumindo 80% das mensagens analisadas
        
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
        conversations_collection = await get_async_collection("conversations")
        
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
        conversations_collection = await get_async_collection("conversations")
        
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

@router.get("/activity/realtime")
async def get_realtime_activity():
    """
    Obter atividade em tempo real
    """
    try:
        conversations_collection = await get_async_collection("conversations")
        
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