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
        return """Você é o Dr. Rogers, um psicólogo virtual especializado em terapia humanista.
        
SEU PAPEL:
- Oferecer apoio emocional e orientação terapêutica
- Usar técnicas de escuta ativa e empatia
- Focar no bem-estar mental do usuário
- Manter um tom acolhedor e profissional

DIRETRIZES:
1. SEMPRE responda em português brasileiro
2. Seja empático e acolhedor
3. Faça perguntas que estimulem reflexão
4. Evite dar conselhos médicos específicos
5. Se detectar crise, oriente buscar ajuda profissional
6. Mantenha respostas concisas (máximo 3 parágrafos)

ESTRUTURA DE RESPOSTA:
- Reconheça o sentimento expresso
- Demonstre empatia
- Faça uma pergunta reflexiva
- Ofereça apoio

EXEMPLO:
Usuário: "Estou muito triste hoje"
Você: "Entendo que você está passando por um momento difícil. É muito corajoso reconhecer e compartilhar esses sentimentos. Pode me contar mais sobre o que está causando essa tristeza? Estou aqui para te ouvir e apoiar."

Lembre-se: você é um psicólogo virtual, não substitui terapia profissional em casos graves."""
    
    def _create_conversation_context(self, session_id: str, user_message: str, conversation_history: Optional[List[Dict]] = None, session_objective: Optional[Dict[str, Any]] = None, initial_prompt: Optional[str] = None) -> List[Dict]:
        """
        Criar contexto da conversa para o OpenAI com otimização de tokens
        """
        # Criar prompt do sistema baseado no objetivo da sessão
        system_prompt = self._create_system_prompt()
        
        # Se há initial_prompt fornecido diretamente, usá-lo (tem prioridade)
        if initial_prompt:
            enhanced_prompt = f"""
INSTRUÇÕES ESPECÍFICAS PARA ESTA SESSÃO:
{initial_prompt}

{system_prompt}
"""
            system_prompt = enhanced_prompt
        # Se há objetivo da sessão, incorporá-lo no prompt do sistema
        elif session_objective:
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
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Processar histórico com otimizações
        if conversation_history:
            optimized_history = self._optimize_conversation_history(conversation_history)
            
            for msg in optimized_history:
                role = "user" if msg.get("type") == "user" else "assistant"
                content = msg.get("content", "")
                if content.strip():
                    messages.append({"role": role, "content": content})
        
        # Adicionar mensagem atual
        messages.append({"role": "user", "content": user_message})
        
        # Log do tamanho do contexto
        total_tokens = self._estimate_tokens(messages)
        logger.info(f"📊 Contexto: {len(messages)} mensagens, ~{total_tokens} tokens")
        
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
            
        Returns:
            Dict com resposta e metadados
        """
        try:
            # Verificar disponibilidade
            if not self.is_available():
                logger.warning("⚠️ OpenAI não disponível - usando fallback")
                return self._fallback_response(user_message)
            
            # Criar contexto da conversa
            messages = self._create_conversation_context(session_id, user_message, conversation_history, session_objective, initial_prompt)
            
            # Fazer chamada para OpenAI
            response = await self._call_openai(messages)
            
            if response:
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=30
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                logger.warning("⚠️ OpenAI retornou resposta vazia")
                return None
                
        except Exception as e:
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