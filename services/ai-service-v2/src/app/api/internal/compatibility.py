"""Internal compatibility routes."""

from fastapi import APIRouter


router = APIRouter(prefix="/internal/compatibility", tags=["internal-compatibility"])


@router.get("/routes")
async def compatibility_routes() -> dict[str, object]:
    """List the initial compatibility targets for the migration."""
    return {
        "service": "ai-service-v2",
        "phase": "scaffold",
        "targets": [
            {"legacy": "/api/chat", "owner": "app.api.public.chat"},
            {"legacy": "/api/chat/*", "owner": "app.api.public.chat_context"},
            {"legacy": "/api/user/*", "owner": "app.api.public.users"},
            {"legacy": "/api/voice/*", "owner": "app.api.public.voice"},
            {"legacy": "/api/prompts/*", "owner": "app.api.public.prompts"},
            {"legacy": "/api/admin/*", "owner": "app.api.admin.*"},
            {"legacy": "/openai/*", "owner": "app.api.internal.llm"},
        ],
    }
