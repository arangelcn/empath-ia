"""
Serviço de chat - orquestra conversas e mensagens
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from ..models.conversation import ConversationModel, ConversationRepository
from ..models.message import MessageModel, MessageRepository

logger = logging.getLogger(__name__)

class ChatService:
    """
    Serviço principal para gerenciar conversas e mensagens
    """
    
    def __init__(self):
        self.conversation_repo = ConversationRepository()
        self.message_repo = MessageRepository()
    
    async def start_or_get_conversation(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Iniciar nova conversa ou recuperar existente
        """
        try:
            if session_id:
                # Tentar recuperar conversa existente
                conversation = await self.conversation_repo.get_conversation_by_session_id(session_id)
                if conversation:
                    # Carregar histórico de mensagens
                    history = await self.message_repo.get_conversation_history(conversation.id)
                    
                    return {
                        "conversation_id": conversation.id,
                        "session_id": conversation.session_id,
                        "created_at": conversation.created_at.isoformat(),
                        "message_count": conversation.message_count,
                        "history": history,
                        "is_new": False
                    }
            
            # Criar nova conversa
            conversation = ConversationModel()
            if session_id:
                conversation.session_id = session_id
            
            conversation_id = await self.conversation_repo.create_conversation(conversation)
            
            return {
                "conversation_id": conversation_id,
                "session_id": conversation.session_id,
                "created_at": conversation.created_at.isoformat(),
                "message_count": 0,
                "history": [],
                "is_new": True
            }
            
        except Exception as e:
            logger.error(f"Erro ao iniciar/recuperar conversa: {e}")
            raise
    
    async def process_user_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Processar mensagem do usuário e gerar resposta
        """
        start_time = time.time()
        
        try:
            # Obter ou criar conversa
            conversation_data = await self.start_or_get_conversation(session_id)
            conversation_id = conversation_data["conversation_id"]
            
            # Salvar mensagem do usuário
            user_msg = MessageModel(
                conversation_id=conversation_id,
                content=user_message,
                message_type="user"
            )
            user_message_id = await self.message_repo.create_message(user_msg)
            
            # Gerar resposta da IA (por enquanto, resposta padrão)
            ai_response = await self._generate_ai_response(user_message, conversation_data["history"])
            
            # Salvar resposta da IA
            ai_msg = MessageModel(
                conversation_id=conversation_id,
                content=ai_response["content"],
                message_type="ai",
                has_video=ai_response.get("has_video", False),
                video_url=ai_response.get("video_url"),
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
            ai_message_id = await self.message_repo.create_message(ai_msg)
            
            # Atualizar contador de mensagens na conversa
            await self.conversation_repo.increment_message_count(conversation_id)
            await self.conversation_repo.increment_message_count(conversation_id)  # User + AI
            
            # Retornar resposta formatada para o frontend
            return {
                "session_id": session_id,
                "conversation_id": conversation_id,
                "user_message": {
                    "id": user_message_id,
                    "content": user_message,
                    "type": "user",
                    "timestamp": user_msg.created_at.isoformat()
                },
                "ai_response": {
                    "id": ai_message_id,
                    "content": ai_response["content"],
                    "type": "ai",
                    "timestamp": ai_msg.created_at.isoformat(),
                    "hasVideo": ai_response.get("has_video", False),
                    "videoUrl": ai_response.get("video_url")
                },
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "total_messages": conversation_data["message_count"] + 2
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            
            # Salvar mensagem de erro
            try:
                error_msg = MessageModel(
                    conversation_id=conversation_id if 'conversation_id' in locals() else "unknown",
                    content=f"Erro interno: {str(e)}",
                    message_type="error"
                )
                await self.message_repo.create_message(error_msg)
            except:
                pass  # Se não conseguir salvar erro, não falhar novamente
            
            raise
    
    async def _generate_ai_response(self, user_message: str, history: List[Dict]) -> Dict[str, Any]:
        """
        Gerar resposta da IA (temporariamente resposta padrão)
        """
        # TODO: Integrar com OpenAI posteriormente
        
        # Respostas padrão baseadas em contexto simples
        user_lower = user_message.lower()
        
        if any(word in user_lower for word in ["olá", "oi", "hello", "hi"]):
            response = "Olá! Sou sua psicóloga virtual. Como posso ajudá-lo hoje? Conte-me o que está sentindo."
        
        elif any(word in user_lower for word in ["triste", "deprimido", "depressão", "mal"]):
            response = "Entendo que você está passando por um momento difícil. É muito corajoso buscar ajuda. Pode me contar mais sobre o que está sentindo? Lembre-se: você não está sozinho."
        
        elif any(word in user_lower for word in ["ansioso", "ansiedade", "nervoso", "preocupado"]):
            response = "A ansiedade é algo muito comum e tratável. Vamos trabalhar juntos para encontrar estratégias que funcionem para você. Que situações costumam despertar essa ansiedade?"
        
        elif any(word in user_lower for word in ["obrigado", "obrigada", "thank", "thanks"]):
            response = "Fico feliz em poder ajudar! É um prazer acompanhá-lo nessa jornada. Como você está se sentindo agora?"
        
        elif any(word in user_lower for word in ["tchau", "bye", "adeus"]):
            response = "Foi um prazer conversar com você. Lembre-se: estou sempre aqui quando precisar. Cuide-se bem! 💙"
        
        else:
            # Resposta genérica empática
            response = f"Entendo sua preocupação. É importante que você tenha compartilhado isso comigo. Vamos explorar essa questão juntos. Pode me contar mais detalhes sobre como isso afeta seu dia a dia?"
        
        return {
            "content": response,
            "has_video": False,  # Por enquanto sem vídeo
            "video_url": None
        }
    
    async def get_conversation_history(self, session_id: str) -> Dict[str, Any]:
        """
        Obter histórico completo de uma conversa
        """
        try:
            conversation_data = await self.start_or_get_conversation(session_id)
            
            return {
                "session_id": session_id,
                "conversation_id": conversation_data["conversation_id"],
                "created_at": conversation_data["created_at"],
                "message_count": conversation_data["message_count"],
                "history": conversation_data["history"]
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            raise
    
    async def list_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Listar conversas recentes
        """
        try:
            conversations = await self.conversation_repo.list_conversations(limit=limit)
            
            result = []
            for conv in conversations:
                # Obter última mensagem para preview
                messages = await self.message_repo.get_messages_by_conversation(
                    conv.id, skip=max(0, conv.message_count - 1), limit=1
                )
                
                last_message = messages[0] if messages else None
                
                result.append({
                    "conversation_id": conv.id,
                    "session_id": conv.session_id,
                    "title": conv.title or "Conversa sem título",
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": conv.message_count,
                    "last_message": {
                        "content": last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else last_message.content if last_message else "",
                        "type": last_message.message_type if last_message else "system",
                        "timestamp": last_message.created_at.isoformat() if last_message else conv.created_at.isoformat()
                    } if last_message else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao listar conversas: {e}")
            raise 