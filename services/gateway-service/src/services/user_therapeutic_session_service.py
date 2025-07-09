"""
Serviço de sessões terapêuticas dos usuários - gerencia sessões individuais de cada usuário
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from ..models.database import get_user_therapeutic_sessions_collection, get_therapeutic_sessions_collection
import re

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
    
    async def create_session_1_for_user(self, username: str) -> Dict[str, Any]:
        """Criar automaticamente a session-1 (cadastro) para um usuário"""
        try:
            # Verificar se a session-1 já existe para o usuário
            existing_session = await self.user_sessions_collection.find_one({
                "username": username,
                "session_id": "session-1"
            })
            
            if existing_session:
                logger.info(f"ℹ️ Session-1 já existe para usuário {username}")
                return {
                    "success": True,
                    "created": False,
                    "already_exists": True,
                    "message": "Session-1 já existe para este usuário"
                }
            
            # Criar session-1 automaticamente
            session_1_data = {
                "username": username,
                "session_id": "session-1",
                "template_session_id": "session-1",
                "title": "Cadastro e Apresentação",
                "subtitle": "Vamos nos conhecer melhor",
                "description": "Sessão inicial para coleta de informações pessoais e estabelecimento do vínculo terapêutico",
                "objective": "Coletar informações pessoais do usuário e estabelecer o primeiro contato terapêutico",
                "initial_prompt": "Olá! Eu sou sua assistente terapêutica. É um prazer te conhecer! Para personalizar nossa conversa, vou fazer algumas perguntas sobre você. Primeiro, me conta: qual é a sua idade?",
                "category": "onboarding",
                "difficulty": "beginner",
                "estimated_duration": 30,
                "status": "unlocked",  # Automaticamente desbloqueada
                "progress": 0,
                "completed_at": None,
                "started_at": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
                "is_registration_session": True,  # Flag especial para identificar sessão de cadastro
                "personalized": False  # Esta é a sessão base, não personalizada
            }
            
            # Inserir session-1 no banco
            result = await self.user_sessions_collection.insert_one(session_1_data)
            
            if result.inserted_id:
                logger.info(f"✅ Session-1 criada automaticamente para usuário {username}")
                return {
                    "success": True,
                    "created": True,
                    "already_exists": False,
                    "message": "Session-1 criada com sucesso",
                    "session_id": "session-1"
                }
            else:
                logger.error(f"❌ Falha ao criar session-1 para usuário {username}")
                return {
                    "success": False,
                    "created": False,
                    "already_exists": False,
                    "message": "Erro ao criar session-1"
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar session-1 para usuário {username}: {e}")
            raise

    async def clone_sessions_for_user(self, username: str) -> Dict[str, Any]:
        """
        DESABILITADO: Não cria mais todas as sessões de uma vez.
        Agora as sessões são criadas uma por vez conforme necessário.
        """
        logger.info(f"⚠️ clone_sessions_for_user chamado para {username} - FUNCIONALIDADE DESABILITADA")
        logger.info(f"ℹ️ Sessões agora são criadas uma por vez após completar a anterior")
        
        return {
            "success": True,
            "message": "Sistema de criação gradual (1 a 1) ativado",
            "cloned_count": 0,
            "note": "Sessões são criadas automaticamente uma por vez quando necessário"
        }
    
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
    
    async def complete_session(self, username: str, session_id: str, progress: int = 100, status: str = "completed") -> bool:
        """Marcar uma sessão como concluída para o usuário"""
        try:
            result = await self.user_sessions_collection.update_one(
                {
                    "username": username,
                    "session_id": session_id
                },
                {
                    "$set": {
                        "status": status,
                        "progress": progress,
                        "completed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Sessão {session_id} marcada como '{status}' para usuário {username}")
                return True
            else:
                logger.warning(f"⚠️ Sessão {session_id} não encontrada para usuário {username}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao marcar sessão {session_id} como '{status}' para usuário {username}: {e}")
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
                # Priorizar session-1 se existir e estiver bloqueada
                session_1 = await self.user_sessions_collection.find_one({
                    "username": username,
                    "session_id": "session-1",
                    "status": "locked"
                })
                
                if session_1:
                    result = await self.user_sessions_collection.update_one(
                        {"_id": session_1["_id"]},
                        {
                            "$set": {
                                "status": "unlocked",
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    
                    if result.modified_count > 0:
                        logger.info(f"✅ Session-1 desbloqueada para usuário {username}")
                        return True
                    else:
                        logger.warning(f"⚠️ Não foi possível desbloquear session-1 para {username}")
                        return False
                else:
                    # Se session-1 não existir ou já estiver desbloqueada, buscar a primeira sessão disponível
                    first_session = await self.user_sessions_collection.find_one(
                        {"username": username, "status": "locked"},
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
                            logger.info(f"✅ Primeira sessão desbloqueada para usuário {username}: {first_session['session_id']}")
                            return True
                        else:
                            logger.warning(f"⚠️ Não foi possível desbloquear primeira sessão para {username}")
                            return False
                    else:
                        logger.warning(f"⚠️ Nenhuma sessão bloqueada encontrada para usuário {username}")
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

    async def get_next_session_number(self, username: str) -> int:
        """
        Obter o próximo número de sessão para o usuário
        """
        try:
            # Buscar todas as sessões do usuário
            cursor = self.user_sessions_collection.find(
                {"username": username},
                {"session_id": 1}
            )
            
            session_numbers = []
            async for session in cursor:
                session_id = session.get("session_id", "")
                # Extrair número da sessão (ex: "session-1" -> 1)
                match = re.search(r'session-(\d+)', session_id)
                if match:
                    session_numbers.append(int(match.group(1)))
            
            # Retornar o próximo número disponível
            if session_numbers:
                return max(session_numbers) + 1
            else:
                return 1  # Primeira sessão
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter próximo número de sessão: {e}")
            return 1

    async def create_dynamic_session(self, username: str, session_data: Dict[str, Any]) -> bool:
        """
        Criar sessão dinâmica baseada nos dados fornecidos
        """
        try:
            # Garantir que o session_id esteja presente
            session_id = session_data.get("session_id")
            if not session_id:
                # Gerar session_id automaticamente
                next_number = await self.get_next_session_number(username)
                session_id = f"session-{next_number}"
                session_data["session_id"] = session_id
            
            # Preparar documento para inserção
            session_document = {
                "username": username,
                "session_id": session_id,
                "title": session_data.get("title", "Sessão Terapêutica"),
                "subtitle": session_data.get("subtitle", ""),
                "objective": session_data.get("objective", ""),
                "initial_prompt": session_data.get("initial_prompt", ""),
                "focus_areas": session_data.get("focus_areas", []),
                "therapeutic_approach": session_data.get("therapeutic_approach", "Abordagem centrada na pessoa"),
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
                "status": "locked",
                "progress": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Inserir documento
            result = await self.user_sessions_collection.insert_one(session_document)
            
            if result.inserted_id:
                logger.info(f"✅ Sessão dinâmica criada: {session_id} para {username}")
                return True
            else:
                logger.error(f"❌ Falha ao criar sessão dinâmica: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar sessão dinâmica: {e}")
            return False

    async def get_user_session_sequence(self, username: str) -> List[Dict[str, Any]]:
        """
        Obter sequência ordenada de sessões do usuário
        """
        try:
            cursor = self.user_sessions_collection.find(
                {"username": username},
                sort=[("created_at", 1)]
            )
            
            sessions = []
            async for session in cursor:
                sessions.append({
                    "session_id": session["session_id"],
                    "title": session["title"],
                    "subtitle": session.get("subtitle", ""),
                    "status": session.get("status", "locked"),
                    "progress": session.get("progress", 0),
                    "created_at": session["created_at"],
                    "generation_method": session.get("generation_method", "template"),
                    "personalized": session.get("personalized", False),
                    "based_on_session": session.get("based_on_session"),
                    "connection_to_previous": session.get("connection_to_previous", "")
                })
            
            return sessions
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter sequência de sessões: {e}")
            return []

    async def get_latest_completed_session(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Obter a última sessão completada do usuário
        """
        try:
            cursor = self.user_sessions_collection.find(
                {"username": username, "status": "completed"},
                sort=[("updated_at", -1)],
                limit=1
            )
            
            async for session in cursor:
                return {
                    "session_id": session["session_id"],
                    "title": session["title"],
                    "completed_at": session["updated_at"],
                    "progress": session.get("progress", 0)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter última sessão completada: {e}")
            return None

    async def can_create_next_session(self, username: str) -> bool:
        """
        Verificar se o usuário pode ter uma nova sessão criada
        """
        try:
            # Verificar se há sessões em andamento ou não iniciadas
            pending_sessions = await self.user_sessions_collection.count_documents({
                "username": username,
                "status": {"$in": ["locked", "unlocked", "in_progress"]}
            })
            
            # Só permite criar nova sessão se não houver sessões pendentes
            return pending_sessions == 0
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar se pode criar nova sessão: {e}")
            return False

    async def auto_unlock_next_session(self, username: str) -> bool:
        """
        Desbloquear automaticamente a próxima sessão na sequência
        """
        try:
            # Buscar próxima sessão bloqueada
            next_session = await self.user_sessions_collection.find_one(
                {"username": username, "status": "locked"},
                sort=[("created_at", 1)]
            )
            
            if next_session:
                session_id = next_session["session_id"]
                success = await self.unlock_session(username, session_id)
                if success:
                    logger.info(f"🔓 Próxima sessão desbloqueada automaticamente: {session_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Falha ao desbloquear próxima sessão: {session_id}")
                    return False
            else:
                logger.info(f"ℹ️ Nenhuma sessão bloqueada encontrada para {username}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao desbloquear próxima sessão: {e}")
            return False 