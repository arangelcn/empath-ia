"""
Service responsible for session context generation and retrieval.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import httpx

from ..models.database import get_collection

logger = logging.getLogger(__name__)


class SessionContextService:
    """Encapsulates all session-context logic extracted from ChatService."""

    def __init__(
        self,
        ai_service_url: str,
        conversation_repo,
        resolve_ref,
        extract_username,
        split_session_id,
        next_session_service,
    ):
        self.ai_service_url = ai_service_url
        self._repo = conversation_repo
        self._resolve_ref = resolve_ref
        self._extract_username = extract_username
        self._split_session_id = split_session_id
        self._next_session_service = next_session_service

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    async def finalize_session_context(self, session_id: str, manual_termination: bool = False) -> Dict[str, Any]:
        """
        Finalizar sessão e gerar contexto/resumo da conversa
        """
        try:
            identity = await self._resolve_ref(session_id)
            session_id = identity.get("legacy_session_id") or session_id
            logger.info(f"🎯 FINALIZANDO CONTEXTO DA SESSÃO: {session_id}")

            # Verificar se a sessão existe
            conversation = await self._repo.get_by_session_id(session_id)
            if not conversation:
                logger.warning(f"⚠️ Conversa não encontrada para contexto: {session_id}")
                return {"success": False, "error": "Conversa não encontrada"}

            # Verificar se já foi finalizada
            if conversation.get("session_context"):
                logger.info(f"✅ Sessão já possui contexto: {session_id}")
                next_session_result = await self._next_session_service.create_next_session_automatically(
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
            history_data = await self._repo.get_history(session_id)
            messages = history_data.get("history", [])

            # ✅ CORREÇÃO: Para session-1 (cadastro), aceitar qualquer quantidade de mensagens
            # pois pode ser finalizada antes de completar todo o questionário
            # A session-1 tem lógica especial: dados de cadastro em registration_data + contexto normal
            _, original_session_id = self._split_session_id(session_id)
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
                    username = self._extract_username(session_id)

                    # Criar documento para session_contexts
                    context_document = {
                        "session_id": session_id,
                        "username": username,
                        "context": context_data,
                        "conversation_text": self._format_conversation_for_analysis(
                            (await self._repo.get_history(session_id)).get("history", [])
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
                    next_session_result = await self._next_session_service.create_next_session_automatically(session_id, context_data)

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

    async def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obter contexto salvo de uma sessão - busca na coleção session_contexts
        """
        try:
            identity = await self._resolve_ref(session_id)
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
                conversation = await self._repo.get_by_session_id(session_id)

                if conversation and conversation.get("session_context"):
                    logger.info(f"✅ Contexto encontrado via fallback em conversations: {session_id}")
                    return conversation["session_context"]
                else:
                    logger.warning(f"⚠️ Contexto não encontrado para sessão: {session_id}")
                    return None

        except Exception as e:
            logger.error(f"❌ Erro ao obter contexto da sessão {session_id}: {e}")
            return None

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

    async def get_previous_context(self, current_session_id: str) -> Optional[Dict[str, Any]]:
        """
        Buscar contexto da sessão anterior para enviar ao AI Service
        """
        try:
            # Extrair username e número da sessão atual
            username = self._extract_username(current_session_id)
            if not username:
                return None

            current_session_number = self._next_session_service.extract_session_number(current_session_id)
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

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

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
            history_data = await self._repo.get_history(session_id)
            messages = history_data.get("history", [])

            # Converter mensagens para texto de conversa
            conversation_text = self._format_conversation_for_analysis(messages)

            # Extrair username do session_id
            username = self._extract_username(session_id)

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
            _, original_session_id = self._split_session_id(session_id)
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
