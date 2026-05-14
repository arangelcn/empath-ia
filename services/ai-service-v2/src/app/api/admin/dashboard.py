"""Admin dashboard, analytics and operational status endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, Query

from ...bootstrap.dependencies import AppContainer, get_container
from ..security import require_admin_permission


router = APIRouter(
    prefix="/api/admin",
    tags=["admin-dashboard"],
    dependencies=[Depends(require_admin_permission("read"))],
)


@router.get("/stats")
async def get_dashboard_stats(container: AppContainer = Depends(get_container)) -> dict[str, object]:
    """Return top-level dashboard counters."""
    users = container.mongo.get_collection("users")
    conversations = container.mongo.get_collection("conversations")
    messages = container.mongo.get_collection("messages")
    user_emotions = container.mongo.get_collection("user_emotions")

    total_users_registered = await users.count_documents({})
    inferred_usernames = await conversations.distinct(
        "username",
        {"username": {"$exists": True, "$nin": [None, ""]}},
    )
    total_users = max(total_users_registered, len(inferred_usernames))
    total_messages = await messages.count_documents({})
    last_24h = datetime.now(UTC) - timedelta(hours=24)
    active_conversations = await conversations.count_documents({"updated_at": {"$gte": last_24h}})
    emotions_analyzed = await user_emotions.count_documents({"timestamp": {"$gte": last_24h}})

    return {
        "success": True,
        "data": {
            "total_users": total_users,
            "active_sessions": active_conversations,
            "emotions_analyzed": int(emotions_analyzed),
            "system_alerts": None,
            "total_messages": total_messages,
            "unavailable_fields": ["session_timeline", "system_alerts"],
            "last_updated": datetime.now(UTC).isoformat(),
        },
    }


@router.get("/emotions/analysis")
async def get_emotions_analysis(
    days: int = Query(7, ge=1, le=90),
    container: AppContainer = Depends(get_container),
) -> dict[str, object]:
    """Return aggregate emotion distribution for the admin dashboard."""
    user_emotions = container.mongo.get_collection("user_emotions")
    start_date = datetime.now(UTC) - timedelta(days=days)
    distribution = {"alegria": 0, "tristeza": 0, "ansiedade": 0, "raiva": 0, "neutro": 0}
    total_analyzed = await user_emotions.count_documents({"timestamp": {"$gte": start_date}})
    async for result in user_emotions.aggregate(
        [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {"$group": {"_id": "$dominant_emotion", "count": {"$sum": 1}}},
        ]
    ):
        emotion = result.get("_id") or "neutro"
        distribution[emotion] = distribution.get(emotion, 0) + result["count"]
    if total_analyzed > 0:
        for emotion in distribution:
            distribution[emotion] = round((distribution[emotion] / total_analyzed) * 100, 1)
    return {
        "success": True,
        "data": {
            "period_days": days,
            "total_analyzed": total_analyzed,
            "distribution": distribution,
            "source": "user_emotions",
            "last_updated": datetime.now(UTC).isoformat(),
        },
    }


@router.get("/activity/realtime")
async def get_realtime_activity(container: AppContainer = Depends(get_container)) -> dict[str, object]:
    """Return the latest emotion events as realtime activity."""
    user_emotions = container.mongo.get_collection("user_emotions")
    last_hour = datetime.now(UTC) - timedelta(hours=1)
    rows = await user_emotions.find({"timestamp": {"$gte": last_hour}}).sort("timestamp", -1).limit(5).to_list(length=5)
    activities = []
    for row in rows:
        timestamp = row.get("timestamp") or datetime.now(UTC)
        confidence = row.get("confidence")
        activities.append(
            {
                "time": timestamp.strftime("%H:%M"),
                "user": row.get("username", "Usuario Anonimo"),
                "emotion": str(row.get("dominant_emotion") or "neutro").capitalize(),
                "confidence": round(float(confidence) * 100, 1) if isinstance(confidence, float) and confidence <= 1 else confidence,
                "source": "user_emotions",
            }
        )
    return {"success": True, "data": {"activities": activities, "last_updated": datetime.now(UTC).isoformat()}}


@router.get("/system-status")
async def get_system_status(container: AppContainer = Depends(get_container)) -> dict[str, object]:
    """Return operational status for the unified service and downstream dependencies."""
    checked_at = datetime.now(UTC)
    services = [
        {
            "id": "ai-service-v2",
            "name": "Unified AI Service",
            "status": "online",
            "url": "internal",
            "last_check": checked_at.isoformat(),
            "details": {"version": container.settings.app_version},
        }
    ]

    try:
        await container.mongo.client.admin.command("ping")
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
            "url": container.settings.mongodb_database,
            "last_check": checked_at.isoformat(),
            "error": database_error,
        }
    )

    downstream = {
        "emotion": container.settings.emotion_service_url,
        "voice": container.settings.voice_service_url,
        "knowledge": container.settings.knowledge_service_url,
    }
    async with httpx.AsyncClient(timeout=3.0) as client:
        for service_name, service_url in downstream.items():
            started_at = datetime.now(UTC)
            try:
                response = await client.get(f"{service_url}/health")
                elapsed_ms = int((datetime.now(UTC) - started_at).total_seconds() * 1000)
                payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else None
                services.append(
                    {
                        "id": service_name,
                        "name": f"{service_name.title()} Service",
                        "status": "online" if response.status_code == 200 else "error",
                        "url": service_url,
                        "last_check": checked_at.isoformat(),
                        "response_time_ms": elapsed_ms,
                        "details": payload,
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

    conversations = container.mongo.get_collection("conversations")
    messages = container.mongo.get_collection("messages")
    users = container.mongo.get_collection("users")
    total_requests = await messages.count_documents({})
    activity_window = checked_at - timedelta(hours=24)
    active_users_from_logins = await users.count_documents({"last_login": {"$gte": activity_window}})
    active_users_from_conversations = len(
        await conversations.distinct(
            "username",
            {
                "updated_at": {"$gte": activity_window},
                "username": {"$exists": True, "$nin": [None, ""]},
            },
        )
    )
    active_users = max(active_users_from_logins, active_users_from_conversations)
    active_sessions = await conversations.count_documents({"updated_at": {"$gte": activity_window}})
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
                    "message": f"{service['name']} indisponivel",
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
async def get_analytics(
    days: int = Query(7, ge=1, le=90),
    container: AppContainer = Depends(get_container),
) -> dict[str, object]:
    """Return analytics derived from stored conversations and emotions."""
    now = datetime.now(UTC)
    start_date = now - timedelta(days=days)
    conversations = container.mongo.get_collection("conversations")
    user_emotions = container.mongo.get_collection("user_emotions")
    total_sessions = await conversations.count_documents({"updated_at": {"$gte": start_date}})
    total_emotions = await user_emotions.count_documents({"timestamp": {"$gte": start_date}})

    emotion_distribution = []
    async for result in user_emotions.aggregate(
        [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {"$group": {"_id": "$dominant_emotion", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
    ):
        count = result["count"]
        emotion_distribution.append(
            {
                "emotion": result.get("_id") or "neutro",
                "count": count,
                "percentage": round((count / total_emotions) * 100, 1) if total_emotions else 0,
            }
        )

    daily_trends = []
    async for result in user_emotions.aggregate(
        [
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
        ]
    ):
        date_key = result["_id"]["date"]
        row = next((item for item in daily_trends if item["date"] == date_key), None)
        if not row:
            row = {"date": date_key, "alegria": 0, "tristeza": 0, "ansiedade": 0, "raiva": 0, "neutro": 0}
            daily_trends.append(row)
        row[result["_id"].get("emotion") or "neutro"] = result["count"]

    hourly_engagement = []
    async for result in conversations.aggregate(
        [
            {"$match": {"updated_at": {"$gte": start_date}}},
            {"$group": {"_id": {"$hour": "$updated_at"}, "sessions": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]
    ):
        hourly_engagement.append(
            {
                "hour": f"{int(result['_id']):02d}:00",
                "sessions": result["sessions"],
                "duration": None,
            }
        )

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
