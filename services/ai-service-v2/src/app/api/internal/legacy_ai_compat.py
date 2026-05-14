"""Legacy ai-service contracts exposed directly by ai-service-v2."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...bootstrap.dependencies import AppContainer, get_container


router = APIRouter(tags=["legacy-ai-compat"])


class LegacyChatRequest(BaseModel):
    """Request shape used by the old `/chat` contract."""

    message: str
    session_id: str = "default"
    username: str = "anonymous"
    user_profile: dict[str, Any] | None = None
    conversation_history: list[dict[str, Any]] | None = None
    session_objective: dict[str, Any] | None = None
    initial_prompt: str | None = None
    previous_session_context: dict[str, Any] | None = None
    rag_policy: dict[str, Any] | None = None
    prompt_key: str | None = None
    prompt_version: int | None = None
    chat_id: str | None = None
    is_voice_mode: bool = False
    trace_id: str | None = None
    rag_language: str | None = None


class UtilCompleteRequest(BaseModel):
    """Legacy completion helper contract used by internal callers."""

    prompt: str
    system: str = "Voce e um assistente que responde de forma concisa e objetiva."
    max_tokens: int = 256


class SessionContextRequest(BaseModel):
    """Legacy session-context generation contract used by the gateway."""

    conversation_text: str
    emotions_data: list[dict[str, Any]] = Field(default_factory=list)
    session_id: str
    username: str
    manual_termination: bool = False
    additional_context: dict[str, Any] | None = None


@router.post("/chat")
async def chat(
    request: LegacyChatRequest,
    container: AppContainer = Depends(get_container),
) -> dict[str, Any]:
    """Expose the old root `/chat` contract through the new orchestration path."""
    try:
        return await container.chat_facade.generate_legacy_compat_reply(request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from exc


@router.post("/chat/stream")
async def stream_chat(
    request: LegacyChatRequest,
    container: AppContainer = Depends(get_container),
) -> StreamingResponse:
    """Expose the old root `/chat/stream` contract."""
    return StreamingResponse(
        container.stream_facade.stream_legacy_openai_compat(request.model_dump()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/util/complete")
async def util_complete(
    request: UtilCompleteRequest,
    container: AppContainer = Depends(get_container),
) -> dict[str, Any]:
    """Expose the old lightweight completion helper."""
    prompt = request.prompt.strip()
    if not prompt:
        return {"success": False, "text": ""}

    result = await container.runtime_service.complete_text(
        prompt=prompt,
        system=request.system,
    )
    text = (result.text or "").strip()
    return {"success": bool(text), "text": text}


@router.post("/openai/generate-session-context")
async def generate_session_context(
    request: SessionContextRequest,
    container: AppContainer = Depends(get_container),
) -> dict[str, Any]:
    """Expose the old session-context generation contract."""
    conversation_text = request.conversation_text.strip()
    if not conversation_text:
        raise HTTPException(status_code=400, detail="conversation_text e obrigatorio")

    prompt = _build_session_context_prompt(request)
    result = await container.runtime_service.complete_text(
        prompt=prompt,
        system=(
            "Voce analisa sessoes terapeuticas e responde apenas com JSON valido, "
            "sem markdown e sem texto adicional."
        ),
    )
    parsed = _extract_json_object(result.text or "")
    context = _normalize_session_context(parsed, conversation_text)

    await container.session_repository.save_session_context(
        request.session_id,
        request.username,
        context,
    )
    await container.conversation_repository.update_conversation_fields(
        request.session_id,
        {
            "session_context": context,
            "session_context_generated_at": datetime.now(UTC),
            "session_context_source": "ai_service_v2",
            "session_context_manual_termination": request.manual_termination,
            "session_context_generation_method": context.get("generation_method", "ai_service_v2"),
        },
    )

    return {
        "success": True,
        "context": context,
        "cached": False,
        "source": context.get("generation_method", "ai_service_v2"),
        "tokens_saved": False,
        "timestamp": datetime.now(UTC).isoformat(),
        "explanation": "Contexto gerado e persistido pelo ai-service-v2.",
    }


def _build_session_context_prompt(request: SessionContextRequest) -> str:
    prompt = (
        (request.additional_context or {}).get("analysis_prompt")
        or ""
    ).strip()
    if prompt:
        return prompt

    termination_context = (
        "manualmente pelo usuario"
        if request.manual_termination
        else "automaticamente por despedida detectada"
    )
    return (
        "Analise a conversa terapeutica abaixo e responda apenas com JSON valido.\n\n"
        f"SESSAO ID: {request.session_id}\n"
        f"USUARIO: {request.username}\n"
        f"TERMINO: {termination_context}\n\n"
        "Formato obrigatorio:\n"
        "{\n"
        '  "summary": "Resumo geral da sessao em 2-3 frases",\n'
        '  "main_themes": ["tema1", "tema2"],\n'
        '  "emotional_state": {"initial": "...", "final": "...", "progression": "..."},\n'
        '  "key_insights": ["insight1", "insight2"],\n'
        '  "important_moments": [{"moment": "...", "significance": "..."}],\n'
        '  "user_progress": {"strengths_shown": ["..."], "challenges_identified": ["..."], "growth_areas": ["..."]},\n'
        '  "therapeutic_notes": {"techniques_used": ["..."], "user_response": "...", "engagement_level": "Alto/Medio/Baixo"},\n'
        '  "future_sessions": {"suggested_topics": ["..."], "areas_to_explore": ["..."], "therapeutic_goals": ["..."]}\n'
        "}\n\n"
        f"CONVERSA:\n{request.conversation_text}"
    )


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    cleaned = (raw_text or "").strip()
    if not cleaned:
        return {}

    try:
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end <= start:
        return {}

    try:
        value = json.loads(cleaned[start : end + 1])
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def _normalize_session_context(parsed: dict[str, Any], conversation_text: str) -> dict[str, Any]:
    themes = _normalize_string_list(parsed.get("main_themes")) or _extract_keywords(conversation_text)
    summary = _coerce_text(parsed.get("summary")) or _fallback_summary(conversation_text)
    key_insights = _normalize_string_list(parsed.get("key_insights")) or [
        f"Os temas mais presentes foram: {', '.join(themes[:3])}.",
        "A conversa trouxe material suficiente para continuidade terapeutica.",
    ]

    context = {
        "summary": summary,
        "main_themes": themes,
        "emotional_state": _normalize_mapping(
            parsed.get("emotional_state"),
            {
                "initial": "Nao identificado com confianca.",
                "final": "Nao identificado com confianca.",
                "progression": "Oscilacao emocional nao inferida com seguranca.",
            },
        ),
        "key_insights": key_insights,
        "important_moments": _normalize_moment_list(parsed.get("important_moments")),
        "user_progress": _normalize_mapping(
            parsed.get("user_progress"),
            {
                "strengths_shown": [],
                "challenges_identified": themes[:2],
                "growth_areas": themes[:2],
            },
        ),
        "therapeutic_notes": _normalize_mapping(
            parsed.get("therapeutic_notes"),
            {
                "techniques_used": ["escuta_reflexiva"],
                "user_response": "Engajamento identificado na troca verbal.",
                "engagement_level": "Medio",
            },
        ),
        "future_sessions": _normalize_mapping(
            parsed.get("future_sessions"),
            {
                "suggested_topics": themes[:3],
                "areas_to_explore": themes[:3],
                "therapeutic_goals": key_insights[:2],
            },
        ),
        "generation_method": "ai_service_v2_runtime",
    }

    if not context["important_moments"]:
        context["important_moments"] = [
            {
                "moment": "Trecho central da conversa identificado no resumo.",
                "significance": "Ajuda a recuperar rapidamente o foco tematico da sessao.",
            }
        ]

    return context


def _normalize_moment_list(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    moments: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        moment = _coerce_text(item.get("moment"))
        significance = _coerce_text(item.get("significance"))
        if moment and significance:
            moments.append({"moment": moment, "significance": significance})
    return moments


def _normalize_mapping(value: Any, default: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return default

    normalized = dict(default)
    for key, fallback in default.items():
        candidate = value.get(key)
        if isinstance(fallback, list):
            normalized[key] = _normalize_string_list(candidate) or fallback
        else:
            normalized[key] = _coerce_text(candidate) or fallback
    return normalized


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items = [_coerce_text(item) for item in value]
    return [item for item in items if item]


def _coerce_text(value: Any) -> str:
    if isinstance(value, str):
        return " ".join(value.split()).strip()
    return str(value).strip() if value is not None else ""


def _fallback_summary(conversation_text: str) -> str:
    lines = [
        " ".join(line.split()).strip()
        for line in conversation_text.splitlines()
        if line.strip()
    ]
    if not lines:
        return "Sessao sem conteudo suficiente para resumo."
    return " ".join(lines[:3])[:500].strip()


def _extract_keywords(conversation_text: str) -> list[str]:
    stopwords = {
        "sobre",
        "porque",
        "para",
        "como",
        "muito",
        "estava",
        "estou",
        "tenho",
        "com",
        "uma",
        "umas",
        "uns",
        "que",
        "isso",
        "essa",
        "esse",
        "pela",
        "pelos",
        "pelas",
        "entre",
        "quando",
        "onde",
        "mais",
        "menos",
        "aqui",
        "hoje",
        "user",
        "usuario",
        "terapeuta",
    }
    tokens = [
        token.strip(".,!?;:()[]{}\"'").lower()
        for token in conversation_text.split()
    ]
    candidates = [
        token
        for token in tokens
        if len(token) >= 5 and token.isalpha() and token not in stopwords
    ]
    ranked = [token for token, _ in Counter(candidates).most_common(5)]
    if ranked:
        return ranked
    return ["autoconhecimento", "relacionamentos", "bem-estar"]
