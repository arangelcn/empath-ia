"""Chat title, context, finalization, and initial-message routes."""

import hashlib
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..domain.session_subjects import join_subjects, select_previous_session_subjects
from ..domain.user_display import first_name_from_user
from ..models.database import get_collection
from ..services.chat_service import ChatService
from ..services.user_service import UserService
from ..services.user_therapeutic_session_service import UserTherapeuticSessionService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat Context"])
chat_service = ChatService()
user_service = UserService()
user_therapeutic_session_service = UserTherapeuticSessionService()


class GenerateTitleRequest(BaseModel):
    mode: str = "initial"


async def _get_user_display_name(username: str) -> str:
    """Nome humano para UI/prompts; username continua sendo apenas identificador técnico."""
    try:
        user = await user_service.get_user(username)
        return first_name_from_user(user, username) or ""
    except Exception as exc:
        logger.warning("Não foi possível obter display_name para %s: %s", username, exc)
        return first_name_from_user(None, username) or ""


async def _find_previous_conversation_doc(previous_session_id: str) -> dict | None:
    conversations = get_collection("conversations")
    return await conversations.find_one(
        {
            "$or": [
                {"session_id": previous_session_id},
                {"legacy_session_id": previous_session_id},
            ]
        }
    )


async def _find_previous_user_session_doc(username: str, previous_original_session_id: str) -> dict | None:
    user_sessions = get_collection("user_therapeutic_sessions")
    return await user_sessions.find_one({"username": username, "session_id": previous_original_session_id})


@router.post("/generate-title/{chat_id}")
async def generate_chat_title(chat_id: str, request: GenerateTitleRequest):
    """Generate a contextual AI title and subtitle for a chat session."""
    return await chat_service.generate_chat_title(chat_id, request.mode)


