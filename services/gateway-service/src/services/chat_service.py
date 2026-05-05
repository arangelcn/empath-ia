"""
Serviço de chat - orquestra conversas e mensagens
"""

import logging
import uuid
import json
import time
from typing import AsyncGenerator, Dict, List, Optional, Any
from datetime import datetime
import httpx
from ..config import settings
from ..domain.conversation_identity import build_legacy_session_id, split_composite_session_id
from ..models.database import get_collection
from ..repositories.conversation_repository import ConversationRepository
from .chat_title_service import ChatTitleService
from .next_session_service import NextSessionService
from .registration_service import RegistrationService
from .session_context_service import SessionContextService
from .streaming_utils import SentenceChunker, now_ms
from .user_profile_service import UserProfileService
from .voice_synthesis_service import VoiceSynthesisService

logger = logging.getLogger(__name__)

class ChatService:
    """Serviço de chat com persistência MongoDB"""
    
    def __init__(self):
        self.ai_service_url = settings.service_urls.ai
        self.base_voice_url = settings.service_urls.voice
        self.voice_synthesis_service = VoiceSynthesisService(self.base_voice_url)
        self.user_profile_service = UserProfileService()
        self.next_session_service = NextSessionService(
            extract_username_from_session_id=self._extract_username_from_session_id,
            user_profile_service=self.user_profile_service,
        )
        self.conversation_repo = ConversationRepository(
            resolve_ref=self.resolve_conversation_ref,
            extract_username=self._extract_username_from_session_id,
        )
        self.session_context_service = SessionContextService(
            ai_service_url=self.ai_service_url,
            conversation_repo=self.conversation_repo,
            resolve_ref=self.resolve_conversation_ref,
            extract_username=self._extract_username_from_session_id,
            split_session_id=self._split_composite_session_id,
            next_session_service=self.next_session_service,
        )
        self.registration_service = RegistrationService(
            save_message=self._save_message,
            finalize_session_context=self.session_context_service.finalize_session_context,
            generate_audio=self._generate_audio,
            extract_username_from_session_id=self._extract_username_from_session_id,
            user_profile_service=self.user_profile_service,
        )
        self.chat_title_service = ChatTitleService(
            self.ai_service_url,
            get_collection,
            httpx.AsyncClient,
        )

    def _split_composite_session_id(self, session_id: str) -> tuple[Optional[str], str]:
        return split_composite_session_id(session_id)

    def _build_legacy_session_id(self, username: Optional[str], therapeutic_session_id: Optional[str]) -> str:
        return build_legacy_session_id(username, therapeutic_session_id)

    async def _ensure_conversation_identity(
        self,
        conversation: Dict[str, Any],
        fallback_ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Normalizar uma conversa para o modelo novo.

        chat_id é a PK pública/opaca. session_id antigo permanece como chave legada para
        compatibilidade com dados existentes e serviços internos que ainda esperam esse formato.
        """
        conversations = get_collection("conversations")
        updates: Dict[str, Any] = {}

        chat_id = conversation.get("chat_id")
        if not chat_id:
            chat_id = f"chat_{uuid.uuid4().hex}"
            updates["chat_id"] = chat_id

        legacy_session_id = conversation.get("legacy_session_id") or conversation.get("session_id") or fallback_ref
        username = conversation.get("username") or conversation.get("user_preferences", {}).get("username")
        therapeutic_session_id = conversation.get("therapeutic_session_id")

        if legacy_session_id and not therapeutic_session_id:
            parsed_username, parsed_session_id = self._split_composite_session_id(legacy_session_id)
            if parsed_username and parsed_session_id.startswith("session-"):
                username = username or parsed_username
                therapeutic_session_id = parsed_session_id

        if not legacy_session_id:
            legacy_session_id = self._build_legacy_session_id(username, therapeutic_session_id)

        if username and conversation.get("username") != username:
            updates["username"] = username
        if therapeutic_session_id and conversation.get("therapeutic_session_id") != therapeutic_session_id:
            updates["therapeutic_session_id"] = therapeutic_session_id
        if legacy_session_id and conversation.get("legacy_session_id") != legacy_session_id:
            updates["legacy_session_id"] = legacy_session_id

        if updates:
            updates["updated_at"] = datetime.utcnow()
            await conversations.update_one({"_id": conversation["_id"]}, {"$set": updates})
            conversation.update(updates)

        return {
            "chat_id": chat_id,
            "legacy_session_id": legacy_session_id,
            "username": username,
            "therapeutic_session_id": therapeutic_session_id,
            "conversation": conversation,
        }

    async def resolve_conversation_ref(
        self,
        conversation_ref: str,
        *,
        username: Optional[str] = None,
        therapeutic_session_id: Optional[str] = None,
        create: bool = False,
    ) -> Dict[str, Any]:
        """
        Resolver chat_id novo ou session_id legado para a mesma conversa.

        Ordem de busca:
        1. chat_id opaco
        2. par lógico (username, therapeutic_session_id)
        3. session_id legado composto
        """
        conversations = get_collection("conversations")
        conversation = None

        if conversation_ref:
            conversation = await conversations.find_one({"chat_id": conversation_ref})

        if not conversation and username and therapeutic_session_id:
            conversation = await conversations.find_one({
                "username": username,
                "therapeutic_session_id": therapeutic_session_id,
            })

        legacy_session_id = self._build_legacy_session_id(username, therapeutic_session_id)
        if not conversation and conversation_ref:
            parsed_username, parsed_session_id = self._split_composite_session_id(conversation_ref)
            if parsed_username and parsed_session_id.startswith("session-"):
                username = username or parsed_username
                therapeutic_session_id = therapeutic_session_id or parsed_session_id
                legacy_session_id = conversation_ref
                conversation = await conversations.find_one({"session_id": conversation_ref})
            else:
                conversation = await conversations.find_one({"session_id": conversation_ref})
                legacy_session_id = conversation_ref

        if not conversation and username and therapeutic_session_id:
            legacy_session_id = self._build_legacy_session_id(username, therapeutic_session_id)
            conversation = await conversations.find_one({"session_id": legacy_session_id})

        if conversation:
            return await self._ensure_conversation_identity(conversation, legacy_session_id)

        if not create:
            parsed_username, parsed_session_id = self._split_composite_session_id(conversation_ref or "")
            return {
                "chat_id": None,
                "legacy_session_id": conversation_ref or legacy_session_id,
                "username": username or parsed_username,
                "therapeutic_session_id": therapeutic_session_id or parsed_session_id,
                "conversation": None,
            }

        if not username or not therapeutic_session_id:
            parsed_username, parsed_session_id = self._split_composite_session_id(conversation_ref or "")
            username = username or parsed_username
            therapeutic_session_id = therapeutic_session_id or parsed_session_id

        chat_id = f"chat_{uuid.uuid4().hex}"
        legacy_session_id = self._build_legacy_session_id(username, therapeutic_session_id)
        now = datetime.utcnow()
        conversation_data = {
            "chat_id": chat_id,
            "session_id": legacy_session_id,
            "legacy_session_id": legacy_session_id,
            "therapeutic_session_id": therapeutic_session_id,
            "username": username,
            "created_at": now,
            "updated_at": now,
            "user_preferences": {},
            "message_count": 0,
            "is_active": True,
        }

        await conversations.insert_one(conversation_data)
        logger.info(
            "🆕 Nova conversa criada: chat_id=%s username=%s session_id=%s",
            chat_id,
            username,
            therapeutic_session_id,
        )

        return {
            "chat_id": chat_id,
            "legacy_session_id": legacy_session_id,
            "username": username,
            "therapeutic_session_id": therapeutic_session_id,
            "conversation": conversation_data,
        }
    
    async def start_or_get_conversation(
        self,
        session_id: str,
        username: Optional[str] = None,
        therapeutic_session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Iniciar ou recuperar conversa existente"""
        try:
            identity = await self.resolve_conversation_ref(
                session_id,
                username=username,
                therapeutic_session_id=therapeutic_session_id,
                create=True,
            )
            conversation = identity["conversation"] or {}
            exists = bool(conversation.get("_id"))
            logger.info(
                "📖 Conversa resolvida: chat_id=%s username=%s session_id=%s",
                identity["chat_id"],
                identity["username"],
                identity["therapeutic_session_id"],
            )

            return {
                "chat_id": identity["chat_id"],
                "session_id": identity["legacy_session_id"],
                "therapeutic_session_id": identity["therapeutic_session_id"],
                "username": identity["username"],
                "exists": exists,
                "user_preferences": conversation.get("user_preferences", {}),
                "created_at": conversation.get("created_at"),
                "updated_at": conversation.get("updated_at"),
            }
                
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar/recuperar conversa: {e}")
            raise
    
    async def process_user_message(self, session_id: str, user_message: str, session_objective: Optional[Dict[str, Any]] = None, is_voice_mode: bool = False) -> Dict[str, Any]:
        """
        Processar mensagem do usuário e gerar resposta da IA
        """
        try:
            identity = await self.resolve_conversation_ref(session_id, create=True)
            chat_id = identity.get("chat_id")
            session_id = identity.get("legacy_session_id") or session_id

            logger.info(f"💬 PROCESSANDO MENSAGEM para chat_id={chat_id}, sessão={session_id}")
            logger.info(f"📝 Mensagem do usuário: {user_message[:100]}...")
            logger.info(f"🎤 Modo de voz: {'ATIVO' if is_voice_mode else 'INATIVO'}")  # ✅ NOVO: Log do VoiceMode
            
            # ✅ NOVO: Detectar se é sessão de cadastro (session-1)
            # Extrair session_id original para verificar se é session-1
            original_session_id = session_id
            username_part = ""
            
            if "_" in session_id:
                try:
                    last_underscore_index = session_id.rfind("_")
                    if last_underscore_index != -1:
                        username_part = session_id[:last_underscore_index]
                        original_session_id = session_id[last_underscore_index + 1:]
                        logger.info(f"🔍 DETECÇÃO: session_id='{session_id}' -> username='{username_part}', original='{original_session_id}'")
                    else:
                        logger.warning(f"⚠️ Underscore não encontrado em: {session_id}")
                except Exception as ex:
                    logger.error(f"❌ Erro ao extrair session_id: {ex}")
            else:
                logger.info(f"🔍 DETECÇÃO: session_id='{session_id}' (sem underscore)")
            
            # Log da verificação de session-1
            is_registration_session = original_session_id == "session-1"
            logger.info(f"🎯 VERIFICAÇÃO: original_session_id='{original_session_id}', is_registration={is_registration_session}")
            
            # Se for session-1, usar nossa função de cadastro
            if is_registration_session:
                logger.info(f"🔒 DETECTADA SESSÃO DE CADASTRO - usando função própria para {session_id}")
                return await self._handle_registration_session(session_id, user_message, is_voice_mode)
            
            # Para outras sessões, usar fluxo normal com OpenAI
            logger.info(f"🤖 SESSÃO NORMAL - usando OpenAI para {session_id}")
            
            # Criar ou recuperar conversa
            await self.start_or_get_conversation(session_id)
            
            # Extrair username do session_id para buscar preferências
            username = self._extract_username_from_session_id(session_id) or 'default'
            
            # Carregar preferências do usuário (voz, etc.)
            users_collection = get_collection("users")
            user = await users_collection.find_one({"username": username})
            
            selected_voice = "pt-BR-Neural2-B"  # padrão masculino
            voice_enabled = True
            
            if user and user.get("preferences"):
                preferences = user["preferences"]
                selected_voice = preferences.get("selected_voice", selected_voice)
                voice_enabled = preferences.get("voice_enabled", voice_enabled)
            
            # ✅ NOVO: Forçar voice_enabled=True quando em VoiceMode
            if is_voice_mode:
                voice_enabled = True
                logger.info(f"🎤 VoiceMode detectado - Forçando síntese de voz (voice_enabled=True)")
            
            logger.info(f"🔊 Configuração de voz - voice_enabled: {voice_enabled}, selected_voice: {selected_voice}")
            
            # Buscar initial_prompt se não foi fornecido via session_objective
            initial_prompt = None
            if not session_objective:
                initial_prompt = await self._get_session_initial_prompt(session_id)
                if initial_prompt:
                    logger.info(f"📋 Initial prompt encontrado para sessão {session_id}")
                else:
                    logger.warning(f"⚠️ Initial prompt não encontrado para sessão {session_id}")
            
            # Gerar resposta da IA
            ai_response_data = await self._get_ai_response(
                user_message, 
                session_id, 
                selected_voice, 
                voice_enabled,
                session_objective,
                initial_prompt,
                is_voice_mode  # ✅ NOVO: Passar indicador de VoiceMode
            )
            
            # Salvar mensagem do usuário
            user_message_id = await self._save_message(session_id, "user", user_message)
            
            # Salvar resposta da IA
            ai_message_id = await self._save_message(
                session_id, 
                "ai", 
                ai_response_data["response"], 
                ai_response_data.get("audio_url")
            )
            
            # Atualizar contador de mensagens
            await self._update_message_count(session_id)
            
            # Verificar se a mensagem indica fim de conversa
            conversation_ended = self.detect_conversation_end(user_message)
            if conversation_ended:
                logger.info(f"🔚 Fim de conversa detectado para sessão: {session_id}")
                # Gerar contexto em background (não bloquear resposta)
                import asyncio
                asyncio.create_task(self.finalize_session_context(session_id, manual_termination=False))
            
            return {
                "success": True,
                "data": {
                    "chat_id": chat_id,
                    "session_id": session_id,
                    "therapeutic_session_id": identity.get("therapeutic_session_id"),
                    "user_message": {
                        "id": user_message_id,
                        "content": user_message
                    },
                    "ai_response": {
                        "id": ai_message_id,
                        "content": ai_response_data["response"],
                        "audioUrl": ai_response_data.get("audio_url"),
                        "provider": ai_response_data.get("provider", "unknown"),
                        "model": ai_response_data.get("model", "unknown")
                    },
                    "conversation_ended": conversation_ended
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {e}")
            return {
                "success": False,
                "error": f"Erro ao processar mensagem: {str(e)}"
            }

    async def process_user_message_stream(
        self,
        session_id: str,
        user_message: str,
        session_objective: Optional[Dict[str, Any]] = None,
        is_voice_mode: bool = True,
        trace_id: Optional[str] = None,
        client_metrics: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a voice message and emit SSE-ready events."""
        trace_id = trace_id or f"trace_{uuid.uuid4().hex}"
        started_at = time.perf_counter()
        ai_done_data: Dict[str, Any] = {}
        full_response = ""
        audio_sequence = 0
        tts_stream_failed = False
        audio_url = None
        first_audio_ms: Optional[int] = None
        first_text_ms: Optional[int] = None

        try:
            identity = await self.resolve_conversation_ref(session_id, create=True)
            chat_id = identity.get("chat_id")
            legacy_session_id = identity.get("legacy_session_id") or session_id
            username = identity.get("username") or self._extract_username_from_session_id(legacy_session_id)

            if not username:
                raise ValueError(f"Session ID inválido: {legacy_session_id}")

            parsed_original_session_id = identity.get("therapeutic_session_id") or legacy_session_id.split("_")[-1]
            if parsed_original_session_id == "session-1":
                result = await self.process_user_message(
                    legacy_session_id,
                    user_message,
                    session_objective=session_objective,
                    is_voice_mode=is_voice_mode,
                )
                yield {
                    "event": "meta",
                    "data": {
                        "trace_id": trace_id,
                        "chat_id": chat_id,
                        "session_id": legacy_session_id,
                        "streaming": False,
                        "fallback_reason": "registration_session",
                    },
                }
                ai_response = (result.get("data") or {}).get("ai_response") or {}
                if ai_response.get("content"):
                    yield {"event": "text_delta", "data": {"delta": ai_response["content"], "trace_id": trace_id}}
                if ai_response.get("audioUrl"):
                    yield {"event": "audio_url", "data": {"audio_url": ai_response["audioUrl"], "trace_id": trace_id}}
                yield {"event": "done", "data": {"trace_id": trace_id, "result": result, "streaming": False}}
                return

            await self.start_or_get_conversation(legacy_session_id)

            users_collection = get_collection("users")
            user = await users_collection.find_one({"username": username})
            selected_voice = "pt-BR-Neural2-B"
            voice_enabled = True
            if user and user.get("preferences"):
                preferences = user["preferences"]
                selected_voice = preferences.get("selected_voice", selected_voice)
                voice_enabled = preferences.get("voice_enabled", voice_enabled)
            if is_voice_mode:
                voice_enabled = True

            initial_prompt = None
            if not session_objective:
                initial_prompt = await self._get_session_initial_prompt(legacy_session_id)

            user_profile = await self.user_profile_service.get_user_profile(username)
            conversation_history = await self._get_conversation_context(legacy_session_id)
            previous_session_context = await self._get_previous_session_context(legacy_session_id)

            user_message_id = await self._save_message(legacy_session_id, "user", user_message)

            yield {
                "event": "meta",
                "data": {
                    "trace_id": trace_id,
                    "chat_id": chat_id,
                    "session_id": legacy_session_id,
                    "therapeutic_session_id": identity.get("therapeutic_session_id"),
                    "user_message": {"id": user_message_id, "content": user_message},
                    "voice": selected_voice,
                    "streaming": True,
                    "client_metrics": client_metrics or {},
                    "started_at": datetime.utcnow().isoformat(),
                },
            }

            ai_request = {
                "message": user_message,
                "session_id": legacy_session_id,
                "username": username,
                "user_profile": user_profile,
                "conversation_history": conversation_history,
                "session_objective": session_objective,
                "initial_prompt": initial_prompt,
                "previous_session_context": previous_session_context,
                "is_voice_mode": True,
                "trace_id": trace_id,
            }

            chunker = SentenceChunker(
                max_chars=settings.voice_chunks.max_chars,
                max_wait_ms=settings.voice_chunks.max_wait_ms,
                min_timed_flush_chars=settings.voice_chunks.min_timed_flush_chars,
                min_timed_flush_words=settings.voice_chunks.min_timed_flush_words,
            )

            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{self.ai_service_url}/openai/chat/stream",
                    json=ai_request,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status_code != 200:
                        raise RuntimeError(f"AI stream HTTP {response.status_code}: {await response.aread()}")

                    current_event = "message"
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("event:"):
                            current_event = line.split(":", 1)[1].strip()
                            continue
                        if not line.startswith("data:"):
                            continue

                        payload = json.loads(line.split(":", 1)[1].strip() or "{}")
                        if current_event == "text_delta":
                            delta = payload.get("delta", "")
                            if not delta:
                                continue
                            if first_text_ms is None:
                                first_text_ms = now_ms(started_at)
                            full_response += delta
                            yield {
                                "event": "text_delta",
                                "data": {
                                    "delta": delta,
                                    "trace_id": trace_id,
                                    "elapsed_ms": now_ms(started_at),
                                },
                            }
                            if voice_enabled:
                                for text_chunk in chunker.push(delta):
                                    async for audio_event in self._stream_tts_or_batch_chunk(
                                        text_chunk,
                                        selected_voice,
                                        trace_id,
                                        audio_sequence,
                                        started_at,
                                    ):
                                        if audio_event["event"] == "audio_chunk":
                                            audio_sequence += 1
                                            if first_audio_ms is None:
                                                first_audio_ms = now_ms(started_at)
                                        elif audio_event["event"] == "audio_url":
                                            audio_sequence += 1
                                            audio_url = audio_event["data"].get("audio_url") or audio_url
                                            if first_audio_ms is None:
                                                first_audio_ms = now_ms(started_at)
                                        elif audio_event["event"] == "error" and audio_event["data"].get("stage") == "tts_stream":
                                            tts_stream_failed = True
                                        yield audio_event
                        elif current_event == "done":
                            ai_done_data = payload

            remaining = chunker.flush()
            if remaining and voice_enabled:
                async for audio_event in self._stream_tts_or_batch_chunk(
                    remaining,
                    selected_voice,
                    trace_id,
                    audio_sequence,
                    started_at,
                ):
                    if audio_event["event"] == "audio_chunk":
                        audio_sequence += 1
                        if first_audio_ms is None:
                            first_audio_ms = now_ms(started_at)
                    elif audio_event["event"] == "audio_url":
                        audio_sequence += 1
                        audio_url = audio_event["data"].get("audio_url") or audio_url
                        if first_audio_ms is None:
                            first_audio_ms = now_ms(started_at)
                    elif audio_event["event"] == "error" and audio_event["data"].get("stage") == "tts_stream":
                        tts_stream_failed = True
                    yield audio_event

            final_text = (ai_done_data.get("response") or full_response).strip()
            if voice_enabled and audio_sequence == 0 and final_text:
                audio_url = await self._generate_audio(final_text, selected_voice, is_voice_mode=True)
                if audio_url:
                    yield {
                        "event": "audio_url",
                        "data": {
                            "audio_url": audio_url,
                            "trace_id": trace_id,
                            "sequence": audio_sequence,
                            "segment": False,
                            "elapsed_ms": now_ms(started_at),
                        },
                    }
                    audio_sequence += 1
                    if first_audio_ms is None:
                        first_audio_ms = now_ms(started_at)

            ai_message_id = await self._save_message(legacy_session_id, "ai", final_text, audio_url)
            await self._update_message_count(legacy_session_id)

            conversation_ended = self.detect_conversation_end(user_message)
            if conversation_ended:
                import asyncio

                asyncio.create_task(self.finalize_session_context(legacy_session_id, manual_termination=False))

            metrics = {
                "gateway_total_ms": now_ms(started_at),
                "first_text_delta_ms": first_text_ms,
                "first_audio_chunk_ms": first_audio_ms,
                "audio_chunks": audio_sequence,
                "tts_stream_failed": tts_stream_failed,
                "client_metrics": client_metrics or {},
                **(ai_done_data.get("metrics") or {}),
            }
            yield {
                "event": "metrics",
                "data": {"trace_id": trace_id, "metrics": metrics},
            }
            yield {
                "event": "done",
                "data": {
                    "trace_id": trace_id,
                    "success": True,
                    "data": {
                        "chat_id": chat_id,
                        "session_id": legacy_session_id,
                        "therapeutic_session_id": identity.get("therapeutic_session_id"),
                        "user_message": {"id": user_message_id, "content": user_message},
                        "ai_response": {
                            "id": ai_message_id,
                            "content": final_text,
                            "audioUrl": audio_url,
                            "provider": ai_done_data.get("provider", "unknown"),
                            "model": ai_done_data.get("model", "unknown"),
                        },
                        "conversation_ended": conversation_ended,
                    },
                    "metrics": metrics,
                },
            }
        except Exception as exc:
            logger.error("❌ Erro no stream de mensagem: %s", exc, exc_info=True)
            yield {
                "event": "error",
                "data": {
                    "trace_id": trace_id,
                    "error": str(exc),
                    "elapsed_ms": now_ms(started_at),
                },
            }

    async def _stream_tts_or_batch_chunk(
        self,
        text: str,
        voice: str,
        trace_id: str,
        sequence: int,
        started_at: float,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream PCM for a text chunk, or immediately synthesize that chunk as batch audio."""
        emitted_audio = False
        stream_failed = False

        async for audio_event in self._stream_tts_chunk(text, voice, trace_id, sequence, started_at):
            if audio_event["event"] == "audio_chunk":
                emitted_audio = True
            elif audio_event["event"] == "error":
                stream_failed = True
            yield audio_event

        if emitted_audio:
            return

        audio_url = await self._generate_audio(text, voice, is_voice_mode=True)
        if audio_url:
            if stream_failed:
                logger.info("🔊 Fallback batch por trecho gerado após falha no streaming TTS")
            yield {
                "event": "audio_url",
                "data": {
                    "audio_url": audio_url,
                    "trace_id": trace_id,
                    "sequence": sequence,
                    "segment": True,
                    "text_length": len(text),
                    "elapsed_ms": now_ms(started_at),
                },
            }
        elif stream_failed:
            logger.warning("⚠️ Streaming TTS falhou e fallback batch por trecho não gerou áudio")

    async def _stream_tts_chunk(
        self,
        text: str,
        voice: str,
        trace_id: str,
        sequence: int,
        started_at: float,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        async for event in self.voice_synthesis_service.stream_tts_chunk(
            text,
            voice,
            trace_id,
            sequence,
            started_at,
        ):
            yield event
    
    async def get_conversation_history(self, session_id: str) -> Dict[str, Any]:
        """Obter histórico completo de uma conversa"""
        return await self.conversation_repo.get_history(session_id)
    
    async def update_conversation_data(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Atualizar dados da conversa"""
        return await self.conversation_repo.update(session_id, update_data)
    
    async def _save_message(self, session_id: str, message_type: str, content: str, audio_url: Optional[str] = None) -> str:
        """Salvar mensagem no MongoDB"""
        return await self.conversation_repo.save_message(session_id, message_type, content, audio_url)
    
    async def _get_ai_response(self, user_message: str, session_id: str, selected_voice: str, voice_enabled: bool = True, session_objective: Optional[Dict[str, Any]] = None, initial_prompt: Optional[str] = None, is_voice_mode: bool = False) -> Dict[str, Any]:
        """Obter resposta da IA usando AI Service com contexto completo"""
        try:
            logger.info(f"🤖 Chamando AI Service para sessão: {session_id}")
            
            # ✅ NOVO: Log adicional para VoiceMode
            if is_voice_mode:
                logger.info(f"🎤 VoiceMode ativo - Priorizando síntese de voz para resposta fluida")
            
            # ✅ NOVO: Extrair username do session_id
            username = self._extract_username_from_session_id(session_id)
            if not username:
                logger.error(f"❌ Não foi possível extrair username do session_id: {session_id}")
                raise ValueError(f"Session ID inválido: {session_id}")
            
            # ✅ NOVO: Buscar perfil completo do usuário para enviar ao AI Service
            user_profile = await self.user_profile_service.get_user_profile(username)
            logger.info(f"👤 Perfil do usuário {username}: {'encontrado' if user_profile else 'não encontrado'}")
            
            # ✅ NOVO: Obter contexto da conversa atual
            conversation_history = await self._get_conversation_context(session_id)
            
            # ✅ NOVO: Buscar contexto da sessão anterior (se existir)
            previous_session_context = await self._get_previous_session_context(session_id)
            
            # Preparar dados para o AI Service
            ai_request = {
                "message": user_message,
                "session_id": session_id,
                "username": username,  # ✅ NOVO: Incluir username
                "user_profile": user_profile,  # ✅ NOVO: Perfil completo do usuário
                "conversation_history": conversation_history,
                "session_objective": session_objective,
                "initial_prompt": initial_prompt,
                "previous_session_context": previous_session_context  # ✅ NOVO: Contexto da sessão anterior
            }
            
            logger.info(f"📤 Enviando para AI Service - usuário: {username}, sessão: {session_id}, mensagem: {user_message[:50]}..., histórico: {len(conversation_history)} msgs, contexto anterior: {'sim' if previous_session_context else 'não'}")
            
            # ✅ DEBUG: Log detalhado do que está sendo enviado
            logger.info(f"🔍 DEBUG GATEWAY - Dados sendo enviados para AI Service:")
            logger.info(f"  - message: {len(user_message)} chars")
            logger.info(f"  - session_id: {session_id}")
            logger.info(f"  - username: {username}")
            logger.info(f"  - user_profile: {'✅' if user_profile else '❌'}")
            logger.info(f"  - conversation_history: {len(conversation_history)} mensagens")
            logger.info(f"  - session_objective: {'✅' if session_objective else '❌'}")
            logger.info(f"  - initial_prompt: {'✅' if initial_prompt else '❌'}")
            logger.info(f"  - previous_session_context: {'✅' if previous_session_context else '❌'}")
            
            if previous_session_context:
                logger.info(f"🔍 DEBUG - previous_session_context sendo enviado: {len(str(previous_session_context))} chars")
                logger.info(f"🔍 DEBUG - Chaves: {list(previous_session_context.keys()) if isinstance(previous_session_context, dict) else 'Não é dict'}")
                if isinstance(previous_session_context, dict) and previous_session_context.get("registration_data"):
                    reg_data = previous_session_context["registration_data"]
                    if reg_data.get("ocupacao"):
                        logger.info(f"🔍 DEBUG - Ocupação no registration_data: '{reg_data['ocupacao']}'")
                    else:
                        logger.warning(f"⚠️ DEBUG - Ocupação NÃO encontrada no registration_data")
                else:
                    logger.warning(f"⚠️ DEBUG - registration_data NÃO encontrado no previous_session_context")
            else:
                logger.error(f"❌ DEBUG - previous_session_context está VAZIO/NULO sendo enviado para AI Service!")
            
            # ✅ IMPLEMENTAÇÃO REAL: Chamar AI Service via HTTP
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.ai_service_url}/chat",
                        json=ai_request,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        ai_data = response.json()
                        ai_response = ai_data.get("response", "")
                        
                        logger.info(f"✅ Resposta recebida do AI Service para {username}: {ai_response[:100]}...")
                        
                        ai_service_response = {
                            "response": ai_response,
                            "model": ai_data.get("model", "unknown"),
                            "session_id": session_id,
                            "username": username,
                            "timestamp": datetime.utcnow().isoformat(),
                            "provider": ai_data.get("provider", "openai"),
                            "success": True
                        }
                        
                    else:
                        logger.error(f"❌ AI Service retornou erro {response.status_code}: {response.text}")
                        # Fallback para resposta padrão
                        ai_service_response = self._get_fallback_response(user_message)
                        ai_service_response.update({
                            "session_id": session_id,
                            "username": username,
                            "timestamp": datetime.utcnow().isoformat(),
                            "error": f"AI Service HTTP {response.status_code}"
                        })
                        
            except httpx.ConnectError:
                logger.warning(f"⚠️ AI Service não disponível, usando resposta fallback para {username}")
                ai_service_response = self._get_fallback_response(user_message)
                ai_service_response.update({
                    "session_id": session_id,
                    "username": username,
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": "AI Service unavailable"
                })
                
            except Exception as http_error:
                logger.error(f"❌ Erro na chamada HTTP para AI Service: {http_error}")
                ai_service_response = self._get_fallback_response(user_message)
                ai_service_response.update({
                    "session_id": session_id,
                    "username": username,
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(http_error)
                })
            
            # Usar a resposta do AI Service (ou fallback)
            simulated_response = ai_service_response
            
            # Gerar áudio se habilitado
            audio_url = None
            if voice_enabled:
                if is_voice_mode:
                    logger.info(f"🎤 Iniciando síntese de voz para VoiceMode - Texto: {simulated_response['response'][:50]}...")
                audio_url = await self._generate_audio(simulated_response['response'], selected_voice, is_voice_mode)
            
            return {
                "response": simulated_response['response'],
                "model": simulated_response['model'],
                "session_id": session_id,
                "username": username,  # ✅ NOVO: Username na resposta
                "timestamp": simulated_response['timestamp'],
                "provider": simulated_response['provider'],
                "audio_url": audio_url,
                "voice_enabled": voice_enabled,
                "selected_voice": selected_voice
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter resposta da IA: {e}")
            
            # Resposta de fallback
            fallback_response = f"Desculpe, estou com dificuldades técnicas. Pode repetir sua mensagem?"
            
            return {
                "response": fallback_response,
                "model": "fallback",
                "session_id": session_id,
                "username": username if 'username' in locals() else "unknown",  # ✅ NOVO: Username mesmo no fallback
                "timestamp": datetime.utcnow().isoformat(),
                "provider": "fallback",
                "audio_url": None,
                "voice_enabled": voice_enabled,
                "selected_voice": selected_voice,
                "error": str(e)
            }

    async def _get_previous_session_context(self, current_session_id: str) -> Optional[Dict[str, Any]]:
        """Buscar contexto da sessão anterior para enviar ao AI Service"""
        return await self.session_context_service.get_previous_context(current_session_id)

    async def _generate_audio(self, text: str, voice: str, is_voice_mode: bool = False) -> Optional[str]:
        return await self.voice_synthesis_service.generate_audio(text, voice, is_voice_mode)

    def _gateway_audio_url(self, audio_url: str) -> str:
        return self.voice_synthesis_service.gateway_audio_url(audio_url)

    def _get_fallback_response(self, user_message: str) -> Dict[str, Any]:
        """
        Resposta fallback quando AI Service não está disponível
        """
        # Resposta padrão empática baseada na abordagem Rogers
        default_responses = [
            "Entendo como você está se sentindo. Pode me contar mais sobre isso?",
            "Isso parece ser muito importante para você. Como isso te afeta?",
            "Percebo que há algo significativo no que você está compartilhando. Gostaria de explorar isso mais?",
            "Suas palavras me mostram muito sobre seus sentimentos. O que mais vem à sua mente sobre isso?",
            "Compreendo que isso é parte da sua experiência. Como você se sente em relação a isso agora?",
            "Obrigado por compartilhar isso comigo. Que sentimentos isso desperta em você?",
            "Vejo que isso tem um significado especial para você. Pode me ajudar a entender melhor?",
            "Suas reflexões são muito valiosas. O que você pensa sobre essa situação?",
            "Sinto que há algo profundo no que você está expressando. Como isso se conecta com você?",
            "Agradeço sua abertura em compartilhar isso. O que isso representa para você?"
        ]
        
        # Escolher resposta baseada no hash da mensagem para consistência
        import hashlib
        hash_obj = hashlib.md5(user_message.encode())
        response_index = int(hash_obj.hexdigest(), 16) % len(default_responses)
        ai_response_text = default_responses[response_index]
        
        return {
            "response": ai_response_text,
            "audio_url": None,
            "provider": "fallback",
            "model": "empathic_fallback"
        }
    
    async def _get_conversation_context(self, session_id: str) -> List[Dict[str, Any]]:
        """Obter contexto da conversa para enviar ao AI Service"""
        return await self.conversation_repo.get_context(session_id)

    async def _get_session_initial_prompt(self, session_id: str) -> Optional[str]:
        """Buscar o initial_prompt da sessão terapêutica do usuário"""
        return await self.conversation_repo.get_initial_prompt(session_id)
    
    async def _update_message_count(self, session_id: str):
        """Atualizar contador de mensagens da conversa"""
        await self.conversation_repo.update_message_count(session_id)

    # ===== SISTEMA DE CONTEXTO DE SESSÃO =====

    async def finalize_session_context(self, session_id: str, manual_termination: bool = False) -> Dict[str, Any]:
        """Finalizar sessão e gerar contexto/resumo da conversa"""
        return await self.session_context_service.finalize_session_context(session_id, manual_termination)

    async def _create_next_session_automatically(self, current_session_id: str, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Criar APENAS a próxima sessão automaticamente usando AI Service (1 a 1)
        """
        return await self.next_session_service.create_next_session_automatically(
            current_session_id,
            session_context,
        )

    def _extract_username_from_session_id(self, session_id: str) -> Optional[str]:
        """
        Extrair username do session_id no formato 'username_session-X'
        """
        try:
            username, original_session_id = self._split_composite_session_id(session_id)
            if username and original_session_id.startswith("session-"):
                return username

            # Para sessões legacy sem username
            if session_id in ["default", "test"]:
                return "anonymous"

            logger.warning(f"⚠️ Session ID sem username: {session_id}")
            return None
                    
        except Exception as e:
            logger.error(f"❌ Erro ao extrair username do session_id {session_id}: {e}")
            return None

    def _validate_session_ownership(self, session_id: str, username: str) -> bool:
        """
        Validar se o usuário tem acesso à sessão
        """
        try:
            extracted_username = self._extract_username_from_session_id(session_id)
            if not extracted_username:
                logger.error(f"❌ Não foi possível extrair username do session_id: {session_id}")
                return False
                
            if extracted_username != username:
                logger.error(f"❌ Tentativa de acesso não autorizado: {username} tentou acessar sessão de {extracted_username}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao validar propriedade da sessão: {e}")
            return False

    def detect_conversation_end(self, message: str) -> bool:
        """Detectar se a mensagem indica fim de conversa"""
        return self.session_context_service.detect_conversation_end(message)

    async def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obter contexto salvo de uma sessão"""
        return await self.session_context_service.get_session_context(session_id)

    async def list_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Listar conversas recentes"""
        return await self.conversation_repo.list_recent(limit)

    async def get_conversation_by_session_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Busca uma conversa por chat_id novo ou session_id legado e retorna como dicionário."""
        return await self.conversation_repo.get_by_session_id(session_id)

    async def generate_chat_title(self, chat_id: str, mode: str = "initial") -> Dict[str, Any]:
        return await self.chat_title_service.generate_chat_title(
            chat_id,
            mode,
            self._get_conversation_context,
        )

    # ✅ NOVO: Sistema de cadastro/onboarding para session-1
    async def _handle_registration_session(self, session_id: str, user_message: str, is_voice_mode: bool = False) -> Dict[str, Any]:
        """
        Gerenciar a sessão de cadastro (session-1) com perguntas próprias, sem OpenAI
        """
        return await self.registration_service.handle_session(session_id, user_message, is_voice_mode)
    
    async def _save_user_profile(self, username: str, registration_data: Dict[str, Any]):
        """
        Salvar perfil completo e padronizado do usuário na coleção users
        """
        await self.user_profile_service.save_user_profile(username, registration_data)
