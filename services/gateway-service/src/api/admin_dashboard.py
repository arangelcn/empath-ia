"""
Admin dashboard, analytics and operational status endpoints.
"""

import logging
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from ..config import SERVICE_URLS, settings
from ..models.database import get_collection, get_database
from .auth import require_admin_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin_permission("read"))],
)


@router.get("/stats")
async def get_dashboard_stats():
    """
    Obter estatísticas gerais para o dashboard
    """
    try:
        users_collection = get_collection("users")
        conversations_collection = get_collection("conversations")
        messages_collection = get_collection("messages")

        # Estatísticas básicas
        total_users = await users_collection.count_documents({})
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
                "total_users": total_users,
                "active_sessions": active_conversations,
                "emotions_analyzed": int(emotions_analyzed),
                "system_alerts": None,
                "total_messages": total_messages,
                "unavailable_fields": ["session_timeline", "system_alerts"],
                "last_updated": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emotions/analysis")
async def get_emotions_analysis(
    days: int = Query(7, ge=1, le=90)
):
    """
    Obter análise de emoções dos últimos dias
    """
    try:
        user_emotions_collection = get_collection("user_emotions")

        # Período de análise
        start_date = datetime.utcnow() - timedelta(days=days)

        emotion_distribution = {
            "alegria": 0,
            "tristeza": 0,
            "ansiedade": 0,
            "raiva": 0,
            "neutro": 0
        }

        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {"$group": {"_id": "$dominant_emotion", "count": {"$sum": 1}}},
        ]

        total_analyzed = await user_emotions_collection.count_documents({
            "timestamp": {"$gte": start_date}
        })

        async for result in user_emotions_collection.aggregate(pipeline):
            emotion = result.get("_id") or "neutro"
            emotion_distribution[emotion] = emotion_distribution.get(emotion, 0) + result["count"]

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
                "source": "user_emotions",
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
        user_emotions_collection = get_collection("user_emotions")

        last_hour = datetime.utcnow() - timedelta(hours=1)
        cursor = user_emotions_collection.find({
            "timestamp": {"$gte": last_hour}
        }).sort("timestamp", -1).limit(5)

        recent_emotions = await cursor.to_list(length=5)

        activities = []
        for item in recent_emotions:
            timestamp = item.get("timestamp") or datetime.utcnow()
            emotion = item.get("dominant_emotion") or "neutro"
            confidence = item.get("confidence")
            activities.append({
                "time": timestamp.strftime("%H:%M"),
                "user": item.get("username", "Usuário Anônimo"),
                "emotion": emotion.capitalize(),
                "confidence": round(float(confidence) * 100, 1) if isinstance(confidence, float) and confidence <= 1 else confidence,
                "source": "user_emotions"
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


@router.get("/system-status")
async def get_system_status():
    """
    Obter status operacional real a partir do gateway, MongoDB e health checks dos serviços.
    Métricas de CPU/memória/uptime ainda não possuem coletor backend e são marcadas como indisponíveis.
    """
    checked_at = datetime.utcnow()
    services = [
        {
            "id": "gateway",
            "name": "Gateway Service",
            "status": "online",
            "url": "internal",
            "last_check": checked_at.isoformat(),
            "details": {"version": "2.0.0"},
        }
    ]

    try:
        await get_database().command("ping")
        database_status = "online"
        database_error = None
    except Exception as exc:
        database_status = "error"
        database_error = str(exc)

    services.append(
        {
            "id": "mongodb",
            "name": "MongoDB",
            "status": database_status,
            "url": settings.mongodb_database,
            "last_check": checked_at.isoformat(),
            "error": database_error,
        }
    )

    async with httpx.AsyncClient(timeout=3.0) as client:
        for service_name, service_url in SERVICE_URLS.items():
            started_at = datetime.utcnow()
            try:
                response = await client.get(f"{service_url}/health")
                elapsed_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
                services.append(
                    {
                        "id": service_name,
                        "name": f"{service_name.title()} Service",
                        "status": "online" if response.status_code == 200 else "error",
                        "url": service_url,
                        "last_check": checked_at.isoformat(),
                        "response_time_ms": elapsed_ms,
                        "details": response.json() if response.headers.get("content-type", "").startswith("application/json") else None,
                    }
                )
            except Exception as exc:
                services.append(
                    {
                        "id": service_name,
                        "name": f"{service_name.title()} Service",
                        "status": "unreachable",
                        "url": service_url,
                        "last_check": checked_at.isoformat(),
                        "error": str(exc),
                    }
                )

    conversations_collection = get_collection("conversations")
    messages_collection = get_collection("messages")
    users_collection = get_collection("users")
    total_requests = await messages_collection.count_documents({})
    active_users = await users_collection.count_documents({"last_login": {"$gte": checked_at - timedelta(hours=24)}})
    active_sessions = await conversations_collection.count_documents({"updated_at": {"$gte": checked_at - timedelta(hours=24)}})
    error_count = len([service for service in services if service["status"] in {"error", "unreachable"}])

    return {
        "success": True,
        "data": {
            "services": services,
            "metrics": {
                "total_requests": total_requests,
                "active_users": active_users,
                "active_sessions": active_sessions,
                "online_services": len([service for service in services if service["status"] == "online"]),
                "total_services": len(services),
                "error_count": error_count,
                "avg_response_time_ms": None,
                "error_rate": None,
                "disk_usage": None,
                "network_latency_ms": None,
            },
            "alerts": [
                {
                    "level": "error",
                    "message": f"{service['name']} indisponível",
                    "detail": service.get("error") or service.get("status"),
                    "service": service["id"],
                }
                for service in services
                if service["status"] in {"error", "unreachable"}
            ],
            "unavailable_fields": [
                "service_uptime",
                "cpu_usage",
                "memory_usage",
                "avg_response_time_ms",
                "error_rate",
                "disk_usage",
                "network_latency_ms",
                "service_actions",
            ],
            "last_updated": checked_at.isoformat(),
        },
    }


@router.get("/analytics")
async def get_analytics(days: int = Query(7, ge=1, le=90)):
    """
    Métricas analíticas derivadas das coleções existentes.
    Dados sem fonte atual, como demografia e satisfação, retornam como indisponíveis.
    """
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)

    conversations_collection = get_collection("conversations")
    user_emotions_collection = get_collection("user_emotions")

    total_sessions = await conversations_collection.count_documents({"updated_at": {"$gte": start_date}})
    total_emotions = await user_emotions_collection.count_documents({"timestamp": {"$gte": start_date}})

    emotion_distribution = []
    async for result in user_emotions_collection.aggregate([
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {"_id": "$dominant_emotion", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]):
        count = result["count"]
        emotion_distribution.append({
            "emotion": result.get("_id") or "neutro",
            "count": count,
            "percentage": round((count / total_emotions) * 100, 1) if total_emotions else 0,
        })

    daily_trends = []
    async for result in user_emotions_collection.aggregate([
        {"$match": {"timestamp": {"$gte": start_date}}},
        {
            "$group": {
                "_id": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "emotion": "$dominant_emotion",
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.date": 1}},
    ]):
        date_key = result["_id"]["date"]
        row = next((item for item in daily_trends if item["date"] == date_key), None)
        if not row:
            row = {"date": date_key, "alegria": 0, "tristeza": 0, "ansiedade": 0, "raiva": 0, "neutro": 0}
            daily_trends.append(row)
        row[result["_id"].get("emotion") or "neutro"] = result["count"]

    hourly_engagement = []
    async for result in conversations_collection.aggregate([
        {"$match": {"updated_at": {"$gte": start_date}}},
        {"$group": {"_id": {"$hour": "$updated_at"}, "sessions": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]):
        hourly_engagement.append({
            "hour": f"{int(result['_id']):02d}:00",
            "sessions": result["sessions"],
            "duration": None,
        })

    return {
        "success": True,
        "data": {
            "period_days": days,
            "metrics": {
                "total_sessions": total_sessions,
                "avg_session_duration_minutes": None,
                "emotions_detected": total_emotions,
                "satisfaction_rate": None,
            },
            "emotion_trends": daily_trends,
            "engagement_by_hour": hourly_engagement,
            "top_emotions": emotion_distribution,
            "demographics": [],
            "insights": [],
            "unavailable_fields": [
                "avg_session_duration_minutes",
                "satisfaction_rate",
                "demographics",
                "automated_insights",
            ],
            "last_updated": now.isoformat(),
        },
    }
