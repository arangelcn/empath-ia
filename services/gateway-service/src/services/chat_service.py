"""
Serviço de chat - orquestra conversas e mensagens
"""

import os
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from ..models.database import get_collection

logger = logging.getLogger(__name__)

class ChatService:
    """Serviço de chat com persistência MongoDB"""
    
    def __init__(self):
        self.ai_service_url = os.getenv("AI_SERVICE_URL", "http://ai-service:8001")
        # self.voice_service_url = os.getenv("VOICE_SERVICE_URL", "http://voice-service:8004")  # Comentado temporariamente
    
    async def start_or_get_conversation(self, session_id: str) -> Dict[str, Any]:
        """Iniciar ou recuperar conversa existente"""
        try:
            conversations = get_collection("conversations")
            
            # Verificar se a conversa já existe
            existing = await conversations.find_one({"session_id": session_id})
            
            if existing:
                logger.info(f"📖 Recuperando conversa existente: {session_id}")
                return {
                    "session_id": session_id,
                    "exists": True,
                    "user_preferences": existing.get("user_preferences", {}),
                    "created_at": existing.get("created_at"),
                    "updated_at": existing.get("updated_at")
                }
            else:
                # Criar nova conversa
                conversation_data = {
                    "session_id": session_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "user_preferences": {},
                    "message_count": 0
                }
                
                await conversations.insert_one(conversation_data)
                logger.info(f"🆕 Nova conversa criada: {session_id}")
                
                return {
                    "session_id": session_id,
                    "exists": False,
                    "created_at": conversation_data["created_at"]
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar/recuperar conversa: {e}")
            raise
    
    async def process_user_message(self, session_id: str, user_message: str, session_objective: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processar mensagem do usuário e gerar resposta"""
        try:
            # Garantir que a conversa existe
            await self.start_or_get_conversation(session_id)
            
            # Buscar preferências do usuário
            conversations = get_collection("conversations")
            conversation = await conversations.find_one({"session_id": session_id})
            selected_voice = None
            voice_enabled = True  # padrão habilitado
            if conversation:
                user_prefs = conversation.get("user_preferences", {})
                selected_voice = user_prefs.get("selected_voice")
                voice_enabled = user_prefs.get("voice_enabled", True)
            if not selected_voice:
                selected_voice = "pt-BR-Neural2-A"  # fallback padrão
            
            # Verificar se é a primeira mensagem (sem histórico) e buscar initial_prompt
            initial_prompt = None
            conversation_history = await self._get_conversation_context(session_id)
            if not conversation_history:  # Primeira mensagem
                logger.info(f"🔍 Primeira mensagem da sessão {session_id} - buscando initial_prompt")
                initial_prompt = await self._get_session_initial_prompt(session_id)
                if initial_prompt:
                    logger.info(f"📝 Usando initial_prompt para primeira mensagem da sessão {session_id}: {initial_prompt[:100]}...")
                else:
                    logger.info(f"⚠️ Nenhum initial_prompt encontrado para sessão {session_id}")
            else:
                logger.info(f"📚 Conversa existente com {len(conversation_history)} mensagens - não usando initial_prompt")
            
            # Salvar mensagem do usuário
            user_msg_id = await self._save_message(session_id, "user", user_message)
            
            # Obter resposta da IA (incluindo initial_prompt se for primeira mensagem)
            ai_response = await self._get_ai_response(user_message, session_id, selected_voice, voice_enabled, session_objective, initial_prompt)
            
            # Salvar resposta da IA
            ai_msg_id = await self._save_message(session_id, "ai", ai_response["content"], ai_response.get("audio_url"))
            
            # Atualizar contador de mensagens
            await self._update_message_count(session_id)
            
            return {
                "id": ai_msg_id,
                "content": ai_response["content"],
                "audioUrl": ai_response.get("audio_url"),
                "session_id": session_id,
                "provider": ai_response.get("provider", "unknown"),
                "model": ai_response.get("model", "unknown")
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {e}")
            raise
    
    async def get_conversation_history(self, session_id: str) -> Dict[str, Any]:
        """Obter histórico completo de uma conversa"""
        try:
            messages = get_collection("messages")
            
            # Buscar todas as mensagens da sessão
            cursor = messages.find(
                {"session_id": session_id},
                sort=[("created_at", 1)]
            )
            
            history = []
            async for msg in cursor:
                history.append({
                    "id": str(msg["_id"]),
                    "type": msg["type"],
                    "content": msg["content"],
                    "audio_url": msg.get("audio_url"),
                    "created_at": msg["created_at"]
                })
            
            return {
                "session_id": session_id,
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
            
            update_data["updated_at"] = datetime.utcnow()
            
            result = await conversations.update_one(
                {"session_id": session_id},
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
            
            message_data = {
                "session_id": session_id,
                "type": message_type,
                "content": content,
                "audio_url": audio_url,
                "created_at": datetime.utcnow()
            }
            
            result = await messages.insert_one(message_data)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar mensagem: {e}")
            raise
    
    async def _get_ai_response(self, user_message: str, session_id: str, selected_voice: str, voice_enabled: bool = True, session_objective: Optional[Dict[str, Any]] = None, initial_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Obter resposta da IA via AI Service com contexto da conversa"""
        try:
            # Obter histórico da conversa para contexto
            conversation_history = await self._get_conversation_context(session_id)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Preparar payload com contexto
                payload = {
                    "message": user_message,
                    "session_id": session_id,
                    "session_objective": session_objective,
                    "initial_prompt": initial_prompt
                }
                
                # Adicionar histórico se disponível (últimas 6 mensagens para otimizar tokens)
                if conversation_history:
                    # Limitar a últimas 6 mensagens para economizar tokens
                    limited_history = conversation_history[-6:]
                    payload["conversation_history"] = limited_history
                    logger.info(f"📊 Enviando contexto: {len(limited_history)} mensagens para sessão {session_id}")
                
                # Obter resposta textual da IA
                response = await client.post(
                    f"{self.ai_service_url}/chat",
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response_text = data.get("response", "Desculpe, não consegui processar sua mensagem.")
                    
                    return {
                        "content": ai_response_text,
                        "audio_url": None,  # Não geramos mais áudio
                        "provider": data.get("provider", "unknown"),
                        "model": data.get("model", "unknown")
                    }
                else:
                    logger.warning(f"⚠️ AI Service retornou {response.status_code}")
                    return {
                        "content": "Desculpe, o serviço de IA está temporariamente indisponível.",
                        "audio_url": None,
                        "provider": "fallback",
                        "model": "fallback"
                    }
                    
        except Exception as e:
            logger.error(f"❌ Erro ao obter resposta da IA: {e}")
            return {
                "content": "Desculpe, ocorreu um erro ao processar sua mensagem.",
                "audio_url": None,
                "provider": "fallback",
                "model": "fallback"
            }
    
    async def _get_conversation_context(self, session_id: str) -> List[Dict[str, Any]]:
        """Obter contexto da conversa para enviar ao AI Service"""
        try:
            messages = get_collection("messages")
            
            # Buscar mensagens da sessão (excluindo a atual)
            cursor = messages.find(
                {"session_id": session_id},
                sort=[("created_at", 1)]
            )
            
            context = []
            async for msg in cursor:
                # Converter para formato esperado pelo AI Service
                context.append({
                    "type": msg["type"],
                    "content": msg["content"]
                })
            
            logger.info(f"🔍 Contexto da conversa {session_id}: {len(context)} mensagens")
            return context
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter contexto da conversa: {e}")
            return []
    
    async def _get_session_initial_prompt(self, session_id: str) -> Optional[str]:
        """Buscar o initial_prompt da sessão terapêutica do usuário"""
        try:
            # Buscar na coleção user_therapeutic_sessions
            user_sessions = get_collection("user_therapeutic_sessions")
            user_session = await user_sessions.find_one({"session_id": session_id})
            
            if user_session and user_session.get("initial_prompt"):
                return user_session["initial_prompt"]
            
            # Se não encontrar, buscar na coleção therapeutic_sessions (template)
            sessions = get_collection("therapeutic_sessions")
            session = await sessions.find_one({"session_id": session_id})
            
            if session and session.get("initial_prompt"):
                return session["initial_prompt"]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar initial_prompt para sessão {session_id}: {e}")
            return None
    
    # async def _generate_audio(self, text: str, session_id: str, voice: str) -> Optional[str]:
    #     """Gerar áudio via Voice Service - COMENTADO TEMPORARIAMENTE"""
    #     try:
    #         async with httpx.AsyncClient(timeout=60.0) as client:
    #             response = await client.post(
    #                 f"{self.voice_service_url}/api/v1/synthesize",
    #                 json={
    #                     "text": text,
    #                     "voice": voice,
    #                     "speed": 1.0,
    #                     "pitch": 0.0
    #             }
    #             )
    #             
    #             if response.status_code == 200:
    #                 data = response.json()
    #                 audio_url = data.get("audio_url")
    #                 if audio_url:
    #                     # Extrair o nome do arquivo da URL completa
    #                     audio_filename = audio_url.split("/")[-1]
    #                     # Retornar URL para acessar o áudio via gateway
    #                     return f"/api/voice/audio/{audio_filename}"
    #                 else:
    #                     logger.warning("⚠️ Voice Service não retornou URL do áudio")
    #                     return None
    #             else:
    #                 logger.warning(f"⚠️ Voice Service retornou {response.status_code}: {response.text}")
    #                 return None
    #                 
    #     except Exception as e:
    #         logger.error(f"❌ Erro ao gerar áudio: {e}")
    #         return None
    
    async def _update_message_count(self, session_id: str):
        """Atualizar contador de mensagens da conversa"""
        try:
            conversations = get_collection("conversations")
            await conversations.update_one(
                {"session_id": session_id},
                {"$inc": {"message_count": 1}, "$set": {"updated_at": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar contador: {e}")
    
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
                    "session_id": conv["session_id"],
                    "created_at": conv["created_at"],
                    "updated_at": conv["updated_at"],
                    "message_count": conv.get("message_count", 0)
                })
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar conversas: {e}")
            raise

    async def get_conversation_by_session_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Busca uma conversa pelo session_id e retorna como dicionário."""
        try:
            conversations = get_collection("conversations")
            conversation = await conversations.find_one({"session_id": session_id})
            
            if conversation:
                return {
                    "session_id": conversation["session_id"],
                    "created_at": conversation["created_at"],
                    "updated_at": conversation["updated_at"],
                    "message_count": conversation.get("message_count", 0),
                    "user_preferences": conversation.get("user_preferences", {})
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar conversa por session_id: {e}")
            raise 