"""
Serviço de integração com OpenAI para o AI Service
Responsável por gerenciar conversas terapêuticas com GPT
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Import OpenAI com tratamento de erro
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None
    OpenAI = None

# Configurar logging
logger = logging.getLogger(__name__)

class OpenAIService:
    """
    Serviço para integração com OpenAI GPT
    Gerencia conversas terapêuticas com psicólogo Rogers
    """
    
    def __init__(self):
        """Inicializar serviço OpenAI"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("MODEL_NAME", "gpt-4o")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
        # Configurações de contexto
        self.max_history_messages = int(os.getenv("MAX_HISTORY_MESSAGES", "6"))  # Últimas 6 mensagens
        self.max_context_tokens = int(os.getenv("MAX_CONTEXT_TOKENS", "2000"))   # Máximo 2000 tokens de contexto
        self.enable_context_compression = os.getenv("ENABLE_CONTEXT_COMPRESSION", "true").lower() == "true"
        
        # Verificar configuração
        if not self.api_key or not OPENAI_AVAILABLE:
            logger.warning("⚠️ OPENAI_API_KEY não configurada ou OpenAI não disponível - usando modo fallback")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✅ Cliente OpenAI inicializado com sucesso")
            except Exception as e:
                logger.error(f"❌ Erro ao inicializar cliente OpenAI: {e}")
                self.client = None
    
    def is_available(self) -> bool:
        """Verificar se o serviço OpenAI está disponível"""
        return self.client is not None and self.api_key is not None
    
    def _create_system_prompt(self) -> str:
        """
        Criar prompt do sistema para o psicólogo Rogers
        """
        return """DIRETRIZES:
1. SEMPRE responda em português brasileiro"""
    
    def _create_conversation_context(self, session_id: str, user_message: str, conversation_history: Optional[List[Dict]] = None, session_objective: Optional[Dict[str, Any]] = None, initial_prompt: Optional[str] = None) -> List[Dict]:
        """
        Criar contexto da conversa para o OpenAI com otimização de tokens
        """
        # Criar prompt do sistema baseado no objetivo da sessão
        system_prompt = self._create_system_prompt()
        
        # 🔍 Log inicial
        logger.info(f"🎯 Criando contexto para sessão {session_id}")
        
        # Se há initial_prompt fornecido diretamente, usá-lo (tem prioridade)
        if initial_prompt:
            logger.info(f"📋 INITIAL_PROMPT encontrado para sessão {session_id}")
            logger.info(f"📝 Conteúdo do initial_prompt: {initial_prompt[:200]}{'...' if len(initial_prompt) > 200 else ''}")
            
            enhanced_prompt = f"""
INSTRUÇÕES ESPECÍFICAS PARA ESTA SESSÃO:
{initial_prompt}
"""
            system_prompt = enhanced_prompt
            logger.info(f"✅ Prompt do sistema ENHANCED com initial_prompt para sessão {session_id}")
            
        # Se há objetivo da sessão, incorporá-lo no prompt do sistema
        elif session_objective:
            logger.info(f"🎯 SESSION_OBJECTIVE encontrado para sessão {session_id}")
            logger.info(f"📋 Título: {session_objective.get('title', 'N/A')}")
            logger.info(f"📋 Subtítulo: {session_objective.get('subtitle', 'N/A')}")
            logger.info(f"📋 Objetivo: {session_objective.get('objective', 'N/A')[:100]}{'...' if len(session_objective.get('objective', '')) > 100 else ''}")
            
            if session_objective.get('initial_prompt'):
                logger.info(f"📝 Conteúdo do initial_prompt do objective: {session_objective.get('initial_prompt')[:200]}{'...' if len(session_objective.get('initial_prompt', '')) > 200 else ''}")
            
            objective_text = f"""
OBJETIVO DESTA SESSÃO:
Título: {session_objective.get('title', 'Sessão Terapêutica')}
Subtitle: {session_objective.get('subtitle', '')}
Objetivo: {session_objective.get('objective', '')}

INSTRUÇÕES ESPECÍFICAS PARA ESTA SESSÃO:
{session_objective.get('initial_prompt', '')}

{system_prompt}
"""
            system_prompt = objective_text
            logger.info(f"✅ Prompt do sistema ENHANCED com session_objective para sessão {session_id}")
            
        else:
            logger.info(f"📄 Usando prompt do sistema PADRÃO para sessão {session_id}")
        
        # 🔍 Log do prompt do sistema completo (truncado para não poluir logs)
        logger.info(f"🤖 PROMPT DO SISTEMA (primeiros 300 caracteres): {system_prompt[:300]}{'...' if len(system_prompt) > 300 else ''}")
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Processar histórico com otimizações
        if conversation_history:
            logger.info(f"📚 Processando histórico: {len(conversation_history)} mensagens originais")
            optimized_history = self._optimize_conversation_history(conversation_history)
            logger.info(f"📚 Após otimização: {len(optimized_history)} mensagens")
            
            for msg in optimized_history:
                role = "user" if msg.get("type") == "user" else "assistant"
                content = msg.get("content", "")
                if content.strip():
                    messages.append({"role": role, "content": content})
        else:
            logger.info(f"📄 Nenhum histórico fornecido para sessão {session_id}")
        
        # Adicionar mensagem atual
        logger.info(f"💬 Mensagem do usuário: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
        messages.append({"role": "user", "content": user_message})
        
        # Log do tamanho do contexto
        total_tokens = self._estimate_tokens(messages)
        logger.info(f"📊 Contexto FINAL: {len(messages)} mensagens, ~{total_tokens} tokens")
        
        # 🔍 Log resumo das mensagens que serão enviadas para OpenAI
        logger.info(f"📤 RESUMO ENVIADO PARA OPENAI:")
        for i, msg in enumerate(messages):
            role = msg["role"]
            content_preview = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
            logger.info(f"  [{i+1}] {role.upper()}: {content_preview}")
        
        return messages
    
    def _optimize_conversation_history(self, history: List[Dict]) -> List[Dict]:
        """
        Otimizar histórico de conversa para reduzir tokens
        """
        if not history:
            return []
        
        # Limitar número de mensagens
        limited_history = history[-self.max_history_messages:]
        
        # Se habilitado, comprimir contexto longo
        if self.enable_context_compression and len(history) > self.max_history_messages:
            compressed_history = self._compress_long_conversation(history)
            return compressed_history[-self.max_history_messages:]
        
        return limited_history
    
    def _compress_long_conversation(self, history: List[Dict]) -> List[Dict]:
        """
        Comprimir conversa longa mantendo contexto essencial
        """
        if len(history) <= self.max_history_messages:
            return history
        
        # Manter primeiras mensagens (contexto inicial)
        initial_context = history[:2]
        
        # Manter últimas mensagens (contexto recente)
        recent_context = history[-self.max_history_messages+2:]
        
        # Criar resumo do meio se necessário
        middle_context = []
        if len(history) > self.max_history_messages + 2:
            middle_context = [{
                "type": "assistant",
                "content": f"[Resumo: Conversa anterior com {len(history)-self.max_history_messages} mensagens sobre o mesmo tema]"
            }]
        
        return initial_context + middle_context + recent_context
    
    def _estimate_tokens(self, messages: List[Dict]) -> int:
        """
        Estimar número de tokens (aproximação simples)
        """
        total_chars = 0
        for msg in messages:
            total_chars += len(msg.get("content", ""))
        
        # Aproximação: 1 token ≈ 4 caracteres
        return total_chars // 4
    
    async def generate_therapeutic_response(
        self, 
        user_message: str, 
        session_id: str,
        conversation_history: Optional[List[Dict]] = None,
        session_objective: Optional[Dict[str, Any]] = None,
        initial_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gerar resposta terapêutica usando OpenAI
        
        Args:
            user_message: Mensagem do usuário
            session_id: ID da sessão
            conversation_history: Histórico da conversa (opcional)
            session_objective: Objetivo da sessão terapêutica (opcional)
            initial_prompt: Prompt inicial específico (opcional)
            
        Returns:
            Dict com resposta e metadados
        """
        try:
            # 🚀 Log inicial da função
            logger.info(f"🚀 INICIANDO GERAÇÃO DE RESPOSTA TERAPÊUTICA")
            logger.info(f"🎯 Session ID: {session_id}")
            logger.info(f"💬 Mensagem do usuário: {user_message[:150]}{'...' if len(user_message) > 150 else ''}")
            logger.info(f"📚 Histórico fornecido: {'Sim' if conversation_history else 'Não'} ({len(conversation_history) if conversation_history else 0} mensagens)")
            logger.info(f"🎯 Session Objective fornecido: {'Sim' if session_objective else 'Não'}")
            logger.info(f"📋 Initial Prompt fornecido: {'Sim' if initial_prompt else 'Não'}")
            
            # Verificar disponibilidade
            if not self.is_available():
                logger.warning("⚠️ OpenAI não disponível - usando fallback")
                return self._fallback_response(user_message)
            
            logger.info(f"✅ OpenAI disponível - gerando resposta com modelo {self.model}")
            
            # Criar contexto da conversa
            messages = self._create_conversation_context(session_id, user_message, conversation_history, session_objective, initial_prompt)
            
            # Fazer chamada para OpenAI
            logger.info(f"📡 Enviando requisição para OpenAI com {len(messages)} mensagens")
            response = await self._call_openai(messages)
            
            if response:
                logger.info(f"✅ Resposta recebida da OpenAI: {response[:100]}{'...' if len(response) > 100 else ''}")
                return {
                    "response": response,
                    "model": self.model,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "provider": "openai",
                    "success": True
                }
            else:
                logger.error("❌ Falha ao obter resposta da OpenAI")
                return self._fallback_response(user_message)
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resposta terapêutica: {e}")
            return self._fallback_response(user_message)
    
    async def _call_openai(self, messages: List[Dict]) -> Optional[str]:
        """
        Fazer chamada para API da OpenAI
        """
        if not self.client or not OPENAI_AVAILABLE:
            logger.warning("⚠️ Cliente OpenAI não disponível")
            return None
            
        try:
            # 🔍 Log detalhado da chamada OpenAI
            logger.info(f"🤖 CHAMADA PARA API OPENAI:")
            logger.info(f"   Modelo: {self.model}")
            logger.info(f"   Max Tokens: {self.max_tokens}")
            logger.info(f"   Temperatura: {self.temperature}")
            logger.info(f"   Número de mensagens: {len(messages)}")
            
            # Log do sistema prompt (mais detalhado se necessário)
            if messages and len(messages) > 0 and messages[0]["role"] == "system":
                system_content = messages[0]["content"]
                logger.info(f"🎯 SYSTEM PROMPT (primeiros 500 chars): {system_content[:500]}{'...' if len(system_content) > 500 else ''}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=30
            )
            
            if response.choices and len(response.choices) > 0:
                ai_response = response.choices[0].message.content.strip()
                logger.info(f"✅ SUCESSO na chamada OpenAI")
                logger.info(f"📊 Tokens usados: prompt={getattr(response.usage, 'prompt_tokens', 'N/A')}, completion={getattr(response.usage, 'completion_tokens', 'N/A')}, total={getattr(response.usage, 'total_tokens', 'N/A')}")
                logger.info(f"🤖 Resposta da IA (primeiros 200 chars): {ai_response[:200]}{'...' if len(ai_response) > 200 else ''}")
                return ai_response
            else:
                logger.warning("⚠️ OpenAI retornou resposta vazia")
                return None
                
        except Exception as e:
            logger.error(f"❌ ERRO na chamada OpenAI: {e}")
            if openai and hasattr(openai, 'RateLimitError') and isinstance(e, openai.RateLimitError):
                logger.error("❌ Rate limit da OpenAI atingido")
            elif openai and hasattr(openai, 'APIError') and isinstance(e, openai.APIError):
                logger.error(f"❌ Erro da API OpenAI: {e}")
            else:
                logger.error(f"❌ Erro inesperado na chamada OpenAI: {e}")
            return None
    
    def _fallback_response(self, user_message: str) -> Dict[str, Any]:
        """
        Resposta de fallback quando OpenAI não está disponível
        Mantém a lógica atual como backup
        """
        message_lower = user_message.lower()
        
        # Padrões de reconhecimento (mantidos da implementação atual)
        greeting_patterns = ['oi', 'olá', 'hello', 'hi', 'bom dia', 'boa tarde', 'boa noite']
        sadness_patterns = ['triste', 'deprimido', 'depressão', 'mal', 'ruim', 'pessimo', 'horrível']
        anxiety_patterns = ['ansioso', 'ansiedade', 'nervoso', 'preocupado', 'estressado', 'tenso']
        anger_patterns = ['raiva', 'irritado', 'bravo', 'furioso', 'chateado']
        gratitude_patterns = ['obrigado', 'obrigada', 'valeu', 'thanks', 'thank you']
        goodbye_patterns = ['tchau', 'bye', 'adeus', 'até logo', 'até mais']
        
        # Verificar padrões
        if any(pattern in message_lower for pattern in greeting_patterns):
            response = "Olá! Sou o Dr. Rogers, seu psicólogo virtual. É um prazer conhecê-lo. Como posso ajudá-lo hoje? Sinta-se à vontade para compartilhar o que está sentindo."
        elif any(pattern in message_lower for pattern in sadness_patterns):
            response = "Entendo que você está passando por um momento difícil. É muito corajoso buscar ajuda e compartilhar seus sentimentos. Pode me contar mais sobre o que está sentindo? Lembre-se: você não está sozinho, e é normal ter dias difíceis."
        elif any(pattern in message_lower for pattern in anxiety_patterns):
            response = "A ansiedade é algo muito comum e tratável. Vamos trabalhar juntos para encontrar estratégias que funcionem para você. Que situações costumam despertar essa ansiedade? Podemos explorar técnicas de respiração e mindfulness que podem ajudar."
        elif any(pattern in message_lower for pattern in anger_patterns):
            response = "Vejo que você está se sentindo irritado. É importante reconhecer e validar esses sentimentos. Pode me contar o que aconteceu? Às vezes, falar sobre o que nos incomoda pode ajudar a processar melhor essas emoções."
        elif any(pattern in message_lower for pattern in gratitude_patterns):
            response = "Fico muito feliz em poder ajudar! É um prazer acompanhá-lo nessa jornada de autoconhecimento e bem-estar. Como você está se sentindo agora? Há algo mais que gostaria de conversar?"
        elif any(pattern in message_lower for pattern in goodbye_patterns):
            response = "Foi um prazer conversar com você hoje. Lembre-se: estou sempre aqui quando precisar de apoio. Cuide-se bem e continue cuidando da sua saúde mental. Até a próxima! 💙"
        else:
            response = f"Obrigado por compartilhar isso comigo. É importante que você tenha confiança para falar sobre seus sentimentos. Pode me contar mais sobre como isso afeta seu dia a dia? Juntos podemos explorar formas de lidar melhor com essa situação."
        
        return {
            "response": response,
            "model": "fallback",
            "session_id": "default",
            "timestamp": datetime.now().isoformat(),
            "provider": "fallback",
            "success": True
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Retornar status do serviço OpenAI
        """
        return {
            "openai_configured": self.is_available(),
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "api_key_present": bool(self.api_key),
            "context_optimization": {
                "max_history_messages": self.max_history_messages,
                "max_context_tokens": self.max_context_tokens,
                "enable_compression": self.enable_context_compression
            }
        }

    async def generate_session_context(self, conversation_text: str, emotions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gerar contexto estruturado da sessão incluindo resumo e análise
        """
        try:
            # Processar dados de emoções
            emotion_summary = self._process_emotions_data(emotions_data)
            
            # Criar prompt para análise de contexto
            context_prompt = f"""
            Você é um especialista em análise de conversas terapêuticas. Analise a conversa abaixo e forneça um contexto estruturado no formato JSON.

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

            IMPORTANTE: Retorne apenas o JSON, sem texto adicional.
            """
            
            # Gerar contexto com OpenAI
            if self.is_available():
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Você é um especialista em análise de conversas terapêuticas. Sempre responda em JSON válido."},
                        {"role": "user", "content": context_prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.3
                )
                
                result = response.choices[0].message.content
                
                # Tentar parsear JSON
                try:
                    context_data = json.loads(result)
                    
                    # Validar estrutura mínima
                    required_fields = ["summary", "main_themes", "emotional_state", "key_insights"]
                    for field in required_fields:
                        if field not in context_data:
                            context_data[field] = self._get_default_value(field)
                    
                    return context_data
                    
                except json.JSONDecodeError:
                    # Se não conseguir parsear, criar estrutura básica
                    return self._create_fallback_context(result, emotion_summary)
                    
            else:
                # Fallback quando OpenAI não está disponível
                return self._create_fallback_context(conversation_text, emotion_summary)
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar contexto da sessão: {e}")
            # Retornar contexto básico em caso de erro
            return self._create_fallback_context("Erro ao processar conversa", {})

    def _process_emotions_data(self, emotions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Processar dados de emoções para análise"""
        if not emotions_data:
            return {"dominant_emotion": "neutro", "count": 0, "distribution": {}}
        
        # Agregar emoções
        emotion_counts = {}
        total_detections = len(emotions_data)
        
        for emotion in emotions_data:
            dominant = emotion.get("dominant_emotion", "neutro")
            emotion_counts[dominant] = emotion_counts.get(dominant, 0) + 1
        
        # Encontrar emoção dominante
        dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutro"
        
        return {
            "dominant_emotion": dominant_emotion,
            "count": total_detections,
            "distribution": emotion_counts
        }
    
    def _get_default_value(self, field: str) -> Any:
        """Obter valor padrão para campos obrigatórios"""
        defaults = {
            "summary": "Resumo não disponível",
            "main_themes": ["Tema geral"],
            "emotional_state": {
                "dominant_emotion": "neutro",
                "emotional_journey": "Não analisado",
                "stability": "desconhecido"
            },
            "key_insights": ["Análise não disponível"]
        }
        return defaults.get(field, "")
    
    def _create_fallback_context(self, conversation_text: str, emotion_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Criar contexto de fallback quando a IA não está disponível
        """
        return {
            "summary": f"Sessão terapêutica com conversa de aproximadamente {len(conversation_text.split())} palavras",
            "main_themes": ["conversa terapêutica", "apoio emocional"],
            "emotional_state": {
                "dominant_emotion": emotion_summary.get("dominant_emotion", "neutro"),
                "journey": "Processo terapêutico em andamento",
                "stability": "Estável"
            },
            "key_insights": [
                "Usuário engajado no processo terapêutico",
                "Demonstra abertura para o diálogo",
                "Busca apoio emocional"
            ],
            "therapeutic_progress": {
                "engagement_level": "Médio",
                "progress_indicators": ["participação ativa"],
                "areas_of_growth": ["expressão emocional"]
            },
            "next_session_recommendations": [
                "Continuar processo terapêutico",
                "Aprofundar temas identificados"
            ],
            "risk_indicators": [],
            "session_quality_rating": 7,
            "generation_method": "fallback"
        }

    async def generate_next_session(self, user_profile: Dict[str, Any], session_context: Dict[str, Any], current_session_id: str) -> Dict[str, Any]:
        """
        Gerar próxima sessão terapêutica personalizada baseada no contexto do usuário
        """
        try:
            logger.info(f"🎯 Gerando próxima sessão baseada no contexto de {current_session_id}")
            
            # Criar prompt para gerar a próxima sessão
            session_prompt = self._create_next_session_prompt(user_profile, session_context, current_session_id)
            
            # Tentar gerar com OpenAI
            if self.is_available():
                try:
                    messages = [
                        {"role": "system", "content": "Você é um especialista em terapia que cria sessões terapêuticas personalizadas baseadas no contexto do usuário."},
                        {"role": "user", "content": session_prompt}
                    ]
                    
                    ai_response = await self._call_openai(messages)
                    
                    if ai_response:
                        # Parsear resposta JSON
                        import json
                        try:
                            # Extrair JSON da resposta
                            start_idx = ai_response.find('{')
                            end_idx = ai_response.rfind('}') + 1
                            
                            if start_idx >= 0 and end_idx > start_idx:
                                json_str = ai_response[start_idx:end_idx]
                                next_session_data = json.loads(json_str)
                                
                                # Adicionar metadados
                                next_session_data.update({
                                    "generated_at": datetime.now().isoformat(),
                                    "based_on_session": current_session_id,
                                    "generation_method": "openai",
                                    "personalized": True
                                })
                                
                                logger.info(f"✅ Próxima sessão gerada com OpenAI para {current_session_id}")
                                return next_session_data
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"⚠️ Erro ao parsear resposta JSON do OpenAI: {e}")
                            
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao chamar OpenAI para próxima sessão: {e}")
            
            # Fallback: criar sessão baseada em template
            logger.info(f"🔄 Usando fallback para gerar próxima sessão de {current_session_id}")
            return self._create_fallback_next_session(user_profile, session_context, current_session_id)
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar próxima sessão: {e}")
            return self._create_fallback_next_session(user_profile, session_context, current_session_id)

    def _create_next_session_prompt(self, user_profile: Dict[str, Any], session_context: Dict[str, Any], current_session_id: str) -> str:
        """
        Criar prompt para gerar a próxima sessão terapêutica
        """
        # Extrair número da sessão atual
        session_number = self._extract_session_number(current_session_id)
        next_session_number = session_number + 1
        next_session_id = f"session-{next_session_number}"
        
        # Extrair informações relevantes do perfil do usuário
        user_summary = self._extract_user_summary(user_profile)
        
        # Extrair informações relevantes do contexto da sessão
        session_summary = self._extract_session_summary(session_context)
        
        prompt = f"""
GERAÇÃO DE SESSÃO TERAPÊUTICA PERSONALIZADA

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

RESPONDA APENAS COM O JSON, SEM TEXTO ADICIONAL.
"""
        return prompt

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

    def _extract_user_summary(self, user_profile: Dict[str, Any]) -> str:
        """
        Extrair resumo do perfil do usuário
        """
        try:
            summary_parts = []
            
            # Informações pessoais
            personal_info = user_profile.get("personal_info", {})
            if personal_info.get("idade", {}).get("valor"):
                summary_parts.append(f"Idade: {personal_info['idade']['valor']} anos")
            if personal_info.get("genero", {}).get("categoria"):
                summary_parts.append(f"Gênero: {personal_info['genero']['categoria']}")
            if personal_info.get("localizacao", {}).get("formatted"):
                summary_parts.append(f"Localização: {personal_info['localizacao']['formatted']}")
            
            # Informações sociais
            social_info = user_profile.get("social_info", {})
            if social_info.get("ocupacao", {}).get("content"):
                summary_parts.append(f"Ocupação: {social_info['ocupacao']['content'][:100]}")
            
            # Informações terapêuticas
            therapeutic_info = user_profile.get("therapeutic_info", {})
            if therapeutic_info.get("motivacao_terapia", {}).get("content"):
                summary_parts.append(f"Motivação: {therapeutic_info['motivacao_terapia']['content'][:150]}")
            
            # Objetivos identificados
            objectives = therapeutic_info.get("objetivos_identificados", [])
            if objectives:
                summary_parts.append(f"Objetivos: {', '.join(objectives[:3])}")
            
            return "\n".join(summary_parts) if summary_parts else "Informações limitadas do usuário"
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair resumo do usuário: {e}")
            return "Perfil do usuário indisponível"

    def _extract_session_summary(self, session_context: Dict[str, Any]) -> str:
        """
        Extrair resumo do contexto da sessão
        """
        try:
            summary_parts = []
            
            # Resumo geral
            if session_context.get("summary"):
                summary_parts.append(f"Resumo: {session_context['summary']}")
            
            # Temas principais
            main_themes = session_context.get("main_themes", [])
            if main_themes:
                summary_parts.append(f"Temas principais: {', '.join(main_themes)}")
            
            # Estado emocional
            emotional_state = session_context.get("emotional_state", {})
            if emotional_state.get("dominant_emotion"):
                summary_parts.append(f"Estado emocional: {emotional_state.get('progression', 'N/A')}")
            
            # Insights chave
            key_insights = session_context.get("key_insights", [])
            if key_insights:
                summary_parts.append(f"Insights: {'; '.join(key_insights[:3])}")
            
            # Recomendações para próxima sessão
            recommendations = session_context.get("next_session_recommendations", [])
            if recommendations:
                summary_parts.append(f"Recomendações: {'; '.join(recommendations[:3])}")
            
            return "\n".join(summary_parts) if summary_parts else "Contexto da sessão indisponível"
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair resumo da sessão: {e}")
            return "Contexto da sessão indisponível"

    def _create_fallback_next_session(self, user_profile: Dict[str, Any], session_context: Dict[str, Any], current_session_id: str) -> Dict[str, Any]:
        """
        Criar próxima sessão usando fallback quando OpenAI não está disponível
        """
        try:
            session_number = self._extract_session_number(current_session_id)
            next_session_number = session_number + 1
            next_session_id = f"session-{next_session_number}"
            
            # Extrair temas da sessão anterior
            main_themes = session_context.get("main_themes", ["desenvolvimento pessoal"])
            
            # Criar sessão baseada em template
            return {
                "session_id": next_session_id,
                "title": f"Sessão {next_session_number}: Continuando sua jornada",
                "subtitle": "Aprofundando temas identificados na sessão anterior",
                "objective": f"Explorar e aprofundar os temas: {', '.join(main_themes[:2])}",
                "initial_prompt": f"Olá! Como você está se sentindo desde nossa última conversa? Gostaria de continuar explorando os temas que identificamos: {', '.join(main_themes[:2])}.",
                "focus_areas": main_themes[:3] if main_themes else ["autoconhecimento", "bem-estar", "crescimento pessoal"],
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
                "generated_at": datetime.now().isoformat(),
                "based_on_session": current_session_id,
                "generation_method": "fallback_template",
                "personalized": True
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar fallback da próxima sessão: {e}")
            return {
                "session_id": f"session-{self._extract_session_number(current_session_id) + 1}",
                "title": "Próxima sessão terapêutica",
                "subtitle": "Continuando o processo terapêutico",
                "objective": "Dar continuidade ao processo de autoconhecimento",
                "initial_prompt": "Olá! Como você está hoje? Vamos continuar nossa conversa terapêutica.",
                "focus_areas": ["autoconhecimento", "bem-estar emocional"],
                "therapeutic_approach": "Abordagem centrada na pessoa",
                "expected_outcomes": ["Continuidade do processo terapêutico"],
                "session_type": "continuação",
                "estimated_duration": "45-60 minutos",
                "preparation_notes": "Sessão de continuidade",
                "connection_to_previous": "Continuação do processo terapêutico",
                "personalization_factors": ["processo terapêutico"],
                "generated_at": datetime.now().isoformat(),
                "based_on_session": current_session_id,
                "generation_method": "minimal_fallback",
                "personalized": False
            }