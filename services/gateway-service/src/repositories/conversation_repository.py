"""
Repository for conversation/message persistence in MongoDB.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..models.database import get_collection

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Encapsulates all MongoDB access for conversations and messages."""

    def __init__(self, resolve_ref, extract_username):
        self._resolve_ref = resolve_ref
        self._extract_username = extract_username

    # ------------------------------------------------------------------
    # get_history  (based on get_conversation_history)
    # ------------------------------------------------------------------

    async def get_history(self, session_id: str) -> Dict[str, Any]:
        """Obter histórico completo de uma conversa"""
        try:
            messages = get_collection("messages")
            identity = await self._resolve_ref(session_id)
            chat_id = identity.get("chat_id")
            session_id = identity.get("legacy_session_id") or session_id

            # 🔒 CORREÇÃO CRÍTICA: Extrair username para validação adicional
            username = identity.get("username") or self._extract_username(session_id)

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

    # ------------------------------------------------------------------
    # save_message  (based on _save_message)
    # ------------------------------------------------------------------

    async def save_message(self, session_id: str, message_type: str, content: str, audio_url: Optional[str] = None) -> str:
        """Salvar mensagem no MongoDB"""
        try:
            messages = get_collection("messages")
            identity = await self._resolve_ref(session_id)
            chat_id = identity.get("chat_id")
            session_id = identity.get("legacy_session_id") or session_id

            # 🔒 CORREÇÃO CRÍTICA: Extrair username do session_id para validação adicional
            username = identity.get("username") or self._extract_username(session_id)

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

    # ------------------------------------------------------------------
    # update  (based on update_conversation_data)
    # ------------------------------------------------------------------

    async def update(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Atualizar dados da conversa"""
        try:
            conversations = get_collection("conversations")
            identity = await self._resolve_ref(session_id)

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

    # ------------------------------------------------------------------
    # update_message_count  (based on _update_message_count)
    # ------------------------------------------------------------------

    async def update_message_count(self, session_id: str):
        """Atualizar contador de mensagens da conversa"""
        try:
            conversations = get_collection("conversations")
            identity = await self._resolve_ref(session_id)
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

    # ------------------------------------------------------------------
    # list_recent  (based on list_recent_conversations)
    # ------------------------------------------------------------------

    async def list_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
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

    # ------------------------------------------------------------------
    # get_by_session_id  (based on get_conversation_by_session_id)
    # ------------------------------------------------------------------

    async def get_by_session_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Busca uma conversa por chat_id novo ou session_id legado e retorna como dicionário."""
        try:
            identity = await self._resolve_ref(session_id)
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

    # ------------------------------------------------------------------
    # get_context  (based on _get_conversation_context)
    # ------------------------------------------------------------------

    async def get_context(self, session_id: str) -> List[Dict[str, Any]]:
        """Obter contexto da conversa para enviar ao AI Service"""
        try:
            messages = get_collection("messages")
            identity = await self._resolve_ref(session_id)
            chat_id = identity.get("chat_id")
            session_id = identity.get("legacy_session_id") or session_id

            # 🔒 CORREÇÃO CRÍTICA: Extrair username para validação adicional
            username = identity.get("username") or self._extract_username(session_id)

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

    # ------------------------------------------------------------------
    # get_initial_prompt  (based on _get_session_initial_prompt)
    # ------------------------------------------------------------------

    async def get_initial_prompt(self, session_id: str) -> Optional[str]:
        """Buscar o initial_prompt da sessão terapêutica do usuário"""
        try:
            identity = await self._resolve_ref(session_id)
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
