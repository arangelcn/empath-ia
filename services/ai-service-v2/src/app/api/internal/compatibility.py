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
            {"legacy": "/chat", "owner": "app.api.internal.legacy_ai_compat", "status": "migrated"},
            {"legacy": "/chat/stream", "owner": "app.api.internal.legacy_ai_compat", "status": "migrated"},
            {"legacy": "/util/complete", "owner": "app.api.internal.legacy_ai_compat", "status": "migrated"},
            {
                "legacy": "/openai/generate-session-context",
                "owner": "app.api.internal.legacy_ai_compat",
                "status": "migrated",
            },
            {"legacy": "/api/chat/send", "owner": "app.application.chat.chat_facade", "status": "migrated"},
            {"legacy": "/api/chat/send-stream", "owner": "app.application.chat.stream_facade", "status": "migrated"},
            {"legacy": "/openai/chat", "owner": "app.application.chat.chat_facade", "status": "migrated"},
            {"legacy": "/openai/chat/stream", "owner": "app.application.chat.stream_facade", "status": "migrated"},
            {"legacy": "/api/chat/*", "owner": "app.api.public.chat", "status": "active"},
            {"legacy": "/api/auth/*", "owner": "app.api.public.auth", "status": "migrated"},
            {"legacy": "/api/user/*", "owner": "app.api.public.users + app.api.public.sessions", "status": "migrated"},
            {"legacy": "/api/sessions/*", "owner": "app.api.public.sessions", "status": "migrated"},
            {"legacy": "/api/prompts/*", "owner": "app.api.public.prompts", "status": "migrated"},
            {"legacy": "/api/emotion* and /api/emotions/*", "owner": "app.api.public.emotions", "status": "migrated"},
            {"legacy": "/api/voice/*", "owner": "app.api.public.voice", "status": "direct-service"},
            {"legacy": "/api/admin/*", "owner": "app.api.admin.*", "status": "migrated"},
            {"legacy": "/api/admin/knowledge/*", "owner": "app.api.admin.knowledge", "status": "direct-service"},
        ],
    }
