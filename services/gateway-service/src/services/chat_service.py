"""
Serviço de chat - orquestra conversas e mensagens
"""

import logging
import os
import uuid
import base64
import json
import time
from typing import AsyncGenerator, Dict, List, Optional, Any
from datetime import datetime
import httpx
from ..models.database import get_collection
from .streaming_utils import SentenceChunker, now_ms

logger = logging.getLogger(__name__)

class ChatService:
    """Serviço de chat com persistência MongoDB"""
    
    def __init__(self):
        self.ai_service_url = os.getenv("AI_SERVICE_URL", "http://ai-service:8001")
        self.base_voice_url = os.getenv("VOICE_SERVICE_URL", "http://voice-service:8004")

    def _split_composite_session_id(self, session_id: str) -> tuple[Optional[str], str]:
        """
        Separar session_id composto no formato '{username}_session-N'.
        O username pode conter underscores, então a separação deve usar a última ocorrência de '_session-'.
        """
        if not session_id:
            return None, session_id

        separator_index = session_id.rfind("_session-")
        if separator_index == -1:
            return None, session_id

        return session_id[:separator_index], session_id[separator_index + 1:]

    def _build_legacy_session_id(self, username: Optional[str], therapeutic_session_id: Optional[str]) -> str:
        """Chave legada usada por documentos antigos: username + session-N."""
        if username and therapeutic_session_id:
            return f"{username}_{therapeutic_session_id}"
        return therapeutic_session_id or username or "default"

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
        tts_failed = False
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

            user_profile = await self._get_user_profile(username)
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
                max_chars=int(os.getenv("VOICE_CHUNK_MAX_CHARS", "220")),
                max_wait_ms=int(os.getenv("VOICE_CHUNK_MAX_WAIT_MS", "700")),
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
                            if voice_enabled and not tts_failed:
                                for text_chunk in chunker.push(delta):
                                    async for audio_event in self._stream_tts_chunk(
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
                                        elif audio_event["event"] == "error":
                                            tts_failed = True
                                        yield audio_event
                        elif current_event == "done":
                            ai_done_data = payload

            remaining = chunker.flush()
            if remaining and voice_enabled and not tts_failed:
                async for audio_event in self._stream_tts_chunk(
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
                    elif audio_event["event"] == "error":
                        tts_failed = True
                    yield audio_event

            final_text = (ai_done_data.get("response") or full_response).strip()
            audio_url = None
            if voice_enabled and audio_sequence == 0 and final_text:
                audio_url = await self._generate_audio(final_text, selected_voice, is_voice_mode=True)
                if audio_url:
                    yield {"event": "audio_url", "data": {"audio_url": audio_url, "trace_id": trace_id}}

            ai_message_id = await self._save_message(legacy_session_id, "ai", final_text, audio_url)
            await self._update_message_count(legacy_session_id)
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
                "tts_stream_failed": tts_failed,
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

    async def _stream_tts_chunk(
        self,
        text: str,
        voice: str,
        trace_id: str,
        sequence: int,
        started_at: float,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Call Voice Service streaming endpoint and emit base64 PCM chunks."""
        if not text.strip():
            return

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_voice_url}/api/v1/synthesize-stream",
                    json={
                        "text": text,
                        "voice_name": voice,
                        "language_code": "pt-BR",
                    },
                ) as response:
                    if response.status_code != 200:
                        detail = (await response.aread()).decode("utf-8", errors="ignore")
                        logger.warning("⚠️ Voice streaming indisponível: HTTP %s %s", response.status_code, detail)
                        yield {
                            "event": "error",
                            "data": {
                                "trace_id": trace_id,
                                "stage": "tts_stream",
                                "error": f"voice_stream_http_{response.status_code}",
                                "recoverable": True,
                            },
                        }
                        return

                    sample_rate = int(response.headers.get("X-Audio-Sample-Rate", "24000"))
                    encoding = response.headers.get("X-Audio-Encoding", "PCM")
                    chunk_sequence = sequence
                    async for chunk in response.aiter_bytes():
                        if not chunk:
                            continue
                        yield {
                            "event": "audio_chunk",
                            "data": {
                                "trace_id": trace_id,
                                "sequence": chunk_sequence,
                                "audio": base64.b64encode(chunk).decode("ascii"),
                                "sample_rate_hz": sample_rate,
                                "encoding": encoding,
                                "elapsed_ms": now_ms(started_at),
                            },
                        }
                        chunk_sequence += 1
        except Exception as exc:
            logger.warning("⚠️ Falha no streaming TTS: %s", exc)
            yield {
                "event": "error",
                "data": {
                    "trace_id": trace_id,
                    "stage": "tts_stream",
                    "error": str(exc),
                    "recoverable": True,
                },
            }
    
    async def get_conversation_history(self, session_id: str) -> Dict[str, Any]:
        """Obter histórico completo de uma conversa"""
        try:
            messages = get_collection("messages")
            identity = await self.resolve_conversation_ref(session_id)
            chat_id = identity.get("chat_id")
            session_id = identity.get("legacy_session_id") or session_id
            
            # 🔒 CORREÇÃO CRÍTICA: Extrair username para validação adicional
            username = identity.get("username") or self._extract_username_from_session_id(session_id)
            
            # Construir query com dupla validação
            if chat_id:
                query = {"$or": [{"chat_id": chat_id}, {"session_id": session_id}]}
            else:
                query = {"session_id": session_id}
            if username:
                # 🔒 Adicionar filtro por username para segurança adicional
                query["username"] = username
                logger.info(f"📖 Carregando histórico com validação dupla - session_id: {session_id}, username: {username}")
            else:
                logger.warning(f"⚠️ Carregando histórico apenas por session_id (legado): {session_id}")
            
            # Buscar todas as mensagens da sessão com validação de usuário
            cursor = messages.find(
                query,
                sort=[("created_at", 1)]
            )
            
            history = []
            async for msg in cursor:
                history.append({
                    "id": str(msg["_id"]),
                    "type": msg["type"],
                    "content": msg["content"],
                    "audio_url": msg.get("audio_url"),
                    "created_at": msg["created_at"].isoformat() if msg.get("created_at") else None
                })
            
            logger.info(f"📖 Histórico carregado para {session_id}: {len(history)} mensagens (username: {username})")
            
            return {
                "chat_id": chat_id,
                "session_id": session_id,
                "therapeutic_session_id": identity.get("therapeutic_session_id"),
                "username": username,
                "history": history,
                "message_count": len(history)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter histórico: {e}")
            raise
    
    async def update_conversation_data(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Atualizar dados da conversa"""
        try:
            conversations = get_collection("conversations")
            identity = await self.resolve_conversation_ref(session_id, create=True)
            
            update_data["updated_at"] = datetime.utcnow()
            if identity.get("chat_id"):
                query = {"chat_id": identity["chat_id"]}
            else:
                query = {"session_id": identity.get("legacy_session_id") or session_id}
            
            result = await conversations.update_one(
                query,
                {"$set": update_data}
            )
            
            return result.modified_count > 0 or result.matched_count > 0
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar conversa: {e}")
            raise
    
    async def _save_message(self, session_id: str, message_type: str, content: str, audio_url: Optional[str] = None) -> str:
        """Salvar mensagem no MongoDB"""
        try:
            messages = get_collection("messages")
            identity = await self.resolve_conversation_ref(session_id)
            chat_id = identity.get("chat_id")
            session_id = identity.get("legacy_session_id") or session_id
            
            # 🔒 CORREÇÃO CRÍTICA: Extrair username do session_id para validação adicional
            # Formato esperado: "username_original_session_id"
            username = identity.get("username") or self._extract_username_from_session_id(session_id)
            
            message_data = {
                "chat_id": chat_id,
                "session_id": session_id,
                "therapeutic_session_id": identity.get("therapeutic_session_id"),
                "username": username,  # 🔒 Adicionar username para dupla validação
                "type": message_type,
                "content": content,
                "audio_url": audio_url,
                "created_at": datetime.utcnow()
            }
            
            result = await messages.insert_one(message_data)
            
            # Log de auditoria para rastreamento
            logger.info(f"💾 Mensagem salva - session_id: {session_id}, username: {username}, type: {message_type}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar mensagem: {e}")
            raise
    
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
            user_profile = await self._get_user_profile(username)
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
        """
        Buscar contexto da sessão anterior para enviar ao AI Service
        """
        try:
            # Extrair username e número da sessão atual
            username = self._extract_username_from_session_id(current_session_id)
            if not username:
                return None
                
            current_session_number = self._extract_session_number(current_session_id)
            if current_session_number <= 1:
                logger.info(f"🔍 Session-{current_session_number}: não há sessão anterior")
                return None
            
            # Buscar sessão anterior (session-X -> session-(X-1))
            previous_session_number = current_session_number - 1
            previous_session_id = f"{username}_session-{previous_session_number}"
            
            logger.info(f"🔍 Buscando contexto da sessão anterior: {previous_session_id}")
            
            # ✅ CORREÇÃO: Buscar contexto na coleção session_contexts primeiro
            session_contexts = get_collection("session_contexts")
            context_doc = await session_contexts.find_one({"session_id": previous_session_id})
            
            if context_doc:
                context = context_doc.get("context", {})
                logger.info(f"✅ Contexto encontrado da sessão anterior: {len(str(context))} chars")
                
                # Buscar registration_data da conversation se necessário
                conversations = get_collection("conversations")
                previous_conversation = await conversations.find_one({"session_id": previous_session_id})
                
                # Retornar contexto completo incluindo registration_data
                return {
                    "session_id": previous_session_id,
                    "registration_data": previous_conversation.get("registration_data", {}) if previous_conversation else {},  # ✅ NOVO: Dados de registro
                    "session_context": context,  # ✅ NOVO: Contexto completo da sessão
                    # Campos principais para compatibilidade
                    "summary": context.get("summary", ""),
                    "main_themes": context.get("main_themes", []),
                    "key_insights": context.get("key_insights", []),
                    "emotional_state": context.get("emotional_state", {}),
                    "future_sessions": context.get("future_sessions", {}),
                    "user_progress": context.get("user_progress", {})
                }
            else:
                # ✅ FALLBACK: Para sessões antigas que ainda têm contexto na coleção conversations
                logger.warning(f"⚠️ Contexto não encontrado em session_contexts, tentando fallback para {previous_session_id}")
                conversations = get_collection("conversations")
                previous_conversation = await conversations.find_one({"session_id": previous_session_id})
                
                if previous_conversation and previous_conversation.get("session_context"):
                    context = previous_conversation["session_context"]
                    logger.info(f"✅ Contexto encontrado via fallback da sessão anterior: {len(str(context))} chars")
                    
                    # Retornar contexto completo incluindo registration_data
                    return {
                        "session_id": previous_session_id,
                        "registration_data": previous_conversation.get("registration_data", {}),  # ✅ NOVO: Dados de registro
                        "session_context": context,  # ✅ NOVO: Contexto completo da sessão
                        # Campos principais para compatibilidade
                        "summary": context.get("summary", ""),
                        "main_themes": context.get("main_themes", []),
                        "key_insights": context.get("key_insights", []),
                        "emotional_state": context.get("emotional_state", {}),
                        "future_sessions": context.get("future_sessions", {}),
                        "user_progress": context.get("user_progress", {})
                    }
                else:
                    logger.warning(f"⚠️ Contexto não encontrado para sessão anterior: {previous_session_id}")
                    return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar contexto da sessão anterior: {e}")
            return None

    async def _generate_audio(self, text: str, voice: str, is_voice_mode: bool = False) -> Optional[str]:
        """
        Gerar áudio via Voice Service se disponível
        Otimizado para VoiceMode quando is_voice_mode=True
        """
        try:
            # ✅ NOVO: Timeout otimizado para VoiceMode (conversação fluida)
            timeout_seconds = 15.0 if is_voice_mode else 30.0
            
            if is_voice_mode:
                logger.info(f"🎤 Gerando áudio para VoiceMode - Timeout otimizado: {timeout_seconds}s")
            
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                # Usar endpoint do Voice Service via Gateway
                response = await client.post(
                    f"http://localhost:8000/api/voice/speak",
                    json={
                        "text": text,
                        "voice_name": voice,
                        "speaking_rate": 1.1 if is_voice_mode else 1.0
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("audio_url"):
                        logger.info(f"🔊 Áudio gerado: {data['audio_url']} {'(VoiceMode)' if is_voice_mode else ''}")
                        return data["audio_url"]
                
        except Exception as e:
            error_msg = f"⚠️ Falha ao gerar áudio{'(VoiceMode)' if is_voice_mode else ''}: {e}"
            logger.warning(error_msg)
        
        return None

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
        try:
            messages = get_collection("messages")
            identity = await self.resolve_conversation_ref(session_id)
            chat_id = identity.get("chat_id")
            session_id = identity.get("legacy_session_id") or session_id
            
            # 🔒 CORREÇÃO CRÍTICA: Extrair username para validação adicional
            username = identity.get("username") or self._extract_username_from_session_id(session_id)
            
            # Construir query com dupla validação
            if chat_id:
                query = {"$or": [{"chat_id": chat_id}, {"session_id": session_id}]}
            else:
                query = {"session_id": session_id}
            if username:
                # 🔒 Adicionar filtro por username para segurança adicional
                query["username"] = username
                logger.info(f"🔍 Buscando mensagens com validação dupla - session_id: {session_id}, username: {username}")
            else:
                logger.warning(f"⚠️ Buscando mensagens apenas por session_id (legado): {session_id}")
            
            # Buscar mensagens da sessão com validação de usuário
            cursor = messages.find(
                query,
                sort=[("created_at", 1)]
            )
            
            context = []
            async for msg in cursor:
                # Converter para formato esperado pelo AI Service
                context.append({
                    "type": msg["type"],
                    "content": msg["content"]
                })
            
            logger.info(f"🔍 Contexto da conversa {session_id}: {len(context)} mensagens (username: {username})")
            return context
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter contexto da conversa: {e}")
            return []
    
    async def _get_session_initial_prompt(self, session_id: str) -> Optional[str]:
        """Buscar o initial_prompt da sessão terapêutica do usuário"""
        try:
            identity = await self.resolve_conversation_ref(session_id)
            # 🔒 Extrair username do session_id para buscar na coleção correta
            username = identity.get("username")
            original_session_id = identity.get("therapeutic_session_id") or session_id
            
            if not username and "_" in session_id:
                try:
                    # Formato: "teste_01_session-1" -> username="teste_01", original="session-1"
                    # Precisamos encontrar o último "_" e dividir por aí
                    last_underscore_index = session_id.rfind("_")
                    if last_underscore_index != -1:
                        username = session_id[:last_underscore_index]  # "teste_01"
                        original_session_id = session_id[last_underscore_index + 1:]  # "session-1"
                    else:
                        # Fallback se não encontrar underscore
                        username = session_id
                        original_session_id = session_id
                    
                    logger.info(f"🔍 Extraído - username: {username}, original_session_id: {original_session_id}")
                except Exception as ex:
                    logger.warning(f"⚠️ Erro ao extrair username do session_id: {session_id} - {ex}")
            
            # ✅ NOVO: Buscar APENAS na coleção user_therapeutic_sessions (personalizada por usuário)
            if username:
                user_sessions = get_collection("user_therapeutic_sessions")
                user_session = await user_sessions.find_one({
                    "username": username,
                    "session_id": original_session_id
                })
                
                if user_session and user_session.get("initial_prompt"):
                    logger.info(f"✅ Initial prompt encontrado na user_therapeutic_sessions para {username}:{original_session_id}")
                    return user_session["initial_prompt"]
                else:
                    logger.warning(f"⚠️ User session não encontrada: username={username}, session_id={original_session_id}")
            
            # ✅ REMOVIDO: Não buscar mais na coleção therapeutic_sessions (templates)
            # Agora tudo é personalizado por usuário
            
            logger.warning(f"⚠️ Nenhum initial_prompt encontrado para session_id: {session_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar initial_prompt para sessão {session_id}: {e}")
            return None
    
    async def _update_message_count(self, session_id: str):
        """Atualizar contador de mensagens da conversa"""
        try:
            conversations = get_collection("conversations")
            identity = await self.resolve_conversation_ref(session_id)
            if identity.get("chat_id"):
                query = {"chat_id": identity["chat_id"]}
            else:
                query = {"session_id": identity.get("legacy_session_id") or session_id}
            await conversations.update_one(
                query,
                {"$inc": {"message_count": 1}, "$set": {"updated_at": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar contador: {e}")

    # ===== SISTEMA DE CONTEXTO DE SESSÃO =====
    
    async def finalize_session_context(self, session_id: str, manual_termination: bool = False) -> Dict[str, Any]:
        """
        Finalizar sessão e gerar contexto/resumo da conversa
        """
        try:
            identity = await self.resolve_conversation_ref(session_id)
            session_id = identity.get("legacy_session_id") or session_id
            logger.info(f"🎯 FINALIZANDO CONTEXTO DA SESSÃO: {session_id}")
            
            # Verificar se a sessão existe
            conversation = await self.get_conversation_by_session_id(session_id)
            if not conversation:
                logger.warning(f"⚠️ Conversa não encontrada para contexto: {session_id}")
                return {"success": False, "error": "Conversa não encontrada"}
            
            # Verificar se já foi finalizada
            if conversation.get("session_context"):
                logger.info(f"✅ Sessão já possui contexto: {session_id}")
                next_session_result = await self._create_next_session_automatically(
                    session_id,
                    conversation["session_context"]
                )
                return {
                    "success": True, 
                    "already_finalized": True,
                    "context": conversation["session_context"],
                    "next_session": next_session_result
                }
            
            # Obter histórico completo da conversa
            history_data = await self.get_conversation_history(session_id)
            messages = history_data.get("history", [])
            
            # ✅ CORREÇÃO: Para session-1 (cadastro), aceitar qualquer quantidade de mensagens
            # pois pode ser finalizada antes de completar todo o questionário
            # A session-1 tem lógica especial: dados de cadastro em registration_data + contexto normal
            _, original_session_id = self._split_composite_session_id(session_id)
            is_registration_session = original_session_id == "session-1"
            
            min_messages_required = 1 if is_registration_session else 2
            
            if len(messages) < min_messages_required:
                logger.warning(f"⚠️ Conversa muito curta para gerar contexto: {session_id} ({len(messages)} mensagens)")
                return {"success": False, "error": "Conversa muito curta"}
            
            # Gerar contexto usando IA
            context_data = await self._generate_session_context(session_id, messages, manual_termination)
            
            # ✅ CORREÇÃO: Salvar contexto apenas na coleção session_contexts (eliminar duplicação)
            if context_data:
                session_contexts = get_collection("session_contexts")
                conversations = get_collection("conversations")
                
                # Verificar se o contexto já foi salvo na coleção session_contexts pelo SessionContextService
                context_doc = await session_contexts.find_one({"session_id": session_id})
                
                if not context_doc:
                    # Se não foi salvo pelo SessionContextService, salvar agora (fallback para análise básica)
                    logger.info(f"💾 Salvando contexto na coleção session_contexts (fallback): {session_id}")
                    
                    # Extrair username do session_id
                    username = self._extract_username_from_session_id(session_id)
                    
                    # Criar documento para session_contexts
                    context_document = {
                        "session_id": session_id,
                        "username": username,
                        "context": context_data,
                        "conversation_text": self._format_conversation_for_analysis(
                            (await self.get_conversation_history(session_id)).get("history", [])
                        ),
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "emotions_data": [],
                        "is_active": True,
                        "source": "gateway_fallback",
                        "version": 1
                    }
                    
                    # Salvar na coleção session_contexts
                    result = await session_contexts.insert_one(context_document)
                    context_doc = {"_id": result.inserted_id}
                    logger.info(f"✅ Contexto salvo na coleção session_contexts: {session_id}")
                
                # Salvar apenas referência na coleção conversations
                update_result = await conversations.update_one(
                    {"session_id": session_id},
                    {
                        "$set": {
                            "session_context_ref": context_doc["_id"],  # Referência ao documento
                            "context_generated_at": datetime.utcnow(),
                            "session_finalized": True,
                            "manual_termination": manual_termination,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                if update_result.modified_count > 0:
                    logger.info(f"✅ Contexto referenciado para sessão: {session_id}")
                    
                    # ✅ NOVO: Criar próxima sessão automaticamente
                    next_session_result = await self._create_next_session_automatically(session_id, context_data)
                    
                    return {
                        "success": True,
                        "context": context_data,
                        "manual_termination": manual_termination,
                        "next_session": next_session_result
                    }
                else:
                    logger.error(f"❌ Falha ao referenciar contexto: {session_id}")
                    return {"success": False, "error": "Falha ao referenciar contexto"}
            else:
                logger.error(f"❌ Falha ao gerar contexto: {session_id}")
                return {"success": False, "error": "Falha ao gerar contexto"}
                
        except Exception as e:
            logger.error(f"❌ Erro ao finalizar contexto da sessão {session_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _create_next_session_automatically(self, current_session_id: str, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Criar APENAS a próxima sessão automaticamente usando AI Service (1 a 1)
        """
        try:
            logger.info(f"🚀 CRIANDO PRÓXIMA SESSÃO AUTOMATICAMENTE para {current_session_id}")
            
            # Extrair username do session_id
            username = self._extract_username_from_session_id(current_session_id)
            if not username:
                logger.error(f"❌ Não foi possível extrair username de {current_session_id}")
                return {"success": False, "error": "Username não encontrado"}
            
            # Extrair número da sessão atual
            current_session_number = self._extract_session_number(current_session_id)
            next_session_number = current_session_number + 1
            next_session_id = f"session-{next_session_number}"
            
            logger.info(f"📋 Criando session-{next_session_number} após session-{current_session_number}")
            
            # Verificar se a próxima sessão já existe
            from .user_therapeutic_session_service import UserTherapeuticSessionService
            user_session_service = UserTherapeuticSessionService()
            
            existing_session = await user_session_service.get_user_session(username, next_session_id)
            if existing_session:
                logger.info(f"ℹ️ Session-{next_session_number} já existe para {username}")
                
                # Desbloquear se estiver bloqueada
                if existing_session.get("status") == "locked":
                    unlock_success = await user_session_service.unlock_session(username, next_session_id)
                    if unlock_success:
                        logger.info(f"🔓 Session-{next_session_number} desbloqueada para {username}")
                
                return {
                    "success": True,
                    "created": False,
                    "session_id": next_session_id,
                    "title": existing_session.get("title", f"Sessão {next_session_number}"),
                    "message": "Sessão já existe e foi desbloqueada"
                }
            
            # Buscar perfil do usuário
            user_profile = await self._get_user_profile(username)
            
            # Gerar próxima sessão usando AI Service
            next_session = await self._call_ai_service_for_next_session(user_profile, session_context, current_session_id)
            
            if next_session:
                # Garantir que o session_id seja sequencial
                next_session["session_id"] = next_session_id
                
                # Criar sessão no banco
                creation_result = await self._create_user_session_in_db(username, next_session)
                
                if creation_result:
                    logger.info(f"✅ Session-{next_session_number} criada automaticamente para {username}")
                    return {
                        "success": True,
                        "created": True,
                        "session_id": next_session_id,
                        "title": next_session.get("title", f"Sessão {next_session_number}"),
                        "generation_method": next_session.get("generation_method", "ai_service")
                    }
                else:
                    logger.error(f"❌ Falha ao criar session-{next_session_number} no banco")
                    return {"success": False, "error": "Falha ao criar sessão no banco"}
            else:
                logger.warning(f"⚠️ Falha ao gerar session-{next_session_number} via AI Service")
                return {"success": False, "error": "Falha ao gerar próxima sessão"}
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar próxima sessão automaticamente: {e}")
            return {"success": False, "error": str(e)}

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

    async def _get_user_profile(self, username: str) -> Dict[str, Any]:
        """
        Buscar perfil completo do usuário incluindo dados de registration_data da sessão-1
        """
        try:
            users = get_collection("users")
            conversations = get_collection("conversations")
            
            # 1. Buscar dados estruturados do usuário (se existir)
            user = await users.find_one({"username": username})
            user_profile = {}
            preferences = (user or {}).get("preferences", {})
            display_name = (
                (user or {}).get("display_name")
                or preferences.get("display_name")
                or (user or {}).get("full_name")
                or preferences.get("full_name")
            )
            
            if user and user.get("user_profile"):
                user_profile = user["user_profile"]
                logger.info(f"✅ Perfil estruturado encontrado para {username}")

            user_profile["username"] = username
            user_profile["preferences"] = preferences
            if display_name:
                user_profile["display_name"] = display_name
                user_profile["full_name"] = (user or {}).get("full_name") or preferences.get("full_name") or display_name
            
            # 2. ✅ NOVO: Buscar registration_data da sessão-1 para integrar ao perfil
            session_1_id = f"{username}_session-1"
            session_1_data = await conversations.find_one({"session_id": session_1_id})
            
            if session_1_data and session_1_data.get("registration_data"):
                registration_data = session_1_data["registration_data"]
                logger.info(f"✅ Registration data da sessão-1 encontrado para {username}")
                
                # Integrar registration_data ao user_profile
                user_profile["registration_data"] = registration_data
                
                # ✅ NOVO: Criar summary baseado no registration_data se não existir
                if not user_profile.get("profile_summary"):
                    summary_parts = []
                    if registration_data.get("idade"):
                        summary_parts.append(f"{registration_data['idade']} anos")
                    if registration_data.get("ocupacao"):
                        if "engenheiro de dados" in registration_data["ocupacao"].lower():
                            summary_parts.append("engenheiro de dados")
                        elif "professor" in registration_data["ocupacao"].lower():
                            summary_parts.append("professor")
                    if registration_data.get("localizacao"):
                        summary_parts.append(f"de {registration_data['localizacao']}")
                    
                    if summary_parts:
                        user_profile["profile_summary"] = f"Usuário {username}: {', '.join(summary_parts)}"
                
                return user_profile
            
            # 3. Fallback: retornar perfil básico ou vazio
            if user_profile:
                logger.info(f"✅ Perfil parcial encontrado para {username}")
                return user_profile
            else:
                logger.warning(f"⚠️ Nenhum dado de perfil encontrado para {username}")
                return {
                    "username": username,
                    "display_name": display_name,
                    "full_name": (user or {}).get("full_name") or preferences.get("full_name") or display_name,
                    "preferences": preferences,
                    "profile_summary": f"Usuário {username} - dados limitados",
                    "registration_data": {},
                    "personal_info": {},
                    "therapeutic_info": {}
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar perfil do usuário {username}: {e}")
            return {
                "username": username,
                "profile_summary": f"Usuário {username} - erro ao carregar dados",
                "error": str(e)
            }

    async def _call_ai_service_for_next_session(self, user_profile: Dict[str, Any], session_context: Dict[str, Any], current_session_id: str) -> Optional[Dict[str, Any]]:
        """
        Chamar AI Service para gerar próxima sessão
        """
        try:
            # TODO: Implementar chamada HTTP real quando httpx estiver disponível
            logger.info(f"🤖 Chamando AI Service para próxima sessão de {current_session_id}")
            
            # Simular resposta do AI Service por enquanto
            # Em produção, fazer chamada HTTP para: POST /generate-next-session
            
            # Simular dados baseados no contexto
            session_number = self._extract_session_number(current_session_id)
            next_session_number = session_number + 1
            next_session_id = f"session-{next_session_number}"
            
            # ✅ MELHORADO: Usar dados específicos do usuário para personalização
            # Extrair username para personalização
            username = self._extract_username_from_session_id(current_session_id)
            
            # Extrair temas da sessão anterior
            main_themes = session_context.get("main_themes", ["desenvolvimento pessoal"])
            
            # Extrair dados do perfil do usuário se disponível
            user_objectives = []
            user_age_category = "adulto"
            user_motivation = ""
            
            if user_profile and user_profile.get("therapeutic_info"):
                therapeutic_info = user_profile["therapeutic_info"]
                user_objectives = therapeutic_info.get("objetivos_identificados", [])
                motivation_data = therapeutic_info.get("motivacao_terapia", {})
                if isinstance(motivation_data, dict):
                    user_motivation = motivation_data.get("content", "")
                
            if user_profile and user_profile.get("personal_info"):
                personal_info = user_profile["personal_info"]
                age_data = personal_info.get("idade", {})
                if isinstance(age_data, dict):
                    user_age_category = age_data.get("categoria", "adulto")
            
            # Combinar temas da sessão anterior com objetivos do usuário
            combined_themes = list(set(main_themes + user_objectives[:2]))
            
            # Gerar título e descrição personalizados
            if next_session_number == 2:
                session_title = f"Sessão {next_session_number}: Aprofundando nosso conhecimento"
                session_subtitle = "Construindo sobre nossa primeira conversa"
            else:
                session_title = f"Sessão {next_session_number}: Continuando sua jornada"
                session_subtitle = "Aprofundando temas importantes para você"
            
            # Gerar objetivo personalizado
            if combined_themes:
                objective = f"Explorar e aprofundar os temas: {', '.join(combined_themes[:2])}"
            else:
                objective = "Continuar o processo de autoconhecimento e desenvolvimento pessoal"
            
            # Gerar prompt inicial personalizado
            if main_themes and next_session_number == 2:
                initial_prompt = f"Olá! Como você está se sentindo desde nossa primeira conversa? Na nossa sessão anterior, conversamos sobre {', '.join(main_themes[:2])}. Gostaria de continuar explorando esses temas ou há algo específico que te trouxe aqui hoje?"
            elif main_themes:
                initial_prompt = f"Olá! Como você está se sentindo desde nossa última conversa? Vamos continuar explorando os temas que identificamos: {', '.join(main_themes[:2])}?"
            else:
                initial_prompt = f"Olá! Como você está se sentindo hoje? O que gostaria de explorar em nossa sessão {next_session_number}?"
            
            # Criar sessão personalizada baseada no contexto e perfil do usuário
            next_session = {
                "session_id": next_session_id,
                "title": session_title,
                "subtitle": session_subtitle,
                "objective": objective,
                "initial_prompt": initial_prompt,
                "focus_areas": combined_themes[:3] if combined_themes else ["autoconhecimento", "bem-estar", "crescimento pessoal"],
                "therapeutic_approach": "Abordagem centrada na pessoa (Carl Rogers)",
                "expected_outcomes": [
                    "Maior clareza sobre os temas identificados",
                    "Desenvolvimento de insights pessoais",
                    "Fortalecimento do processo terapêutico"
                ],
                "session_type": "continuação",
                "estimated_duration": "45-60 minutos",
                "preparation_notes": "Revisar contexto da sessão anterior e temas identificados",
                "connection_to_previous": "Continuação dos temas e insights da sessão anterior",
                "personalization_factors": ["histórico do usuário", "temas identificados", "progresso terapêutico"],
                "generated_at": datetime.utcnow().isoformat(),
                "based_on_session": current_session_id,
                "generation_method": "simulated_ai_service",
                "personalized": True,
                "is_active": True
            }
            
            # ✅ CORREÇÃO: Retornar diretamente o objeto da sessão
            return next_session
            
        except Exception as e:
            logger.error(f"❌ Erro ao chamar AI Service para próxima sessão: {e}")
            return None

    def _extract_session_number(self, session_id: str) -> int:
        """
        Extrair número da sessão do session_id
        """
        try:
            import re
            match = re.search(r'session-(\d+)', session_id)
            if match:
                return int(match.group(1))
            else:
                return 1  # Padrão para sessão 1
        except Exception:
            return 1

    async def _create_user_session_in_db(self, username: str, session_data: Dict[str, Any]) -> bool:
        """
        Criar sessão do usuário no banco de dados
        """
        try:
            # Extrair session_id com validação
            session_id = session_data.get("session_id")
            if not session_id:
                logger.error("❌ session_id não encontrado nos dados da sessão")
                return False
            
            # Criar entrada na coleção user_therapeutic_sessions
            user_sessions = get_collection("user_therapeutic_sessions")
            
            session_document = {
                "username": username,
                "session_id": session_id,
                "title": session_data.get("title", "Sessão Terapêutica"),
                "subtitle": session_data.get("subtitle", ""),
                "objective": session_data.get("objective", ""),
                "initial_prompt": session_data.get("initial_prompt", ""),
                "focus_areas": session_data.get("focus_areas", []),
                "therapeutic_approach": session_data.get("therapeutic_approach", ""),
                "expected_outcomes": session_data.get("expected_outcomes", []),
                "session_type": session_data.get("session_type", "individual"),
                "estimated_duration": session_data.get("estimated_duration", "45-60 minutos"),
                "preparation_notes": session_data.get("preparation_notes", ""),
                "connection_to_previous": session_data.get("connection_to_previous", ""),
                "personalization_factors": session_data.get("personalization_factors", []),
                "generated_at": session_data.get("generated_at"),
                "based_on_session": session_data.get("based_on_session"),
                "generation_method": session_data.get("generation_method", "ai_service"),
                "personalized": session_data.get("personalized", True),
                "is_active": session_data.get("is_active", True),
                "status": "unlocked",
                "progress": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Inserir documento
            result = await user_sessions.insert_one(session_document)
            
            if result.inserted_id:
                logger.info(f"✅ Sessão criada e desbloqueada no banco: {session_id} para {username}")
                return True
            else:
                logger.error(f"❌ Falha ao inserir sessão no banco: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar sessão no banco: {e}")
            return False
    
    async def _generate_session_context(self, session_id: str, messages: List[Dict[str, Any]], manual_termination: bool = False) -> Optional[Dict[str, Any]]:
        """
        Gerar contexto da sessão usando IA para resumir a conversa
        """
        try:
            logger.info(f"🤖 Gerando contexto com IA para sessão: {session_id}")
            
            # Preparar conversa para análise
            conversation_text = self._format_conversation_for_analysis(messages)
            
            # Criar prompt específico para gerar contexto
            context_prompt = self._create_context_generation_prompt(session_id, conversation_text, manual_termination)
            
            # Fazer chamada para SessionContextService
            ai_response = await self._call_ai_service_for_context(context_prompt, session_id)
            
            if ai_response and ai_response.get("success"):
                # Usar contexto estruturado do SessionContextService
                context_data = ai_response.get("context_data", {})
                
                # Adicionar metadados
                context_data.update({
                    "session_id": session_id,
                    "total_messages": len(messages),
                    "generated_at": datetime.utcnow().isoformat(),
                    "generation_method": "session_context_service",
                    "manual_termination": manual_termination,
                    "conversation_duration_estimate": self._estimate_conversation_duration(messages)
                })
                
                logger.info(f"✅ Contexto gerado com sucesso pelo SessionContextService para sessão: {session_id}")
                return context_data
            else:
                logger.warning(f"⚠️ SessionContextService não disponível, usando análise básica para sessão: {session_id}")
                return await self._generate_basic_context(session_id, messages, manual_termination)
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar contexto: {e}")
            return await self._generate_basic_context(session_id, messages, manual_termination)
    
    def _format_conversation_for_analysis(self, messages: List[Dict[str, Any]]) -> str:
        """
        Formatar conversa para análise pela IA
        """
        conversation_lines = []
        
        for i, msg in enumerate(messages):
            role = "Usuário" if msg["type"] == "user" else "Terapeuta"
            content = msg["content"]
            conversation_lines.append(f"{role}: {content}")
        
        return "\n\n".join(conversation_lines)
    
    def _create_context_generation_prompt(self, session_id: str, conversation_text: str, manual_termination: bool = False) -> str:
        """
        Criar prompt específico para gerar contexto da sessão
        """
        termination_context = "manualmente pelo usuário" if manual_termination else "automaticamente (palavras de despedida detectadas)"
        
        prompt = f"""
ANÁLISE DE SESSÃO TERAPÊUTICA

Você é um assistente especializado em análise de sessões terapêuticas. Analise a conversa abaixo e gere um contexto/resumo estruturado.

SESSÃO ID: {session_id}
TÉRMINO: {termination_context}

CONVERSA:
{conversation_text}

INSTRUÇÕES:
1. Analise a conversa completa do ponto de vista terapêutico
2. Identifique os temas principais abordados
3. Extraia insights sobre o estado emocional do usuário
4. Identifique padrões de comportamento ou pensamento
5. Destaque momentos importantes da conversa
6. Sugira pontos para futuras sessões

RESPONDA EM FORMATO JSON com as seguintes chaves:
{{
  "summary": "Resumo geral da sessão em 2-3 frases",
  "main_themes": ["tema1", "tema2", "tema3"],
  "emotional_state": {{
    "initial": "Estado emocional inicial",
    "final": "Estado emocional final",
    "progression": "Como evoluiu durante a sessão"
  }},
  "key_insights": ["insight1", "insight2", "insight3"],
  "important_moments": [
    {{
      "moment": "Descrição do momento",
      "significance": "Por que foi importante"
    }}
  ],
  "user_progress": {{
    "strengths_shown": ["força1", "força2"],
    "challenges_identified": ["desafio1", "desafio2"],
    "growth_areas": ["área1", "área2"]
  }},
  "therapeutic_notes": {{
    "techniques_used": ["técnica1", "técnica2"],
    "user_response": "Como o usuário respondeu à terapia",
    "engagement_level": "Alto/Médio/Baixo"
  }},
  "future_sessions": {{
    "suggested_topics": ["tópico1", "tópico2"],
    "areas_to_explore": ["área1", "área2"],
    "therapeutic_goals": ["objetivo1", "objetivo2"]
  }}
}}

RESPONDA APENAS COM O JSON, SEM TEXTO ADICIONAL.
"""
        return prompt
    
    async def _call_ai_service_for_context(self, prompt: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Chamar AI Service para gerar contexto da sessão usando o SessionContextService
        """
        try:
            logger.info(f"🤖 Chamando SessionContextService para gerar contexto da sessão: {session_id}")
            
            # Obter histórico da conversa para enviar ao SessionContextService
            history_data = await self.get_conversation_history(session_id)
            messages = history_data.get("history", [])
            
            # Converter mensagens para texto de conversa
            conversation_text = self._format_conversation_for_analysis(messages)
            
            # Extrair username do session_id
            username = self._extract_username_from_session_id(session_id)
            
            # Preparar dados para o SessionContextService
            ai_request = {
                "session_id": session_id,
                "username": username,
                "conversation_text": conversation_text,
                "emotions_data": [],  # Poderá ser usado no futuro
                "manual_termination": True,  # Como é chamado manualmente
                "additional_context": {
                    "analysis_prompt": prompt,
                    "total_messages": len(messages)
                }
            }
            
            # Chamar o endpoint correto do SessionContextService
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ai_service_url}/openai/generate-session-context",
                    json=ai_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    ai_data = response.json()
                    
                    # Verificar se foi bem-sucedido
                    if ai_data.get("success"):
                        context_data = ai_data.get("context", {})
                        logger.info(f"✅ Contexto gerado pelo SessionContextService para {session_id}")
                        
                        return {
                            "success": True,
                            "context_data": context_data
                        }
                    else:
                        logger.error(f"❌ SessionContextService retornou erro: {ai_data.get('error', 'Erro desconhecido')}")
                        return None
                else:
                    logger.error(f"❌ SessionContextService retornou erro {response.status_code}: {response.text}")
                    return None
                    
        except httpx.ConnectError:
            logger.warning(f"⚠️ SessionContextService não disponível, usando análise básica para {session_id}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao chamar SessionContextService para contexto: {e}")
            return None
    
    def _parse_ai_context_response(self, ai_response: str) -> Dict[str, Any]:
        """
        Parsear resposta da IA e extrair contexto estruturado
        """
        try:
            import json
            
            # Limpar possíveis caracteres extras
            clean_response = ai_response.strip()
            
            # Tentar extrair JSON se houver texto extra
            start_idx = clean_response.find('{')
            end_idx = clean_response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = clean_response[start_idx:end_idx]
                context_data = json.loads(json_str)
                
                logger.info(f"✅ Contexto parseado com sucesso da IA")
                return context_data
            else:
                logger.warning(f"⚠️ Não foi possível extrair JSON da resposta da IA")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao parsear JSON da IA: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Erro ao processar resposta da IA: {e}")
            return {}
    
    async def _generate_basic_context(self, session_id: str, messages: List[Dict[str, Any]], manual_termination: bool = False) -> Dict[str, Any]:
        """
        Gerar contexto básico analisando o conteúdo real da conversa
        """
        try:
            logger.info(f"📄 Gerando contexto básico para sessão: {session_id}")
            
            user_messages = [msg for msg in messages if msg["type"] == "user"]
            ai_messages = [msg for msg in messages if msg["type"] == "ai"]
            
            # ✅ NOVO: Verificar se é sessão de cadastro para análise específica
            _, original_session_id = self._split_composite_session_id(session_id)
            is_registration_session = original_session_id == "session-1"
            
            if is_registration_session:
                logger.info(f"🔍 ANÁLISE DE CADASTRO: Gerando contexto para session-1")
                return await self._generate_registration_context(session_id, user_messages, ai_messages, manual_termination)
            else:
                logger.info(f"🔍 ANÁLISE NORMAL: Gerando contexto para {original_session_id}")
                return self._generate_regular_context(session_id, user_messages, ai_messages, manual_termination)
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar contexto básico: {e}")
            return {
                "summary": "Sessão terapêutica realizada",
                "main_themes": ["conversa terapêutica"],
                "generation_method": "minimal_fallback",
                "error": str(e)
            }

    async def _generate_registration_context(self, session_id: str, user_messages: List[Dict[str, Any]], ai_messages: List[Dict[str, Any]], manual_termination: bool = False) -> Dict[str, Any]:
        """
        Gerar contexto específico para sessão de cadastro (session-1) usando AI Service
        """
        try:
            logger.info(f"📋 ANÁLISE CADASTRO: Processando {len(user_messages)} respostas do usuário")
            
            # Formatar mensagens para o AI Service
            conversation_text = self._format_conversation_for_analysis(user_messages + ai_messages)
            
            # Criar prompt específico para session-1 (cadastro)
            context_prompt = f"""
ANÁLISE DE SESSÃO DE CADASTRO TERAPÊUTICO

Analise a conversa de cadastro abaixo e gere um contexto estruturado. Esta é uma sessão de coleta de dados pessoais para personalizar o atendimento terapêutico.

SESSÃO: {session_id}
TIPO: Cadastro inicial (session-1)
RESPOSTAS DO USUÁRIO: {len(user_messages)} respostas

CONVERSA:
{conversation_text}

INSTRUÇÕES:
1. Analise as respostas do usuário às perguntas de cadastro
2. Identifique os temas principais mencionados pelo usuário
3. Extraia insights sobre motivação, objetivos e situação pessoal
4. Identifique áreas de interesse para futuras sessões
5. Gere sugestões para próximas sessões baseadas no perfil

RESPONDA EM FORMATO JSON com as seguintes chaves:
{{
  "summary": "Resumo do processo de cadastro e perfil do usuário",
  "main_themes": ["tema1", "tema2", "tema3"],
  "emotional_state": {{
    "initial": "Estado emocional no início do cadastro",
    "final": "Estado emocional ao final do cadastro",
    "progression": "Como evoluiu durante o cadastro"
  }},
  "key_insights": ["insight1", "insight2", "insight3"],
  "important_moments": [
    {{
      "moment": "Descrição do momento importante",
      "significance": "Por que foi importante"
    }}
  ],
  "user_progress": {{
    "strengths_shown": ["força1", "força2"],
    "challenges_identified": ["desafio1", "desafio2"],
    "growth_areas": ["área1", "área2"]
  }},
  "therapeutic_notes": {{
    "techniques_used": ["técnica1", "técnica2"],
    "user_response": "Como o usuário respondeu",
    "engagement_level": "Alto/Médio/Baixo"
  }},
  "future_sessions": {{
    "suggested_topics": ["tópico1", "tópico2"],
    "areas_to_explore": ["área1", "área2"],
    "therapeutic_goals": ["objetivo1", "objetivo2"]
  }}
}}

RESPONDA APENAS COM O JSON, SEM TEXTO ADICIONAL.
"""
            
            # Tentar usar SessionContextService primeiro
            ai_response = await self._call_ai_service_for_context(context_prompt, session_id)
            
            if ai_response and ai_response.get("success"):
                # Usar contexto estruturado do SessionContextService
                context_data = ai_response.get("context_data", {})
                
                if context_data:
                    # Adicionar metadados específicos do cadastro
                    context_data.update({
                        "session_id": session_id,
                        "session_type": "registration",
                        "total_messages": len(user_messages + ai_messages),
                        "user_responses": len(user_messages),
                        "generated_at": datetime.utcnow().isoformat(),
                        "generation_method": "session_context_service_registration",
                        "manual_termination": manual_termination
                    })
                    
                    logger.info(f"✅ Contexto de cadastro gerado via SessionContextService para {session_id}")
                    return context_data
            
            # Fallback para análise básica
            logger.warning(f"⚠️ SessionContextService não disponível, usando análise básica para cadastro {session_id}")
            return self._generate_fallback_registration_context(session_id, user_messages, ai_messages)
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar contexto de cadastro: {e}")
            return self._generate_fallback_registration_context(session_id, user_messages, ai_messages)

    def _generate_regular_context(self, session_id: str, user_messages: List[Dict[str, Any]], ai_messages: List[Dict[str, Any]], manual_termination: bool = False) -> Dict[str, Any]:
        """
        Gerar contexto para sessões regulares (não de cadastro)
        """
        # Análise básica de sentimentos
        emotion_analysis = self._analyze_basic_emotions(user_messages)
        
        # Identificar temas básicos
        themes = self._identify_basic_themes(user_messages)
        
        return {
            "summary": f"Sessão com {len(user_messages + ai_messages)} mensagens trocadas. Usuário demonstrou engajamento no processo terapêutico.",
            "main_themes": themes,
            "emotional_state": {
                "initial": "Disponível para o diálogo",
                "final": emotion_analysis.get("dominant_emotion", "neutro"),
                "progression": "Processo terapêutico em andamento"
            },
            "key_insights": [
                f"Conversa envolveu {len(user_messages)} mensagens do usuário",
                f"Duração estimada: {self._estimate_conversation_duration(user_messages + ai_messages)} minutos",
                "Engajamento demonstrado pelo usuário"
            ],
            "important_moments": [
                {
                    "moment": "Início da conversa terapêutica",
                    "significance": "Estabelecimento do vínculo terapêutico"
                }
            ],
            "user_progress": {
                "strengths_shown": ["participação ativa", "abertura ao diálogo"],
                "challenges_identified": ["necessidade de continuidade"],
                "growth_areas": themes[:3] if themes else ["autoconhecimento", "expressão emocional"]
            },
            "therapeutic_notes": {
                "techniques_used": ["escuta ativa", "abordagem rogeriana"],
                "user_response": "Engajado",
                "engagement_level": "Médio"
            },
            "future_sessions": {
                "suggested_topics": themes[:2] if themes else ["continuidade do processo terapêutico"],
                "areas_to_explore": ["aprofundamento emocional"],
                "therapeutic_goals": ["manutenção do vínculo terapêutico"]
            },
            "generation_method": "basic_analysis"
        }
    
    def _analyze_basic_emotions(self, user_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Análise básica de emoções baseada em palavras-chave
        """
        emotion_keywords = {
            "tristeza": ["triste", "deprimido", "mal", "péssimo", "horrível", "chateado"],
            "ansiedade": ["ansioso", "preocupado", "nervoso", "estressado", "medo"],
            "raiva": ["irritado", "bravo", "furioso", "raiva", "odio"],
            "alegria": ["feliz", "contente", "bem", "ótimo", "bom", "alegre"],
            "gratidão": ["obrigado", "obrigada", "grato", "agradecido"]
        }
        
        emotion_scores = {emotion: 0 for emotion in emotion_keywords}
        total_words = 0
        
        for msg in user_messages:
            content = msg["content"].lower()
            words = content.split()
            total_words += len(words)
            
            for emotion, keywords in emotion_keywords.items():
                for keyword in keywords:
                    if keyword in content:
                        emotion_scores[emotion] += 1
        
        # Encontrar emoção dominante
        if any(emotion_scores.values()):
            dominant_emotion = max(emotion_scores.keys(), key=lambda x: emotion_scores[x])
        else:
            dominant_emotion = "neutro"
        
        return {
            "dominant_emotion": dominant_emotion,
            "emotion_scores": emotion_scores,
            "total_words": total_words
        }
    
    def _identify_basic_themes(self, user_messages: List[Dict[str, Any]]) -> List[str]:
        """
        Identificar temas básicos da conversa
        """
        theme_keywords = {
            "trabalho": ["trabalho", "emprego", "carreira", "profissão", "chefe", "colega"],
            "família": ["família", "pai", "mãe", "irmão", "irmã", "filho", "filha", "marido", "esposa"],
            "relacionamentos": ["namorado", "namorada", "amigo", "amiga", "relacionamento", "amor"],
            "saúde": ["saúde", "médico", "hospital", "doença", "dor", "sintoma"],
            "estudos": ["escola", "faculdade", "universidade", "estudo", "prova", "curso"],
            "autoestima": ["autoestima", "confiança", "insegurança", "valor", "autoconceito"],
            "futuro": ["futuro", "planos", "objetivos", "metas", "sonhos", "ambição"]
        }
        
        identified_themes = []
        
        for msg in user_messages:
            content = msg["content"].lower()
            
            for theme, keywords in theme_keywords.items():
                if any(keyword in content for keyword in keywords):
                    if theme not in identified_themes:
                        identified_themes.append(theme)
        
        return identified_themes[:5]  # Máximo 5 temas
    
    def _generate_fallback_registration_context(self, session_id: str, user_messages: List[Dict[str, Any]], ai_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gerar contexto fallback para sessão de cadastro quando AI Service não está disponível
        """
        try:
            logger.info(f"📄 Gerando contexto fallback para cadastro: {session_id}")
            
            # Análise simples das respostas do usuário
            all_user_text = " ".join([msg["content"] for msg in user_messages]).lower()
            
            # Identificar temas básicos baseados em palavras-chave
            themes = []
            theme_keywords = {
                "trabalho": ["trabalho", "emprego", "carreira", "profissão"],
                "família": ["família", "pai", "mãe", "irmão", "filhos"],
                "relacionamentos": ["relacionamento", "namorado", "casado", "solteiro"],
                "saúde": ["saúde", "ansiedade", "depressão", "stress"],
                "estudos": ["estudo", "faculdade", "escola", "formação"],
                "autoestima": ["autoestima", "confiança", "insegurança"],
                "desenvolvimento": ["crescimento", "desenvolvimento", "mudança"]
            }
            
            for theme, keywords in theme_keywords.items():
                if any(keyword in all_user_text for keyword in keywords):
                    themes.append(theme)
            
            if not themes:
                themes = ["desenvolvimento pessoal", "autoconhecimento"]
            
            return {
                "summary": f"Cadastro realizado com {len(user_messages)} respostas do usuário. Processo de conhecimento inicial concluído.",
                "main_themes": themes[:3],
                "emotional_state": {
                    "initial": "Receptivo ao processo de cadastro",
                    "final": "Engajado e colaborativo",
                    "progression": "Abertura progressiva durante o cadastro"
                },
                "key_insights": [
                    f"Usuário forneceu {len(user_messages)} respostas ao questionário",
                    "Demonstrou disposição para compartilhar informações pessoais",
                    "Processo de cadastro concluído com sucesso"
                ],
                "important_moments": [
                    {
                        "moment": "Início do processo de cadastro",
                        "significance": "Primeiro contato com o sistema terapêutico"
                    },
                    {
                        "moment": "Finalização do cadastro",
                        "significance": "Conclusão do processo de conhecimento inicial"
                    }
                ],
                "user_progress": {
                    "strengths_shown": ["abertura", "colaboração", "disposição para mudança"],
                    "challenges_identified": ["necessidade de apoio terapêutico"],
                    "growth_areas": themes[:3] if themes else ["desenvolvimento pessoal"]
                },
                "therapeutic_notes": {
                    "techniques_used": ["coleta de dados estruturada", "questionário guiado"],
                    "user_response": "Colaborativo e aberto",
                    "engagement_level": "Alto"
                },
                "future_sessions": {
                    "suggested_topics": themes[:3] if themes else ["autoconhecimento"],
                    "areas_to_explore": ["questões pessoais identificadas"],
                    "therapeutic_goals": ["bem-estar geral", "desenvolvimento pessoal"]
                },
                "session_id": session_id,
                "session_type": "registration",
                "total_messages": len(user_messages + ai_messages),
                "user_responses": len(user_messages),
                "generated_at": datetime.utcnow().isoformat(),
                "generation_method": "fallback_registration",
                "manual_termination": False
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar contexto fallback de cadastro: {e}")
            return {
                "summary": "Sessão de cadastro realizada",
                "main_themes": ["cadastro", "autoconhecimento"],
                "session_type": "registration",
                "generation_method": "minimal_fallback",
                "error": str(e)
            }
    
    def _estimate_conversation_duration(self, messages: List[Dict[str, Any]]) -> int:
        """
        Estimar duração da conversa em minutos
        """
        if len(messages) < 2:
            return 1
        
        try:
            first_message = messages[0]
            last_message = messages[-1]
            
            start_time = first_message.get("created_at")
            end_time = last_message.get("created_at")
            
            if start_time and end_time:
                duration = end_time - start_time
                return max(1, int(duration.total_seconds() / 60))
            else:
                # Estimar baseado no número de mensagens (2 minutos por intercâmbio)
                return max(1, len(messages) // 2 * 2)
                
        except Exception as e:
            logger.error(f"❌ Erro ao calcular duração: {e}")
            return len(messages)  # Fallback simples
    
    def detect_conversation_end(self, message: str) -> bool:
        """
        Detectar se a mensagem indica fim de conversa
        """
        message_lower = message.lower().strip()
        
        # Palavras/frases que indicam despedida
        farewell_patterns = [
            "tchau", "adeus", "até logo", "até mais", "até breve",
            "bye", "goodbye", "see you", "até a próxima",
            "obrigado pela conversa", "obrigada pela conversa",
            "foi bom conversar", "preciso ir", "tenho que ir",
            "vou desligar", "vou sair", "até outra hora",
            "muito obrigado", "muito obrigada", "valeu pela ajuda",
            "foi ótimo", "me ajudou muito", "estou melhor agora"
        ]
        
        # Verificar padrões de despedida
        for pattern in farewell_patterns:
            if pattern in message_lower:
                return True
        
        # Verificar padrões de finalização
        finalization_patterns = [
            "acabou", "terminou", "é isso", "só isso mesmo",
            "não tenho mais nada", "acho que é só",
            "por hoje é só", "é tudo por hoje"
        ]
        
        for pattern in finalization_patterns:
            if pattern in message_lower:
                return True
        
        return False
    
    async def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obter contexto salvo de uma sessão - busca na coleção session_contexts
        """
        try:
            identity = await self.resolve_conversation_ref(session_id)
            session_id = identity.get("legacy_session_id") or session_id
            # ✅ CORREÇÃO: Buscar contexto na coleção session_contexts para eliminar duplicação
            session_contexts = get_collection("session_contexts")
            context_doc = await session_contexts.find_one({"session_id": session_id})
            
            if context_doc:
                logger.info(f"✅ Contexto encontrado na coleção session_contexts: {session_id}")
                return context_doc.get("context", {})
            else:
                # ✅ FALLBACK: Para sessões antigas que ainda têm contexto na coleção conversations
                logger.warning(f"⚠️ Contexto não encontrado em session_contexts, tentando fallback para {session_id}")
                conversation = await self.get_conversation_by_session_id(session_id)
                
                if conversation and conversation.get("session_context"):
                    logger.info(f"✅ Contexto encontrado via fallback em conversations: {session_id}")
                    return conversation["session_context"]
                else:
                    logger.warning(f"⚠️ Contexto não encontrado para sessão: {session_id}")
                    return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter contexto da sessão {session_id}: {e}")
            return None
    
    async def list_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Listar conversas recentes
        """
        try:
            conversations = get_collection("conversations")
            
            cursor = conversations.find(
                {},
                sort=[("updated_at", -1)],
                limit=limit
            )
            
            result = []
            async for conv in cursor:
                result.append({
                    "chat_id": conv.get("chat_id"),
                    "session_id": conv["session_id"],
                    "therapeutic_session_id": conv.get("therapeutic_session_id"),
                    "username": conv.get("username"),
                    "created_at": conv["created_at"],
                    "updated_at": conv["updated_at"],
                    "message_count": conv.get("message_count", 0)
                })
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar conversas: {e}")
            raise

    async def get_conversation_by_session_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Busca uma conversa por chat_id novo ou session_id legado e retorna como dicionário."""
        try:
            identity = await self.resolve_conversation_ref(session_id)
            conversation = identity.get("conversation")
            
            if conversation:
                # ✅ CORREÇÃO: Retornar todos os campos da conversa, não apenas alguns selecionados
                # Converter ObjectId para string se necessário
                if "_id" in conversation:
                    conversation["_id"] = str(conversation["_id"])
                return conversation
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar conversa por session_id: {e}")
            raise

    # ✅ NOVO: Sistema de cadastro/onboarding para session-1
    async def _handle_registration_session(self, session_id: str, user_message: str, is_voice_mode: bool = False) -> Dict[str, Any]:
        """
        Gerenciar a sessão de cadastro (session-1) com perguntas próprias, sem OpenAI
        """
        try:
            logger.info(f"🔍 PROCESSANDO SESSÃO DE CADASTRO para {session_id}")
            if is_voice_mode:
                logger.info(f"🎤 VoiceMode ativo na sessão de cadastro")
            
            # Extrair username do session_id composto.
            username = self._extract_username_from_session_id(session_id) or 'usuario'
            
            # Buscar preferências do usuário para áudio
            users_collection = get_collection("users")
            user = await users_collection.find_one({"username": username})
            
            selected_voice = "pt-BR-Neural2-A"  # padrão
            if user and user.get("preferences"):
                selected_voice = user["preferences"].get("selected_voice", selected_voice)
            
            # Buscar dados existentes da conversa
            conversations = get_collection("conversations")
            conversation = await conversations.find_one({"session_id": session_id})
            
            # Inicializar dados de cadastro se não existir
            if not conversation:
                conversation = {
                    "session_id": session_id,
                    "username": username,
                    "started_at": datetime.now(),
                    "messages": [],
                    "registration_data": {},
                    "registration_step": 0,
                    "is_registration_complete": False
                }
                await conversations.insert_one(conversation)
            
            # Recuperar dados de cadastro
            registration_data = conversation.get("registration_data", {})
            current_step = conversation.get("registration_step", 0)
            
            # Definir perguntas de cadastro
            registration_questions = [
                {
                    "step": 0,
                    "question": f"Olá! Eu sou seu assistente terapêutico. É um prazer te conhecer! Para personalizar nossa conversa, vou fazer algumas perguntas sobre você. Primeiro, me conta: qual é a sua idade?",
                    "field": "idade",
                    "type": "number"
                },
                {
                    "step": 1,
                    "question": "Obrigado! Agora me conta: como você se identifica em relação ao seu gênero? (Por exemplo: feminino, masculino, não-binário, prefiro não responder, etc.)",
                    "field": "genero",
                    "type": "text"
                },
                {
                    "step": 2,
                    "question": "Perfeito! E como você se identifica em relação à sua cor/raça? (Por exemplo: branco, negro, pardo, indígena, asiático, prefiro não responder, etc.)",
                    "field": "cor_raca",
                    "type": "text"
                },
                {
                    "step": 3,
                    "question": "Obrigado por compartilhar! Agora me conta: em que cidade e estado você mora atualmente?",
                    "field": "localizacao",
                    "type": "text"
                },
                {
                    "step": 4,
                    "question": "Ótimo! Como é sua situação de moradia? Você mora sozinho(a), com família, amigos, companheiro(a)? Me conta um pouco sobre isso.",
                    "field": "situacao_moradia",
                    "type": "text"
                },
                {
                    "step": 5,
                    "question": "Entendi! E como você descreveria sua relação com sua família? Vocês são próximos, há conflitos, moram longe? Fique à vontade para compartilhar o que se sentir confortável.",
                    "field": "relacao_familia",
                    "type": "text"
                },
                {
                    "step": 6,
                    "question": "Obrigado por compartilhar! Agora me conta: qual é sua ocupação atual? Você trabalha, estuda, está desempregado(a)? Como é sua rotina?",
                    "field": "ocupacao",
                    "type": "text"
                },
                {
                    "step": 7,
                    "question": "Interessante! E o que te trouxe até aqui? O que você espera dessas nossas conversas? Há algo específico que gostaria de trabalhar ou simplesmente quer ter um espaço para se expressar?",
                    "field": "motivacao_terapia",
                    "type": "text"
                },
                {
                    "step": 8,
                    "question": "Muito obrigado por compartilhar todas essas informações comigo! Isso me ajuda muito a te conhecer melhor. Há mais alguma coisa sobre você que gostaria de me contar? Algo que considera importante para nossa conversa?",
                    "field": "informacoes_adicionais",
                    "type": "text"
                }
            ]
            
            # ✅ CORRIGIDO: A primeira mensagem já foi enviada via /api/chat/initial-message
            # Agora processar resposta do usuário (seja step 0 para idade ou steps subsequentes)
            
            # Processar resposta do usuário e fazer próxima pergunta
            if current_step >= 0 and current_step < len(registration_questions):
                # Salvar resposta do usuário
                user_message_id = await self._save_message(session_id, "user", user_message)
                
                # ✅ CORRIGIDO: Armazenar a resposta no campo correspondente
                if current_step < len(registration_questions):
                    field = registration_questions[current_step]["field"]
                    registration_data[field] = user_message.strip()
                    
                    # Atualizar dados no banco
                    await conversations.update_one(
                        {"session_id": session_id},
                        {"$set": {"registration_data": registration_data}}
                    )
                    
                    logger.info(f"📝 CADASTRO: Campo '{field}' salvo para {username}")
                
                # Verificar se há próxima pergunta
                next_step_index = current_step + 1
                if next_step_index < len(registration_questions):
                    ai_response = registration_questions[next_step_index]["question"]
                    next_step = current_step + 1
                    logger.info(f"❓ CADASTRO: Pergunta {next_step_index + 1} para {username}")
                    
                    # Salvar resposta da IA para próxima pergunta
                    ai_message_id = await self._save_message(session_id, "ai", ai_response)
                    
                    # ✅ NOVO: Gerar áudio se VoiceMode estiver ativo
                    audio_url = await self._generate_audio_for_registration(ai_response, username, is_voice_mode)
                    
                    # Atualizar step
                    await conversations.update_one(
                        {"session_id": session_id},
                        {"$set": {"registration_step": next_step}}
                    )
                    
                    # Resposta normal para próxima pergunta
                    response_data = {
                        "success": True,
                        "data": {
                            "user_message": {
                                "id": user_message_id,
                                "content": user_message
                            },
                            "ai_response": {
                                "id": ai_message_id,
                                "content": ai_response,
                                "audioUrl": audio_url,  # ✅ NOVO: Incluir URL do áudio
                                "provider": "registration_system",
                                "model": "cadastro_v1"
                            }
                        }
                    }
                    
                    logger.info(f"📝 CADASTRO: Pergunta {next_step_index + 1} de {len(registration_questions)} para {username}")
                    return response_data
                
                else:
                    # ✅ FINALIZAR CADASTRO - Ordem correta das operações
                    logger.info(f"🎯 INICIANDO FINALIZAÇÃO DO CADASTRO para {username}")
                    
                    # 1. Preparar mensagem de finalização
                    ai_response = f"""Perfeito! Muito obrigado por compartilhar todas essas informações comigo, {username}! 

Agora eu te conheço melhor e posso oferecer um apoio mais personalizado. Suas informações estão seguras e serão usadas apenas para tornar nossas conversas mais significativas.

Seu cadastro foi finalizado com sucesso! 🎉

Você agora pode acessar as outras sessões terapêuticas na sua jornada de autoconhecimento. Cada sessão foi cuidadosamente desenvolvida para te apoiar em diferentes aspectos da sua vida."""
                    
                    # 2. Salvar resposta da IA PRIMEIRO
                    ai_message_id = await self._save_message(session_id, "ai", ai_response)
                    logger.info(f"✅ CADASTRO: Mensagem de finalização salva para {username}")
                    
                    # ✅ NOVO: Gerar áudio para finalização se VoiceMode estiver ativo
                    finalization_audio_url = await self._generate_audio_for_registration(ai_response, username, is_voice_mode)
                    
                    # 3. Marcar cadastro como completo
                    await conversations.update_one(
                        {"session_id": session_id},
                        {"$set": {
                            "is_registration_complete": True,
                            "registration_step": current_step + 1,
                            "completed_at": datetime.utcnow()
                        }}
                    )
                    logger.info(f"✅ CADASTRO: Marcado como completo para {username}")
                    
                    # 4. Criar perfil do usuário
                    await self._save_user_profile(username, registration_data)
                    logger.info(f"✅ CADASTRO: Perfil do usuário salvo para {username}")
                    
                    # 5. Marcar session-1 como completed
                    try:
                        from .user_therapeutic_session_service import UserTherapeuticSessionService
                        user_session_service = UserTherapeuticSessionService()
                        
                        completion_success = await user_session_service.complete_session(username, "session-1", 100, status="completed")
                        if completion_success:
                            logger.info(f"✅ CADASTRO: Session-1 marcada como COMPLETED para {username}")
                        else:
                            logger.warning(f"⚠️ CADASTRO: Falha ao marcar session-1 como completed para {username}")
                            
                    except Exception as session_error:
                        logger.error(f"❌ CADASTRO: Erro ao finalizar session-1: {session_error}")
                    
                    # 6. Finalizar contexto da sessão e criar próxima sessão automaticamente
                    finalize_success = False
                    try:
                        logger.info(f"🚀 CADASTRO: Finalizando contexto da session-1 para criar próxima sessão automaticamente")
                        finalize_result = await self.finalize_session_context(session_id, manual_termination=True)
                        
                        if finalize_result.get("success"):
                            finalize_success = True
                            next_session_info = finalize_result.get("next_session", {})
                            if next_session_info.get("success"):
                                logger.info(f"✅ CADASTRO: Próxima sessão criada automaticamente após session-1: {next_session_info.get('session_id')}")
                            else:
                                logger.warning(f"⚠️ CADASTRO: Próxima sessão não foi criada: {next_session_info}")
                        else:
                            logger.warning(f"⚠️ CADASTRO: Falha ao finalizar contexto da session-1: {finalize_result}")
                            
                    except Exception as finalize_error:
                        logger.error(f"❌ CADASTRO: Erro ao finalizar contexto da session-1: {finalize_error}")
                    
                    # 7. Preparar resposta com flags de finalização
                    response_data = {
                        "success": True,
                        "data": {
                            "user_message": {
                                "id": user_message_id,
                                "content": user_message
                            },
                            "ai_response": {
                                "id": ai_message_id,
                                "content": ai_response,
                                "audioUrl": finalization_audio_url,
                                "provider": "registration_system",
                                "model": "cadastro_v1"
                            },
                            # ✅ CORREÇÃO: Flags de finalização definidos imediatamente
                            "registration_completed": True,
                            "session_finished": True,
                            "session_status": "completed",
                            "redirect_to_home": True,
                            "completion_message": "Cadastro finalizado com sucesso! Esta sessão está agora concluída. Você pode revisar a conversa, mas não pode enviar mais mensagens.",
                            "finalize_success": finalize_success,
                            "auto_redirect_delay": 3000  # 3 segundos
                        }
                    }
                    
                    logger.info(f"🎉 CADASTRO: Finalizado com sucesso para {username} - Flags de finalização definidos")
                    return response_data
            
            # Se o cadastro já foi completado, usar mensagem padrão
            ai_response = f"Olá novamente, {username}! Como posso te ajudar hoje?"
            user_message_id = await self._save_message(session_id, "user", user_message)
            ai_message_id = await self._save_message(session_id, "ai", ai_response)
            
            logger.info(f"💬 CADASTRO: Conversa normal pós-cadastro para {username}")
            
            # ✅ CORREÇÃO: Retornar no mesmo formato que process_user_message
            return {
                "success": True,
                "data": {
                    "user_message": {
                        "id": user_message_id,
                        "content": user_message
                    },
                    "ai_response": {
                        "id": ai_message_id,
                        "content": ai_response,
                        "audioUrl": None,
                        "provider": "registration_system",
                        "model": "cadastro_v1"
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na sessão de cadastro: {e}")
            return {
                "success": False,
                "error": f"Erro na sessão de cadastro: {str(e)}"
            }
    
    async def _save_user_profile(self, username: str, registration_data: Dict[str, Any]):
        """
        Salvar perfil completo e padronizado do usuário na coleção users
        """
        try:
            users = get_collection("users")
            
            # ✅ NOVO: Padronizar e estruturar os dados do usuário
            user_profile = self._create_standardized_profile(username, registration_data)
            
            # Atualizar ou criar usuário com perfil padronizado
            await users.update_one(
                {"username": username},
                {
                    "$set": {
                        "username": username,
                        "user_profile": user_profile,
                        "profile_completed": True,
                        "profile_completed_at": datetime.now(),
                        "updated_at": datetime.now()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.now()
                    }
                },
                upsert=True
            )
            
            logger.info(f"✅ Perfil padronizado do usuário {username} salvo com sucesso")
            logger.info(f"📊 Dados salvos: {user_profile}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar perfil do usuário: {e}")

    def _create_standardized_profile(self, username: str, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Criar perfil padronizado a partir dos dados de cadastro
        """
        # Dados pessoais básicos
        personal_info = {
            "idade": self._normalize_age(registration_data.get("idade", "")),
            "genero": self._normalize_gender(registration_data.get("genero", "")),
            "cor_raca": self._normalize_race(registration_data.get("cor_raca", "")),
            "localizacao": self._normalize_location(registration_data.get("localizacao", ""))
        }
        
        # Situação social e familiar
        social_info = {
            "situacao_moradia": self._normalize_text(registration_data.get("situacao_moradia", "")),
            "relacao_familia": self._normalize_text(registration_data.get("relacao_familia", "")),
            "ocupacao": self._normalize_text(registration_data.get("ocupacao", ""))
        }
        
        # Motivação e objetivos terapêuticos
        therapeutic_info = {
            "motivacao_terapia": self._normalize_text(registration_data.get("motivacao_terapia", "")),
            "informacoes_adicionais": self._normalize_text(registration_data.get("informacoes_adicionais", "")),
            "objetivos_identificados": self._extract_objectives(registration_data)
        }
        
        # Perfil completo estruturado
        standardized_profile = {
            "personal_info": personal_info,
            "social_info": social_info,
            "therapeutic_info": therapeutic_info,
            "profile_summary": self._generate_profile_summary(personal_info, social_info, therapeutic_info),
            "keywords": self._extract_keywords(registration_data),
            "risk_factors": self._identify_risk_factors(registration_data),
            "strengths": self._identify_strengths(registration_data),
            "created_at": datetime.now().isoformat(),
            "data_source": "session-1_registration"
        }
        
        return standardized_profile

    def _normalize_age(self, age_input: str) -> Dict[str, Any]:
        """Normalizar idade"""
        try:
            age_text = str(age_input).strip().lower()
            
            # Extrair número da idade
            import re
            age_numbers = re.findall(r'\d+', age_text)
            
            if age_numbers:
                age = int(age_numbers[0])
                
                # Categorizar por faixa etária
                if age < 18:
                    category = "menor_idade"
                elif age < 25:
                    category = "jovem_adulto"
                elif age < 35:
                    category = "adulto_jovem"
                elif age < 50:
                    category = "adulto"
                elif age < 65:
                    category = "adulto_maduro"
                else:
                    category = "idoso"
                
                return {
                    "valor": age,
                    "categoria": category,
                    "original": age_input.strip()
                }
            else:
                return {
                    "valor": None,
                    "categoria": "nao_informado",
                    "original": age_input.strip()
                }
                
        except Exception:
            return {
                "valor": None,
                "categoria": "erro_processamento",
                "original": age_input.strip()
            }

    def _normalize_gender(self, gender_input: str) -> Dict[str, Any]:
        """Normalizar gênero"""
        gender_text = str(gender_input).strip().lower()
        
        # Mapeamento de termos comuns
        gender_mapping = {
            "feminino": "feminino",
            "mulher": "feminino", 
            "f": "feminino",
            "masculino": "masculino",
            "homem": "masculino",
            "m": "masculino",
            "não-binário": "nao_binario",
            "nao binario": "nao_binario",
            "não binário": "nao_binario",
            "nao-binario": "nao_binario",
            "nb": "nao_binario",
            "trans": "trans",
            "transgender": "trans",
            "prefiro não responder": "prefere_nao_responder",
            "prefiro nao responder": "prefere_nao_responder",
            "não responder": "prefere_nao_responder"
        }
        
        normalized = gender_mapping.get(gender_text, "outros")
        
        return {
            "categoria": normalized,
            "original": gender_input.strip()
        }

    def _normalize_race(self, race_input: str) -> Dict[str, Any]:
        """Normalizar cor/raça"""
        race_text = str(race_input).strip().lower()
        
        # Mapeamento baseado no IBGE
        race_mapping = {
            "branco": "branco",
            "branca": "branco",
            "negro": "negro",
            "negra": "negro",
            "preto": "negro",
            "preta": "negro",
            "pardo": "pardo",
            "parda": "pardo",
            "amarelo": "amarelo",
            "amarela": "amarelo",
            "asiático": "amarelo",
            "asiática": "amarelo",
            "indígena": "indigena",
            "índio": "indigena",
            "índia": "indigena",
            "prefiro não responder": "prefere_nao_responder",
            "prefiro nao responder": "prefere_nao_responder"
        }
        
        normalized = race_mapping.get(race_text, "outros")
        
        return {
            "categoria": normalized,
            "original": race_input.strip()
        }

    def _normalize_location(self, location_input: str) -> Dict[str, Any]:
        """Normalizar localização"""
        location_text = str(location_input).strip()
        
        # Tentar extrair cidade e estado
        import re
        
        # Padrões comuns: "Cidade, Estado" ou "Cidade - Estado"
        patterns = [
            r"(.+?)[,\-]\s*(.+?)$",  # Cidade, Estado ou Cidade - Estado
            r"(.+?)\s+(\w{2})$",     # Cidade SP (sigla do estado)
        ]
        
        city = ""
        state = ""
        
        for pattern in patterns:
            match = re.search(pattern, location_text)
            if match:
                city = match.group(1).strip()
                state = match.group(2).strip()
                break
        
        if not city and not state:
            city = location_text
        
        return {
            "cidade": city,
            "estado": state,
            "original": location_input.strip(),
            "formatted": f"{city}, {state}" if state else city
        }

    def _normalize_text(self, text_input: str) -> Dict[str, Any]:
        """Normalizar texto geral"""
        text = str(text_input).strip()
        
        return {
            "content": text,
            "length": len(text),
            "words": len(text.split()) if text else 0,
            "has_content": len(text) > 0
        }

    def _extract_objectives(self, registration_data: Dict[str, Any]) -> List[str]:
        """Extrair objetivos terapêuticos baseados nas respostas"""
        objectives = []
        
        # Analisar motivação para terapia
        motivation = registration_data.get("motivacao_terapia", "").lower()
        
        # Palavras-chave que indicam objetivos específicos
        objective_keywords = {
            "ansiedade": "Trabalhar questões de ansiedade",
            "depressão": "Apoio para questões depressivas",
            "relacionamento": "Melhorar relacionamentos",
            "família": "Resolver questões familiares",
            "trabalho": "Questões profissionais e carreira",
            "autoestima": "Fortalecer autoestima",
            "stress": "Gerenciar stress e pressão",
            "luto": "Processar perdas e luto",
            "mudança": "Lidar com mudanças de vida",
            "crescimento": "Desenvolvimento pessoal"
        }
        
        for keyword, objective in objective_keywords.items():
            if keyword in motivation:
                objectives.append(objective)
        
        # Se não encontrar objetivos específicos, usar objetivo geral
        if not objectives:
            objectives.append("Desenvolvimento pessoal e bem-estar")
        
        return objectives

    def _generate_profile_summary(self, personal_info: Dict, social_info: Dict, therapeutic_info: Dict) -> str:
        """Gerar resumo do perfil do usuário"""
        summary_parts = []
        
        # Informações pessoais
        if personal_info["idade"]["valor"]:
            summary_parts.append(f"Idade: {personal_info['idade']['valor']} anos ({personal_info['idade']['categoria']})")
        
        if personal_info["genero"]["categoria"] != "outros":
            summary_parts.append(f"Gênero: {personal_info['genero']['categoria']}")
        
        if personal_info["localizacao"]["formatted"]:
            summary_parts.append(f"Localização: {personal_info['localizacao']['formatted']}")
        
        # Situação social
        if social_info["ocupacao"]["has_content"]:
            summary_parts.append(f"Ocupação: {social_info['ocupacao']['content'][:50]}...")
        
        # Motivação terapêutica
        if therapeutic_info["motivacao_terapia"]["has_content"]:
            summary_parts.append(f"Motivação: {therapeutic_info['motivacao_terapia']['content'][:100]}...")
        
        return "; ".join(summary_parts)

    def _extract_keywords(self, registration_data: Dict[str, Any]) -> List[str]:
        """Extrair palavras-chave relevantes do cadastro"""
        keywords = []
        
        # Combinar todas as respostas textuais
        text_fields = [
            registration_data.get("genero", ""),
            registration_data.get("situacao_moradia", ""),
            registration_data.get("relacao_familia", ""),
            registration_data.get("ocupacao", ""),
            registration_data.get("motivacao_terapia", ""),
            registration_data.get("informacoes_adicionais", "")
        ]
        
        combined_text = " ".join(text_fields).lower()
        
        # Palavras-chave relevantes para terapia
        relevant_keywords = [
            "ansiedade", "depressão", "stress", "família", "relacionamento",
            "trabalho", "estudos", "autoestima", "confiança", "medo",
            "tristeza", "raiva", "solidão", "conflito", "mudança",
            "crescimento", "desenvolvimento", "apoio", "ajuda"
        ]
        
        for keyword in relevant_keywords:
            if keyword in combined_text:
                keywords.append(keyword)
        
        return keywords

    def _identify_risk_factors(self, registration_data: Dict[str, Any]) -> List[str]:
        """Identificar possíveis fatores de risco mencionados"""
        risk_factors = []
        
        # Combinar respostas para análise
        all_responses = " ".join([
            registration_data.get("relacao_familia", ""),
            registration_data.get("motivacao_terapia", ""),
            registration_data.get("informacoes_adicionais", "")
        ]).lower()
        
        # Indicadores de possíveis fatores de risco
        risk_indicators = {
            "isolamento": ["sozinho", "isolado", "sem amigos", "sem apoio"],
            "conflitos_familiares": ["conflito", "briga", "problema família", "família difícil"],
            "questoes_profissionais": ["desempregado", "sem trabalho", "stress trabalho", "problema trabalho"],
            "questoes_emocionais": ["deprimido", "triste", "ansioso", "medo", "pânico"],
            "mudancas_significativas": ["separação", "divórcio", "morte", "luto", "mudança"]
        }
        
        for risk_type, indicators in risk_indicators.items():
            for indicator in indicators:
                if indicator in all_responses:
                    risk_factors.append(risk_type)
                    break
        
        return list(set(risk_factors))  # Remove duplicatas

    def _identify_strengths(self, registration_data: Dict[str, Any]) -> List[str]:
        """Identificar forças e recursos positivos mencionados"""
        strengths = []
        
        # Combinar respostas para análise
        all_responses = " ".join([
            registration_data.get("situacao_moradia", ""),
            registration_data.get("relacao_familia", ""),
            registration_data.get("ocupacao", ""),
            registration_data.get("motivacao_terapia", ""),
            registration_data.get("informacoes_adicionais", "")
        ]).lower()
        
        # Indicadores de forças e recursos
        strength_indicators = {
            "apoio_familiar": ["família unida", "apoio família", "família próxima", "bom relacionamento família"],
            "apoio_social": ["amigos", "apoio", "grupo", "comunidade"],
            "estabilidade_profissional": ["trabalho", "empregado", "carreira", "estudando"],
            "autoconsciencia": ["autoconhecimento", "crescimento", "desenvolvimento", "melhorar"],
            "motivacao_mudanca": ["quer mudar", "disposto", "determinado", "esperança"]
        }
        
        for strength_type, indicators in strength_indicators.items():
            for indicator in indicators:
                if indicator in all_responses:
                    strengths.append(strength_type)
                    break
        
        return list(set(strengths))  # Remove duplicatas 

    async def _generate_audio_for_registration(self, ai_response: str, username: str, is_voice_mode: bool) -> Optional[str]:
        """
        Gerar áudio para respostas da sessão de cadastro quando VoiceMode está ativo
        """
        if not is_voice_mode:
            return None
            
        try:
            # Buscar preferências do usuário para áudio
            users_collection = get_collection("users")
            user = await users_collection.find_one({"username": username})
            
            selected_voice = "pt-BR-Neural2-A"  # padrão
            if user and user.get("preferences"):
                selected_voice = user["preferences"].get("selected_voice", selected_voice)
            
            logger.info(f"🎤 Gerando áudio para cadastro (VoiceMode) - {username}, voz: {selected_voice}")
            
            # Gerar áudio usando a função existente
            audio_url = await self._generate_audio(ai_response, selected_voice, is_voice_mode)
            
            if audio_url:
                logger.info(f"✅ Áudio gerado para cadastro: {audio_url}")
            else:
                logger.warning(f"⚠️ Falha ao gerar áudio para cadastro")
                
            return audio_url
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar áudio para cadastro: {e}")
            return None

    # ✅ NOVO: Sistema de cadastro/onboarding para session-1
