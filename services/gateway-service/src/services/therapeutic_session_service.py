"""
Serviço de sessões terapêuticas - gerencia sessões terapêuticas
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from ..models.database import get_therapeutic_sessions_collection

logger = logging.getLogger(__name__)

class TherapeuticSessionService:
    """Serviço de sessões terapêuticas com persistência MongoDB"""
    
    def __init__(self):
        self._sessions_collection = None
    
    @property
    def sessions_collection(self):
        if self._sessions_collection is None:
            self._sessions_collection = get_therapeutic_sessions_collection()
        return self._sessions_collection
    
    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Criar nova sessão terapêutica"""
        try:
            # Verificar se sessão já existe
            existing_session = await self.sessions_collection.find_one({"session_id": session_data["session_id"]})
            if existing_session:
                raise ValueError(f"Sessão '{session_data['session_id']}' já existe")
            
            # Adicionar timestamps
            session_data.update({
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            result = await self.sessions_collection.insert_one(session_data)
            session_data["_id"] = result.inserted_id
            
            logger.info(f"🆕 Sessão terapêutica criada: {session_data['session_id']}")
            return {
                "success": True,
                "data": {
                    "id": str(result.inserted_id),
                    "session_id": session_data["session_id"],
                    "message": "Sessão terapêutica criada com sucesso"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar sessão terapêutica: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obter sessão terapêutica por ID"""
        try:
            session = await self.sessions_collection.find_one({"session_id": session_id})
            if session:
                session["_id"] = str(session["_id"])
            return session
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter sessão terapêutica: {e}")
            raise
    
    async def list_sessions(self, limit: int = 50, offset: int = 0, 
                           active_only: bool = False, search: Optional[str] = None) -> Dict[str, Any]:
        """Listar sessões terapêuticas com filtros"""
        try:
            # Construir filtro
            filter_query = {}
            if active_only:
                filter_query["is_active"] = True
            if search:
                filter_query["$or"] = [
                    {"title": {"$regex": search, "$options": "i"}},
                    {"subtitle": {"$regex": search, "$options": "i"}},
                    {"session_id": {"$regex": search, "$options": "i"}}
                ]
            
            # Obter sessões com paginação
            cursor = self.sessions_collection.find(filter_query).sort("created_at", -1).skip(offset).limit(limit)
            sessions = await cursor.to_list(length=limit)
            
            # Contar total para paginação
            total = await self.sessions_collection.count_documents(filter_query)
            
            # Formatar dados
            formatted_sessions = []
            for session in sessions:
                formatted_sessions.append({
                    "id": str(session["_id"]),
                    "session_id": session["session_id"],
                    "title": session["title"],
                    "subtitle": session["subtitle"],
                    "objective": session["objective"],
                    "initial_prompt": session["initial_prompt"],
                    "is_active": session["is_active"],
                    "created_at": session["created_at"].isoformat(),
                    "updated_at": session["updated_at"].isoformat()
                })
            
            return {
                "success": True,
                "data": {
                    "sessions": formatted_sessions,
                    "pagination": {
                        "total": total,
                        "limit": limit,
                        "offset": offset,
                        "has_next": offset + limit < total
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar sessões terapêuticas: {e}")
            raise
    
    async def update_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Atualizar sessão terapêutica"""
        try:
            # Verificar se a sessão existe
            existing = await self.sessions_collection.find_one({"session_id": session_id})
            if not existing:
                raise ValueError(f"Sessão '{session_id}' não encontrada")
            
            # Adicionar timestamp de atualização
            update_data["updated_at"] = datetime.utcnow()
            
            # Atualizar sessão
            result = await self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Sessão terapêutica atualizada: {session_id}")
                return True
            else:
                logger.warning(f"⚠️ Nenhuma alteração feita na sessão: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar sessão terapêutica: {e}")
            raise
    
    async def delete_session(self, session_id: str) -> bool:
        """Deletar sessão terapêutica"""
        try:
            # Verificar se a sessão existe
            existing = await self.sessions_collection.find_one({"session_id": session_id})
            if not existing:
                raise ValueError(f"Sessão '{session_id}' não encontrada")
            
            # Deletar sessão
            result = await self.sessions_collection.delete_one({"session_id": session_id})
            
            if result.deleted_count > 0:
                logger.info(f"✅ Sessão terapêutica deletada: {session_id}")
                return True
            else:
                logger.warning(f"⚠️ Erro ao deletar sessão: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao deletar sessão terapêutica: {e}")
            raise
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Obter estatísticas das sessões terapêuticas"""
        try:
            total_sessions = await self.sessions_collection.count_documents({})
            active_sessions = await self.sessions_collection.count_documents({"is_active": True})
            inactive_sessions = await self.sessions_collection.count_documents({"is_active": False})
            
            # Sessões criadas nos últimos 7 dias
            last_7_days = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            last_7_days = last_7_days.replace(day=last_7_days.day - 7)
            
            recent_sessions = await self.sessions_collection.count_documents({
                "created_at": {"$gte": last_7_days}
            })
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "inactive_sessions": inactive_sessions,
                "recent_sessions": recent_sessions,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas das sessões: {e}")
            raise
    
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Obter apenas sessões ativas"""
        try:
            cursor = self.sessions_collection.find({"is_active": True}).sort("title", 1)
            sessions = await cursor.to_list(length=None)
            
            formatted_sessions = []
            for session in sessions:
                formatted_sessions.append({
                    "id": str(session["_id"]),
                    "session_id": session["session_id"],
                    "title": session["title"],
                    "subtitle": session["subtitle"],
                    "objective": session["objective"],
                    "initial_prompt": session["initial_prompt"]
                })
            
            return formatted_sessions
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter sessões ativas: {e}")
            raise 