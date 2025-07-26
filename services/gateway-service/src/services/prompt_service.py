"""
Serviço de gerenciamento de prompts - gerencia prompts do sistema
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..models.database import get_collection

logger = logging.getLogger(__name__)

class PromptService:
    """Serviço de gerenciamento de prompts com persistência MongoDB"""
    
    def __init__(self):
        self._prompts_collection = None
    
    @property
    def prompts_collection(self):
        """Obter coleção de prompts"""
        if self._prompts_collection is None:
            self._prompts_collection = get_collection("prompts")
        return self._prompts_collection
    
    async def create_prompt(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Criar novo prompt
        
        Args:
            prompt_data: Dados do prompt contendo:
                - prompt_key: Chave única do prompt
                - prompt_type: Tipo do prompt (system, fallback, session_generation, etc.)
                - title: Título do prompt
                - content: Conteúdo do prompt
                - variables: Lista de variáveis disponíveis
                - is_active: Se o prompt está ativo
                - description: Descrição opcional
                - tags: Tags para categorização
        """
        try:
            # Validar dados obrigatórios
            required_fields = ["prompt_key", "prompt_type", "title", "content"]
            for field in required_fields:
                if not prompt_data.get(field):
                    raise ValueError(f"Campo obrigatório não fornecido: {field}")
            
            # Verificar se prompt_key já existe
            existing = await self.prompts_collection.find_one({"prompt_key": prompt_data["prompt_key"]})
            if existing:
                raise ValueError(f"Prompt com chave '{prompt_data['prompt_key']}' já existe")
            
            # Preparar documento do prompt
            prompt_document = {
                "prompt_key": prompt_data["prompt_key"],
                "prompt_type": prompt_data["prompt_type"],
                "title": prompt_data["title"],
                "content": prompt_data["content"],
                "variables": prompt_data.get("variables", []),
                "is_active": prompt_data.get("is_active", True),
                "description": prompt_data.get("description", ""),
                "tags": prompt_data.get("tags", []),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "version": 1
            }
            
            # Inserir prompt
            result = await self.prompts_collection.insert_one(prompt_document)
            prompt_document["_id"] = str(result.inserted_id)
            
            logger.info(f"✅ Prompt criado: {prompt_data['prompt_key']}")
            return {
                "success": True,
                "prompt": prompt_document
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar prompt: {e}")
            raise
    
    async def get_prompt(self, prompt_key: str) -> Optional[Dict[str, Any]]:
        """
        Buscar prompt por chave
        
        Args:
            prompt_key: Chave única do prompt
        """
        try:
            prompt = await self.prompts_collection.find_one({"prompt_key": prompt_key})
            
            if prompt:
                prompt["_id"] = str(prompt["_id"])
                logger.info(f"✅ Prompt encontrado: {prompt_key}")
                return prompt
            else:
                logger.warning(f"⚠️ Prompt não encontrado: {prompt_key}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar prompt: {e}")
            return None
    
    async def get_active_prompt(self, prompt_key: str) -> Optional[Dict[str, Any]]:
        """
        Buscar prompt ativo por chave
        
        Args:
            prompt_key: Chave única do prompt
        """
        try:
            prompt = await self.prompts_collection.find_one({
                "prompt_key": prompt_key,
                "is_active": True
            })
            
            if prompt:
                prompt["_id"] = str(prompt["_id"])
                logger.info(f"✅ Prompt ativo encontrado: {prompt_key}")
                return prompt
            else:
                logger.warning(f"⚠️ Prompt ativo não encontrado: {prompt_key}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar prompt ativo: {e}")
            return None
    
    async def update_prompt(self, prompt_key: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualizar prompt existente
        
        Args:
            prompt_key: Chave única do prompt
            update_data: Dados para atualização
        """
        try:
            # Verificar se prompt existe
            existing = await self.prompts_collection.find_one({"prompt_key": prompt_key})
            if not existing:
                raise ValueError(f"Prompt com chave '{prompt_key}' não encontrado")
            
            # Preparar dados de atualização
            update_fields = {}
            
            # Campos que podem ser atualizados
            updatable_fields = ["title", "content", "variables", "is_active", "description", "tags"]
            for field in updatable_fields:
                if field in update_data:
                    update_fields[field] = update_data[field]
            
            # Sempre atualizar timestamp e versão
            update_fields["updated_at"] = datetime.utcnow()
            update_fields["version"] = existing.get("version", 1) + 1
            
            # Atualizar prompt
            result = await self.prompts_collection.update_one(
                {"prompt_key": prompt_key},
                {"$set": update_fields}
            )
            
            if result.modified_count > 0:
                updated_prompt = await self.get_prompt(prompt_key)
                logger.info(f"✅ Prompt atualizado: {prompt_key}")
                return {
                    "success": True,
                    "prompt": updated_prompt
                }
            else:
                logger.warning(f"⚠️ Nenhuma modificação feita no prompt: {prompt_key}")
                return {
                    "success": False,
                    "message": "Nenhuma modificação foi feita"
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar prompt: {e}")
            raise
    
    async def delete_prompt(self, prompt_key: str) -> Dict[str, Any]:
        """
        Deletar prompt (soft delete - marca como inativo)
        
        Args:
            prompt_key: Chave única do prompt
        """
        try:
            # Verificar se prompt existe
            existing = await self.prompts_collection.find_one({"prompt_key": prompt_key})
            if not existing:
                raise ValueError(f"Prompt com chave '{prompt_key}' não encontrado")
            
            # Soft delete - marcar como inativo
            result = await self.prompts_collection.update_one(
                {"prompt_key": prompt_key},
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.utcnow(),
                        "deleted_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Prompt deletado (soft delete): {prompt_key}")
                return {
                    "success": True,
                    "message": f"Prompt '{prompt_key}' foi desativado com sucesso"
                }
            else:
                return {
                    "success": False,
                    "message": "Nenhuma modificação foi feita"
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao deletar prompt: {e}")
            raise
    
    async def list_prompts(self, prompt_type: Optional[str] = None, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Listar prompts com filtros opcionais
        
        Args:
            prompt_type: Tipo de prompt para filtrar
            active_only: Se deve retornar apenas prompts ativos
        """
        try:
            # Construir filtros
            filters = {}
            
            if prompt_type:
                filters["prompt_type"] = prompt_type
            
            if active_only:
                filters["is_active"] = True
            
            # Buscar prompts
            cursor = self.prompts_collection.find(filters).sort("created_at", -1)
            prompts = []
            
            async for prompt in cursor:
                prompt["_id"] = str(prompt["_id"])
                prompts.append(prompt)
            
            logger.info(f"✅ Listando {len(prompts)} prompts (tipo: {prompt_type or 'todos'}, ativos: {active_only})")
            return prompts
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar prompts: {e}")
            return []
    
    async def get_prompts_by_type(self, prompt_type: str) -> List[Dict[str, Any]]:
        """
        Buscar todos os prompts ativos de um tipo específico
        
        Args:
            prompt_type: Tipo de prompt
        """
        try:
            return await self.list_prompts(prompt_type=prompt_type, active_only=True)
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar prompts por tipo: {e}")
            return []
    
    async def render_prompt(self, prompt_key: str, variables: Dict[str, Any]) -> Optional[str]:
        """
        Renderizar prompt com variáveis
        
        Args:
            prompt_key: Chave única do prompt
            variables: Variáveis para substituir no prompt
        """
        try:
            # Buscar prompt
            prompt = await self.get_active_prompt(prompt_key)
            if not prompt:
                return None
            
            # Renderizar prompt com variáveis
            rendered_content = prompt["content"]
            
            # Substituir variáveis no formato {variavel}
            for var_name, var_value in variables.items():
                placeholder = f"{{{var_name}}}"
                rendered_content = rendered_content.replace(placeholder, str(var_value))
            
            logger.info(f"✅ Prompt renderizado: {prompt_key}")
            return rendered_content
            
        except Exception as e:
            logger.error(f"❌ Erro ao renderizar prompt: {e}")
            return None
    
    async def get_prompt_stats(self) -> Dict[str, Any]:
        """
        Obter estatísticas dos prompts
        """
        try:
            # Contar prompts por tipo
            pipeline = [
                {
                    "$group": {
                        "_id": "$prompt_type",
                        "total": {"$sum": 1},
                        "active": {"$sum": {"$cond": [{"$eq": ["$is_active", True]}, 1, 0]}},
                        "inactive": {"$sum": {"$cond": [{"$eq": ["$is_active", False]}, 1, 0]}}
                    }
                }
            ]
            
            type_stats = []
            async for stat in self.prompts_collection.aggregate(pipeline):
                type_stats.append(stat)
            
            # Contar total de prompts
            total_prompts = await self.prompts_collection.count_documents({})
            active_prompts = await self.prompts_collection.count_documents({"is_active": True})
            inactive_prompts = await self.prompts_collection.count_documents({"is_active": False})
            
            # Contar por tipos específicos (para o frontend)
            system_prompts = await self.prompts_collection.count_documents({"prompt_type": "system"})
            fallback_prompts = await self.prompts_collection.count_documents({"prompt_type": "fallback"})
            session_generation_prompts = await self.prompts_collection.count_documents({"prompt_type": "session_generation"})
            analysis_prompts = await self.prompts_collection.count_documents({"prompt_type": "analysis"})
            
            return {
                "total_prompts": total_prompts,
                "active_prompts": active_prompts,
                "inactive_prompts": inactive_prompts,
                "system_prompts": system_prompts,
                "fallback_prompts": fallback_prompts,
                "session_generation_prompts": session_generation_prompts,
                "analysis_prompts": analysis_prompts,
                "by_type": type_stats
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas de prompts: {e}")
            return {
                "total_prompts": 0,
                "active_prompts": 0,
                "inactive_prompts": 0,
                "system_prompts": 0,
                "fallback_prompts": 0,
                "session_generation_prompts": 0,
                "analysis_prompts": 0,
                "by_type": []
            }
    
    async def create_default_prompts(self) -> Dict[str, Any]:
        """
        Criar prompts padrão do sistema
        """
        try:
            default_prompts = [
                {
                    "prompt_key": "system_rogers",
                    "prompt_type": "system",
                    "title": "Prompt de Sistema - Dr. Rogers",
                    "description": "Prompt principal do sistema para o psicólogo virtual Dr. Rogers",
                    "content": """DIRETRIZES:
1. SEMPRE responda em português brasileiro
2. Você é o Dr. Rogers, um psicólogo virtual empático e acolhedor
3. Use abordagem centrada na pessoa (Carl Rogers)
4. Seja sempre empático, respeitoso e profissional
5. Encoraje o usuário a expressar seus sentimentos
6. Não ofereça diagnósticos médicos ou prescrições
7. Mantenha o foco na escuta ativa e reflexão
8. Adapte sua linguagem ao contexto emocional do usuário
9. Use linguagem masculina (ex: "Fico feliz", "Estou aqui", "Sou grato")

CONTEXTO:
- Você está conduzindo uma sessão de terapia virtual
- O usuário busca apoio emocional e psicológico
- Mantenha um ambiente seguro e acolhedor
- Priorize a validação dos sentimentos do usuário
- Use sempre a primeira pessoa no masculino""",
                    "variables": ["username", "session_id", "user_context", "previous_session_info"],
                    "tags": ["sistema", "rogers", "terapia", "principal"],
                    "is_active": True
                },
                {
                    "prompt_key": "fallback_greeting",
                    "prompt_type": "fallback",
                    "title": "Resposta de Fallback - Saudação",
                    "description": "Resposta automática para saudações quando OpenAI não está disponível",
                    "content": "Olá! Sou o Dr. Rogers, seu psicólogo virtual. É um prazer conhecê-lo. Como posso ajudá-lo hoje? Sinta-se à vontade para compartilhar o que está sentindo.",
                    "variables": ["username"],
                    "tags": ["fallback", "saudacao", "rogers"],
                    "is_active": True
                },
                {
                    "prompt_key": "fallback_sadness",
                    "prompt_type": "fallback",
                    "title": "Resposta de Fallback - Tristeza",
                    "description": "Resposta automática para expressões de tristeza quando OpenAI não está disponível",
                    "content": "Entendo que você está passando por um momento difícil. É muito corajoso buscar ajuda e compartilhar seus sentimentos. Pode me contar mais sobre o que está sentindo? Lembre-se: você não está sozinho, e é normal ter dias difíceis.",
                    "variables": ["username"],
                    "tags": ["fallback", "tristeza", "suporte"],
                    "is_active": True
                },
                {
                    "prompt_key": "fallback_anxiety",
                    "prompt_type": "fallback",
                    "title": "Resposta de Fallback - Ansiedade",
                    "description": "Resposta automática para expressões de ansiedade quando OpenAI não está disponível",
                    "content": "A ansiedade é algo muito comum e tratável. Vamos trabalhar juntos para encontrar estratégias que funcionem para você. Que situações costumam despertar essa ansiedade? Podemos explorar técnicas de respiração e mindfulness que podem ajudar.",
                    "variables": ["username"],
                    "tags": ["fallback", "ansiedade", "tecnicas"],
                    "is_active": True
                },
                {
                    "prompt_key": "fallback_anger",
                    "prompt_type": "fallback",
                    "title": "Resposta de Fallback - Raiva",
                    "description": "Resposta automática para expressões de raiva quando OpenAI não está disponível",
                    "content": "Vejo que você está se sentindo irritado. É importante reconhecer e validar esses sentimentos. Pode me contar o que aconteceu? Às vezes, falar sobre o que nos incomoda pode ajudar a processar melhor essas emoções.",
                    "variables": ["username"],
                    "tags": ["fallback", "raiva", "validacao"],
                    "is_active": True
                },
                {
                    "prompt_key": "fallback_gratitude",
                    "prompt_type": "fallback",
                    "title": "Resposta de Fallback - Gratidão",
                    "description": "Resposta automática para expressões de gratidão quando OpenAI não está disponível",
                    "content": "Fico muito feliz em poder ajudar! É um prazer acompanhá-lo nessa jornada de autoconhecimento e bem-estar. Como você está se sentindo agora? Há algo mais que gostaria de conversar?",
                    "variables": ["username"],
                    "tags": ["fallback", "gratidao", "bem-estar"],
                    "is_active": True
                },
                {
                    "prompt_key": "fallback_goodbye",
                    "prompt_type": "fallback",
                    "title": "Resposta de Fallback - Despedida",
                    "description": "Resposta automática para despedidas quando OpenAI não está disponível",
                    "content": "Foi um prazer conversar com você hoje. Lembre-se: estou sempre aqui quando precisar de apoio. Cuide-se bem e continue cuidando da sua saúde mental. Até a próxima! 💙",
                    "variables": ["username"],
                    "tags": ["fallback", "despedida", "suporte"],
                    "is_active": True
                },
                {
                    "prompt_key": "fallback_default",
                    "prompt_type": "fallback",
                    "title": "Resposta de Fallback - Padrão",
                    "description": "Resposta automática padrão quando OpenAI não está disponível e não há padrão específico",
                    "content": "Obrigado por compartilhar isso comigo. É importante que você tenha confiança para falar sobre seus sentimentos. Pode me contar mais sobre como isso afeta seu dia a dia? Juntos podemos explorar formas de lidar melhor com essa situação.",
                    "variables": ["username"],
                    "tags": ["fallback", "padrao", "suporte"],
                    "is_active": True
                },
                {
                    "prompt_key": "session_context_analysis",
                    "prompt_type": "session_generation",
                    "title": "Análise de Contexto de Sessão",
                    "description": "Prompt para gerar análise estruturada de contexto de sessão terapêutica",
                    "content": """Você é um especialista em análise de conversas terapêuticas. Analise a conversa abaixo e forneça um contexto estruturado no formato JSON.

CONVERSA:
{conversation_text}

DADOS EMOCIONAIS:
{emotion_summary}

Por favor, retorne um JSON com:
{{
    "summary": "Resumo conciso da conversa (max 200 palavras)",
    "main_themes": ["tema1", "tema2", "tema3"],
    "emotional_state": {{
        "dominant_emotion": "emoção_dominante",
        "emotional_journey": "descrição da jornada emocional",
        "stability": "estável|instável|em_transição"
    }},
    "key_insights": ["insight1", "insight2", "insight3"],
    "therapeutic_progress": {{
        "engagement_level": "alto|médio|baixo",
        "communication_style": "descrição do estilo de comunicação",
        "areas_of_focus": ["área1", "área2"]
    }},
    "next_session_recommendations": ["recomendação1", "recomendação2"],
    "risk_indicators": ["indicador1", "indicador2"] ou [],
    "session_quality": "excelente|boa|regular|precisa_atenção"
}}

IMPORTANTE: Retorne apenas o JSON, sem texto adicional.""",
                    "variables": ["conversation_text", "emotion_summary"],
                    "tags": ["sessao", "analise", "contexto", "json"],
                    "is_active": True
                },
                {
                    "prompt_key": "next_session_generation",
                    "prompt_type": "session_generation",
                    "title": "Geração de Próxima Sessão",
                    "description": "Prompt para gerar próxima sessão terapêutica personalizada",
                    "content": """GERAÇÃO DE SESSÃO TERAPÊUTICA PERSONALIZADA

Você é um terapeuta experiente criando a próxima sessão terapêutica personalizada para um usuário.

SESSÃO ATUAL: {current_session_id}
PRÓXIMA SESSÃO: {next_session_id}

PERFIL DO USUÁRIO:
{user_summary}

CONTEXTO DA SESSÃO ANTERIOR:
{session_summary}

INSTRUÇÕES:
1. Crie uma sessão terapêutica personalizada baseada no perfil do usuário e contexto da sessão anterior
2. Considere os temas principais identificados na sessão anterior
3. Leve em conta o estado emocional e progresso do usuário
4. Defina objetivos específicos para a próxima sessão
5. Crie um prompt inicial que seja acolhedor e direcionado

RESPONDA EM FORMATO JSON com as seguintes chaves:
{{
  "session_id": "{next_session_id}",
  "title": "Título da sessão (máximo 60 caracteres)",
  "subtitle": "Subtítulo explicativo (máximo 100 caracteres)",
  "objective": "Objetivo principal da sessão (máximo 200 caracteres)",
  "initial_prompt": "Prompt inicial personalizado para iniciar a sessão (máximo 500 caracteres)",
  "focus_areas": ["área1", "área2", "área3"],
  "therapeutic_approach": "Abordagem terapêutica recomendada",
  "expected_outcomes": ["resultado1", "resultado2", "resultado3"],
  "session_type": "individual|continuação|aprofundamento",
  "estimated_duration": "45-60 minutos",
  "preparation_notes": "Notas de preparação para o terapeuta",
  "connection_to_previous": "Como esta sessão se conecta com a anterior",
  "personalization_factors": ["fator1", "fator2", "fator3"]
}}

RESPONDA APENAS COM O JSON, SEM TEXTO ADICIONAL.""",
                    "variables": ["current_session_id", "next_session_id", "user_summary", "session_summary"],
                    "tags": ["sessao", "geracao", "personalizacao", "json"],
                    "is_active": True
                }
            ]
            
            created_count = 0
            for prompt_data in default_prompts:
                try:
                    # Verificar se já existe
                    existing = await self.prompts_collection.find_one({"prompt_key": prompt_data["prompt_key"]})
                    if not existing:
                        await self.create_prompt(prompt_data)
                        created_count += 1
                    else:
                        logger.info(f"📋 Prompt já existe: {prompt_data['prompt_key']}")
                except Exception as e:
                    logger.error(f"❌ Erro ao criar prompt padrão {prompt_data['prompt_key']}: {e}")
            
            logger.info(f"✅ Criados {created_count} prompts padrão")
            return {
                "success": True,
                "created_count": created_count,
                "total_prompts": len(default_prompts)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar prompts padrão: {e}")
            raise 