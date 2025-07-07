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