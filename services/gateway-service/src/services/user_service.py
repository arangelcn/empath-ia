"""
Serviço de usuários - gerencia usuários e suas preferências
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from ..models.database import get_users_collection

logger = logging.getLogger(__name__)

class UserService:
    """Serviço de usuários com persistência MongoDB"""
    
    def __init__(self):
        self._users_collection = None
    
    @property
    def users_collection(self):
        if self._users_collection is None:
            self._users_collection = get_users_collection()
        return self._users_collection
    
    async def create_user(self, username: str, email: Optional[str] = None, 
                         preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Criar novo usuário"""
        try:
            # Verificar se usuário já existe
            existing_user = await self.users_collection.find_one({"username": username})
            if existing_user:
                raise ValueError(f"Usuário '{username}' já existe")
            
            user_data = {
                "username": username,
                "email": email,
                "preferences": preferences or {
                    "selected_voice": "pt-BR-Neural2-A",
                    "voice_enabled": True,
                    "theme": "dark",
                    "language": "pt-BR"
                },
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
                "is_active": True,
                "session_count": 0
            }

            if preferences:
                if preferences.get("full_name"):
                    user_data["full_name"] = preferences["full_name"]
                if preferences.get("display_name"):
                    user_data["display_name"] = preferences["display_name"]
            
            result = await self.users_collection.insert_one(user_data)
            user_data["_id"] = str(result.inserted_id)
            
            logger.info(f"🆕 Usuário criado: {username}")
            return {
                "success": True,
                "user": user_data
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar usuário: {e}")
            raise
    
    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Obter usuário por username"""
        try:
            user = await self.users_collection.find_one({"username": username})
            if user:
                user["_id"] = str(user["_id"])
            return user
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter usuário: {e}")
            raise
    
    async def update_user_preferences(self, username: str, preferences: Dict[str, Any]) -> bool:
        """Atualizar preferências do usuário"""
        try:
            update_fields = {
                "preferences": preferences,
                "updated_at": datetime.utcnow()
            }

            if "full_name" in preferences:
                update_fields["full_name"] = preferences.get("full_name")
            if "display_name" in preferences:
                update_fields["display_name"] = preferences.get("display_name")

            result = await self.users_collection.update_one(
                {"username": username},
                {"$set": update_fields}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Preferências atualizadas para usuário: {username}")
                return True
            else:
                logger.warning(f"⚠️ Usuário não encontrado: {username}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar preferências: {e}")
            raise
    
    async def update_last_login(self, username: str) -> bool:
        """Atualizar último login do usuário"""
        try:
            result = await self.users_collection.update_one(
                {"username": username},
                {
                    "$set": {
                        "last_login": datetime.utcnow()
                    },
                    "$inc": {
                        "login_count": 1
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar último login: {e}")
            raise
    
    async def increment_session_count(self, username: str) -> bool:
        """Incrementar contador de sessões do usuário"""
        try:
            result = await self.users_collection.update_one(
                {"username": username},
                {
                    "$inc": {
                        "session_count": 1
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Erro ao incrementar contador de sessões: {e}")
            raise
    
    async def list_users(self, limit: int = 50, offset: int = 0, 
                        active_only: bool = True) -> List[Dict[str, Any]]:
        """Listar usuários"""
        try:
            filter_query = {}
            if active_only:
                filter_query["is_active"] = True
            
            cursor = self.users_collection.find(
                filter_query,
                sort=[("created_at", -1)]
            ).skip(offset).limit(limit)
            
            users = []
            async for user in cursor:
                user["_id"] = str(user["_id"])
                users.append(user)
            
            return users
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar usuários: {e}")
            raise
    
    async def deactivate_user(self, username: str) -> bool:
        """Desativar usuário"""
        try:
            result = await self.users_collection.update_one(
                {"username": username},
                {
                    "$set": {
                        "is_active": False,
                        "deactivated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Usuário desativado: {username}")
                return True
            else:
                logger.warning(f"⚠️ Usuário não encontrado: {username}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao desativar usuário: {e}")
            raise
    
    async def get_user_stats(self, username: str) -> Optional[Dict[str, Any]]:
        """Obter estatísticas do usuário"""
        try:
            user = await self.get_user(username)
            if not user:
                return None
            
            # Buscar conversas do usuário
            from .chat_service import ChatService
            chat_service = ChatService()
            
            # Contar conversas do usuário
            conversations = await chat_service.list_recent_conversations(limit=1000)
            user_conversations = [c for c in conversations if c.get("session_id", "").startswith(username)]
            
            stats = {
                "username": username,
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login"),
                "login_count": user.get("login_count", 0),
                "session_count": user.get("session_count", 0),
                "conversation_count": len(user_conversations),
                "is_active": user.get("is_active", True),
                "preferences": user.get("preferences", {})
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas do usuário: {e}")
            raise