@router.post("/finalize/{session_id}")
async def finalize_session(session_id: str):
    """
    Finalizar sessão manualmente, gerar contexto e atualizar título com base na conversa.
    """
    try:
        identity = await chat_service.resolve_conversation_ref(session_id)
        chat_id = identity.get("chat_id") or session_id
        legacy_session_id = identity.get("legacy_session_id") or session_id
        username = identity.get("username", "")
        therapeutic_session_id = identity.get("therapeutic_session_id", "")

        result = await chat_service.finalize_session_context(legacy_session_id, manual_termination=True)

        if "_session-" in legacy_session_id:
            session_separator_index = legacy_session_id.rfind("_session-")
            if session_separator_index != -1:
                username = username or legacy_session_id[:session_separator_index]
                original_session_id = therapeutic_session_id or legacy_session_id[session_separator_index + 1:]

                logger.info("🏁 Finalizando sessão: username=%s, session_id=%s", username, original_session_id)

                try:
                    completion_result = await user_therapeutic_session_service.complete_session(
                        username=username,
                        session_id=original_session_id,
                        progress=100,
                        status="completed",
                    )
                    result["session_completed"] = bool(completion_result)
                    if completion_result:
                        logger.info("✅ Sessão %s marcada como completed para %s", original_session_id, username)
                        result["completion_message"] = f"Sessão {original_session_id} finalizada com sucesso!"
                    else:
                        logger.warning("⚠️ Não foi possível marcar sessão %s como completed", original_session_id)
                except Exception as exc:
                    logger.error("❌ Erro ao marcar sessão como completed: %s", exc)
                    result["session_completed"] = False

                try:
                    title_result = await chat_service.generate_chat_title(chat_id, mode="final")
                    if title_result.get("success"):
                        result["generated_title"] = title_result.get("title")
                        result["generated_subtitle"] = title_result.get("subtitle")
                        logger.info("🏷️ Título final gerado: %r", title_result.get("title"))
                except Exception as exc:
                    logger.warning("⚠️ Título não gerado na finalização: %s", exc)
            else:
                logger.warning("⚠️ Formato de session_id inválido: %s", legacy_session_id)
        else:
            logger.warning("⚠️ Session_id sem padrão '_session-': %s", legacy_session_id)

        return {"success": result.get("success", False), "data": result}

    except Exception as exc:
        logger.error("❌ Erro ao finalizar sessão %s: %s", session_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/context/{session_id}")
async def get_session_context(session_id: str):
    """Obter contexto salvo de uma sessão"""
    try:
        context = await chat_service.get_session_context(session_id)
        if context:
            return {
                "success": True,
                "data": {
                    "session_id": session_id,
                    "context": context,
                },
            }
        raise HTTPException(status_code=404, detail="Contexto não encontrado para esta sessão")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("❌ Erro ao obter contexto da sessão %s: %s", session_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/conversations-with-context")
async def list_conversations_with_context(limit: int = 10):
    """Listar conversas que possuem contexto gerado"""
    try:
        conversations = get_collection("conversations")
        cursor = conversations.find(
            {"session_context": {"$exists": True}},
            sort=[("context_generated_at", -1)],
            limit=limit,
        )

        result = []
        async for conv in cursor:
            context = conv.get("session_context", {})
            result.append(
                {
                    "session_id": conv["session_id"],
                    "username": conv.get("username"),
                    "created_at": conv["created_at"].isoformat(),
                    "context_generated_at": conv.get("context_generated_at", conv["updated_at"]).isoformat(),
                    "manual_termination": conv.get("manual_termination", False),
                    "summary": context.get("summary", ""),
                    "main_themes": context.get("main_themes", []),
                    "emotional_state": context.get("emotional_state", {}),
                    "message_count": conv.get("message_count", 0),
                }
            )

        return {
            "success": True,
            "data": {
                "conversations": result,
                "total": len(result),
            },
        }

    except Exception as exc:
        logger.error("❌ Erro ao listar conversas com contexto: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/initial-message/{session_id}")
async def get_initial_message(session_id: str):
    """Obter mensagem inicial para uma sessão sem esperar input do usuário."""
    try:
        logger.info("🎯 Gerando mensagem inicial para sessão: %s", session_id)

        identity = await chat_service.resolve_conversation_ref(session_id)
        legacy_session_id = identity.get("legacy_session_id") or session_id
        username = identity.get("username")
        original_session_id = identity.get("therapeutic_session_id")
        if not username or not original_session_id:
            username, original_session_id = chat_service._split_composite_session_id(legacy_session_id)

        if not username:
            return {"success": False, "error": "Username não encontrado no session_id"}

        user_label = await _get_user_display_name(username)
        history = await chat_service.get_conversation_history(legacy_session_id)
        if history.get("history") and len(history["history"]) > 0:
            return {
                "success": False,
                "error": "Sessão já possui mensagens, não precisa de mensagem inicial",
            }

        if original_session_id == "session-1":
            greeting = f"Olá, {user_label}!" if user_label else "Olá!"
            initial_message = f"""{greeting}

Eu sou seu assistente terapêutico. É um prazer te conhecer! Para personalizar nossa conversa, vou fazer algumas perguntas sobre você.

Primeiro, me conta: qual é a sua idade?"""
        else:
            initial_message = await _build_followup_initial_message(
                username=username,
                user_label=user_label,
                original_session_id=original_session_id or "session-1",
            )

        await chat_service.start_or_get_conversation(legacy_session_id)
        message_id = await chat_service._save_message(legacy_session_id, "ai", initial_message)
        logger.info("🔍 DEBUG: Mensagem inicial salva com ID: %s", message_id)

        debug_history = await chat_service.get_conversation_history(legacy_session_id)
        logger.info("🔍 DEBUG: Histórico após salvar - %s mensagens", len(debug_history.get("history", [])))
        if debug_history.get("history"):
            for i, msg in enumerate(debug_history["history"]):
                logger.info("🔍 DEBUG: Mensagem %s: type=%s, content=%s...", i + 1, msg["type"], msg["content"][:50])

        audio_url = await _try_generate_initial_audio(username, initial_message)

        return {
            "success": True,
            "data": {
                "message": {
                    "id": message_id,
                    "type": "ai",
                    "content": initial_message,
                    "audioUrl": audio_url,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                "chat_id": identity.get("chat_id"),
                "session_id": legacy_session_id,
                "therapeutic_session_id": original_session_id,
                "is_initial_message": True,
            },
        }

    except Exception as exc:
        logger.error("❌ Erro ao gerar mensagem inicial: %s", exc)
        return {"success": False, "error": f"Erro ao gerar mensagem inicial: {str(exc)}"}


async def _build_followup_initial_message(username: str, user_label: str, original_session_id: str) -> str:
    try:
        session_number_str = original_session_id.split("-")[1] if "-" in original_session_id else "1"
        current_session_number = int(session_number_str)
        previous_session_number = current_session_number - 1
        previous_session_id = f"{username}_session-{previous_session_number}"
        previous_original_session_id = f"session-{previous_session_number}"

        logger.info(
            "🔍 DEBUG SESSÃO 2+: current=%s, previous=%s, username=%s",
            original_session_id,
            previous_session_id,
            username,
        )

        users_collection = get_collection("users")
        user_profile = await users_collection.find_one({"username": username})
        previous_context = await chat_service.get_session_context(previous_session_id)
        previous_conversation = await _find_previous_conversation_doc(previous_session_id)
        previous_user_session = await _find_previous_user_session_doc(username, previous_original_session_id)

        logger.info(
            "🔍 DEBUG: previous_context encontrado? %s, user_profile encontrado? %s",
            previous_context is not None,
            user_profile is not None,
        )

        previous_subjects = select_previous_session_subjects(
            previous_context=previous_context,
            previous_session_doc=previous_user_session,
            previous_conversation_doc=previous_conversation,
        )

        if previous_subjects:
            subjects_text = join_subjects(previous_subjects)
            return f"""Olá, {user_label}! É bom te ver novamente.

Como você está se sentindo desde nossa última conversa?

Na nossa sessão anterior, apareceram temas como {subjects_text}. Gostaria de continuar por aí ou há algo mais presente para você hoje?"""

        if previous_context:
            main_themes = previous_context.get("main_themes", [])
            emotional_state = previous_context.get("emotional_state", {})
            logger.info("🔍 DEBUG CONTEXTO ANTERIOR - Temas: %s, Estado emocional: %s", main_themes, emotional_state)

            return f"""Olá, {user_label}! É bom te ver novamente.

Como você está se sentindo desde nossa última conversa?

O que ficou mais presente para você desde então, ou o que te trouxe aqui hoje?"""

        if user_profile and user_profile.get("user_profile"):
            return _message_from_user_profile(user_label, user_profile["user_profile"], current_session_number)

        return _fallback_initial_message(username, user_label, current_session_number)

    except Exception as exc:
        logger.error("❌ Erro ao processar sessão 2+ para %s: %s", username, exc)
        return f"""Olá, {user_label}! É bom te ver novamente.

Como você está se sentindo hoje? O que gostaria de conversar comigo?"""


def _message_from_user_profile(user_label: str, profile: dict, current_session_number: int) -> str:
    therapeutic_info = profile.get("therapeutic_info", {})
    objectives = therapeutic_info.get("objetivos_identificados", [])
    motivation = therapeutic_info.get("motivacao_terapia", {})
    logger.info("🔍 DEBUG PERFIL - Objetivos: %s, Motivação: %s", objectives, motivation)

    if current_session_number == 2:
        if objectives:
            objectives_text = ", ".join(objectives[:2])
            return f"""Olá, {user_label}! É bom te ver novamente.

Agora que nos conhecemos melhor, esta é nossa segunda sessão terapêutica.

Lembro que você mencionou interesse em trabalhar com {objectives_text}. Como você está se sentindo desde nossa conversa anterior? Gostaria de explorar esses temas ou há algo específico que te trouxe aqui hoje?"""

        return f"""Olá, {user_label}! É bom te ver novamente.

Agora que nos conhecemos melhor, esta é nossa segunda sessão terapêutica.

Como você está se sentindo desde nossa conversa anterior? Há algo específico que gostaria de explorar hoje, ou prefere que conversemos sobre como você tem se sentido recentemente?"""

    return f"""Olá, {user_label}! É bom te ver novamente.

Esta é nossa sessão {current_session_number}. Como você está se sentindo desde nossa última conversa?

O que te trouxe aqui hoje? Há algo específico que gostaria de conversar comigo?"""


def _fallback_initial_message(username: str, user_label: str, current_session_number: int) -> str:
    username_hash = int(hashlib.md5(username.encode()).hexdigest(), 16) % 3

    session_2_variations = [
        f"""Olá, {user_label}! É bom te ver novamente.

Agora que nos conhecemos melhor, esta é nossa segunda sessão terapêutica.

Como você está se sentindo desde nossa conversa anterior? Há algo específico que gostaria de explorar hoje?""",
        f"""Oi, {user_label}! Que bom que você voltou.

Esta é nossa segunda sessão juntos. Como você tem estado desde que conversamos?

O que você gostaria de compartilhar comigo hoje? Há algo que tem estado em sua mente?""",
        f"""Olá, {user_label}! É um prazer te ver novamente.

Agora que já nos conhecemos um pouco, como você está se sentindo hoje?

Há alguma reflexão da nossa primeira conversa que gostaria de continuar explorando, ou algo novo que te trouxe aqui?""",
    ]

    other_session_variations = [
        f"""Olá, {user_label}! É bom te ver novamente.

Esta é nossa sessão {current_session_number}. Como você está se sentindo hoje?

O que te trouxe aqui? Há algo específico que gostaria de conversar comigo?""",
        f"""Oi, {user_label}! Que bom que você voltou.

Como você tem estado desde nossa última conversa?

O que você gostaria de compartilhar comigo hoje nesta sessão {current_session_number}?""",
        f"""Olá, {user_label}! É um prazer te ver novamente.

Como você está se sentindo hoje? Há algo em particular que gostaria de explorar em nossa sessão {current_session_number}?""",
    ]

    logger.warning(
        "⚠️ Contexto e perfil não encontrados para %s. Usando fallback variado para sessão %s (variação %s)",
        username,
        current_session_number,
        username_hash,
    )

    if current_session_number == 2:
        return session_2_variations[username_hash]
    return other_session_variations[username_hash]


async def _try_generate_initial_audio(username: str, initial_message: str) -> str | None:
    try:
        users_collection = get_collection("users")
        user = await users_collection.find_one({"username": username})

        if user and user.get("preferences", {}).get("voice_enabled", True):
            selected_voice = user.get("preferences", {}).get("selected_voice", "pt-BR-Neural2-B")
            return await chat_service._generate_audio(initial_message, selected_voice)
    except Exception as exc:
        logger.warning("⚠️ Erro ao gerar áudio para mensagem inicial: %s", exc)
    return None
