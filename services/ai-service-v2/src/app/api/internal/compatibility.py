"""Internal compatibility routes."""

from fastapi import APIRouter


router = APIRouter(prefix="/internal/compatibility", tags=["internal-compatibility"])


@router.get("/routes")
async def compatibility_routes() -> dict[str, object]:
    """List the current compatibility targets for the migration."""
    return {
        "service": "ai-service-v2",
        "phase": "compatibility-hardening",
        "targets": [
            {"legacy": "/api/chat/send", "owner": "app.application.chat.chat_facade", "status": "migrated"},
            {"legacy": "/api/chat/send-stream", "owner": "app.application.chat.stream_facade", "status": "migrated"},
            {"legacy": "/openai/chat", "owner": "app.application.chat.chat_facade", "status": "migrated"},
            {"legacy": "/openai/chat/stream", "owner": "app.application.chat.stream_facade", "status": "migrated"},
            {"legacy": "/api/chat/*", "owner": "app.api.public.chat", "status": "active"},
            {"legacy": "/api/admin/*", "owner": "app.api.admin.*", "status": "partial-scaffold"},
        ],
    }
