"""
Serviço de sessões terapêuticas dos usuários - gerencia sessões individuais de cada usuário
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from ..models.database import get_user_therapeutic_sessions_collection, get_therapeutic_sessions_collection

logger = logging.getLogger(__name__)

class UserTherapeuticSessionService:
    """Serviço de sessões terapêuticas dos usuários com persistência MongoDB"""
    
    def __init__(self):
        self._user_sessions_collection = None
        self._template_sessions_collection = None
    
    @property
    def user_sessions_collection(self):
        if self._user_sessions_collection is None:
            self._user_sessions_collection = get_user_therapeutic_sessions_collection()
        return self._user_sessions_collection
    
    @property
    def template_sessions_collection(self):
        if self._template_sessions_collection is None:
            self._template_sessions_collection = get_therapeutic_sessions_collection()
        return self._template_sessions_collection
    
    async def clone_sessions_for_user(self, username: str) -> Dict[str, Any]:
        """Clonar todas as sessões terapêuticas ativas para um usuário"""
        try:
            # Buscar todas as sessões templates ativas
            template_sessions = await self.template_sessions_collection.find(
                {"is_active": True}
            ).to_list(length=100)
            
            if not template_sessions:
                logger.warning(f"⚠️ Nenhuma sessão template encontrada para clonar para usuário: {username}")
                return {
                    "success": True,
                    "message": "Nenhuma sessão template disponível",
                    "cloned_count": 0
                }
            
            # Verificar quais sessões já existem para o usuário
            existing_sessions = await self.user_sessions_collection.find(
                {"username": username}
            ).to_list(length=100)
            
            existing_session_ids = {session["session_id"] for session in existing_sessions}
            
            # Clonar apenas sessões que não existem
            cloned_count = 0
            first_session = True  # Flag para identificar a primeira sessão
            
            for template_session in template_sessions:
                session_id = template_session["session_id"]
                
                if session_id not in existing_session_ids:
                    # Determinar o status da sessão
                    # A primeira sessão será desbloqueada automaticamente
                    session_status = "unlocked" if first_session else "locked"
                    
                    # Criar sessão do usuário baseada no template
                    user_session = {
                        "username": username,
                        "session_id": session_id,
                        "template_session_id": session_id,  # Referência ao template
                        "title": template_session["title"],
                        "subtitle": template_session.get("subtitle", ""),
                        "description": template_session.get("description", ""),
                        "objective": template_session.get("objective", ""),  # Incluir objetivo
                        "initial_prompt": template_session.get("initial_prompt", ""),  # Incluir prompt inicial
                        "category": template_session.get("category", "general"),
                        "difficulty": template_session.get("difficulty", "beginner"),
                        "estimated_duration": template_session.get("estimated_duration", 30),
                        "status": session_status,  # Primeira sessão desbloqueada
                        "progress": 0,  # Progresso inicial
                        "completed_at": None,
                        "started_at": None,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "is_active": True
                    }
                    
                    await self.user_sessions_collection.insert_one(user_session)
                    cloned_count += 1
                    
                    if first_session:
                        logger.info(f"✅ Primeira sessão desbloqueada para {username}: {session_id}")
                        first_session = False
                    else:
                        logger.info(f"✅ Sessão clonada para {username}: {session_id}")
            
            logger.info(f"✅ {cloned_count} sessões clonadas para usuário: {username}")
            
            return {
                "success": True,
                "message": f"{cloned_count} sessões clonadas com sucesso",
                "cloned_count": cloned_count,
                "total_templates": len(template_sessions)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao clonar sessões para usuário {username}: {e}")
            raise
    
    async def get_user_sessions(self, username: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obter sessões de um usuário com filtro opcional por status"""
        try:
            filter_query = {"username": username, "is_active": True}
            if status:
                filter_query["status"] = status
            
            cursor = self.user_sessions_collection.find(filter_query).sort("created_at", 1)
            sessions = await cursor.to_list(length=100)
            
            # Formatar dados
            formatted_sessions = []
            for session in sessions:
                session["_id"] = str(session["_id"])
                formatted_sessions.append(session)
            
            return formatted_sessions
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter sessões do usuário {username}: {e}")
            raise
    
    async def get_user_session(self, username: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Obter uma sessão específica de um usuário"""
        try:
            session = await self.user_sessions_collection.find_one({
                "username": username,
                "session_id": session_id
            })
            
            if session:
                session["_id"] = str(session["_id"])
            
            return session
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter sessão {session_id} do usuário {username}: {e}")
            raise
    
    async def unlock_session(self, username: str, session_id: str) -> bool:
        """Desbloquear uma sessão para o usuário"""
        try:
            result = await self.user_sessions_collection.update_one(
                {
                    "username": username,
                    "session_id": session_id
                },
                {
                    "$set": {
                        "status": "unlocked",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Sessão {session_id} desbloqueada para usuário {username}")
                return True
            else:
                logger.warning(f"⚠️ Sessão {session_id} não encontrada para usuário {username}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao desbloquear sessão {session_id} para usuário {username}: {e}")
            raise
    
    async def start_session(self, username: str, session_id: str) -> bool:
        """Iniciar uma sessão para o usuário"""
        try:
            result = await self.user_sessions_collection.update_one(
                {
                    "username": username,
                    "session_id": session_id
                },
                {
                    "$set": {
                        "status": "in_progress",
                        "started_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Sessão {session_id} iniciada para usuário {username}")
                return True
            else:
                logger.warning(f"⚠️ Sessão {session_id} não encontrada para usuário {username}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar sessão {session_id} para usuário {username}: {e}")
            raise
    
    async def complete_session(self, username: str, session_id: str, progress: int = 100) -> bool:
        """Marcar uma sessão como concluída para o usuário"""
        try:
            result = await self.user_sessions_collection.update_one(
                {
                    "username": username,
                    "session_id": session_id
                },
                {
                    "$set": {
                        "status": "completed",
                        "progress": progress,
                        "completed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Sessão {session_id} concluída para usuário {username}")
                return True
            else:
                logger.warning(f"⚠️ Sessão {session_id} não encontrada para usuário {username}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao concluir sessão {session_id} para usuário {username}: {e}")
            raise
    
    async def update_session_progress(self, username: str, session_id: str, progress: int) -> bool:
        """Atualizar progresso de uma sessão"""
        try:
            result = await self.user_sessions_collection.update_one(
                {
                    "username": username,
                    "session_id": session_id
                },
                {
                    "$set": {
                        "progress": progress,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Progresso da sessão {session_id} atualizado para {progress}% - usuário {username}")
                return True
            else:
                logger.warning(f"⚠️ Sessão {session_id} não encontrada para usuário {username}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar progresso da sessão {session_id} para usuário {username}: {e}")
            raise
    
    async def get_user_progress(self, username: str) -> Dict[str, Any]:
        """Obter progresso geral do usuário"""
        try:
            # Buscar todas as sessões do usuário
            sessions = await self.get_user_sessions(username)
            
            total_sessions = len(sessions)
            completed_sessions = len([s for s in sessions if s["status"] == "completed"])
            in_progress_sessions = len([s for s in sessions if s["status"] == "in_progress"])
            unlocked_sessions = len([s for s in sessions if s["status"] == "unlocked"])
            locked_sessions = len([s for s in sessions if s["status"] == "locked"])
            
            # Calcular progresso geral
            overall_progress = 0
            if total_sessions > 0:
                overall_progress = (completed_sessions / total_sessions) * 100
            
            return {
                "username": username,
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "in_progress_sessions": in_progress_sessions,
                "unlocked_sessions": unlocked_sessions,
                "locked_sessions": locked_sessions,
                "overall_progress": round(overall_progress, 1),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter progresso do usuário {username}: {e}")
            raise
    
    async def unlock_first_session(self, username: str) -> bool:
        """Desbloquear a primeira sessão do usuário se não houver nenhuma desbloqueada"""
        try:
            # Verificar se o usuário tem alguma sessão desbloqueada
            unlocked_sessions = await self.user_sessions_collection.count_documents({
                "username": username,
                "status": {"$in": ["unlocked", "in_progress", "completed"]}
            })
            
            if unlocked_sessions == 0:
                # Buscar a primeira sessão do usuário (ordenada por data de criação)
                first_session = await self.user_sessions_collection.find_one(
                    {"username": username},
                    sort=[("created_at", 1)]
                )
                
                if first_session:
                    result = await self.user_sessions_collection.update_one(
                        {"_id": first_session["_id"]},
                        {
                            "$set": {
                                "status": "unlocked",
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    
                    if result.modified_count > 0:
                        logger.info(f"✅ Primeira sessão desbloqueada para usuário existente {username}: {first_session['session_id']}")
                        return True
                    else:
                        logger.warning(f"⚠️ Não foi possível desbloquear primeira sessão para {username}")
                        return False
                else:
                    logger.warning(f"⚠️ Nenhuma sessão encontrada para usuário {username}")
                    return False
            else:
                logger.info(f"ℹ️ Usuário {username} já tem sessões desbloqueadas")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao desbloquear primeira sessão para usuário {username}: {e}")
            raise
    
    async def reset_user_sessions(self, username: str) -> bool:
        """Resetar todas as sessões de um usuário (para testes)"""
        try:
            result = await self.user_sessions_collection.delete_many({"username": username})
            
            if result.deleted_count > 0:
                logger.info(f"✅ {result.deleted_count} sessões resetadas para usuário {username}")
                return True
            else:
                logger.warning(f"⚠️ Nenhuma sessão encontrada para resetar para usuário {username}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao resetar sessões do usuário {username}: {e}")
            raise 