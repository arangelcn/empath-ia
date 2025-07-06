from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime
import re
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar app FastAPI
app = FastAPI(
    title="empatIA AI Service",
    description="Serviço de IA para conversas terapêuticas com psicólogo Rogers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_therapeutic_response(user_message: str) -> str:
    """
    Gera resposta terapêutica baseada na mensagem do usuário
    """
    message_lower = user_message.lower()
    
    # Padrões de reconhecimento
    greeting_patterns = ['oi', 'olá', 'hello', 'hi', 'bom dia', 'boa tarde', 'boa noite']
    sadness_patterns = ['triste', 'deprimido', 'depressão', 'mal', 'ruim', 'pessimo', 'horrível']
    anxiety_patterns = ['ansioso', 'ansiedade', 'nervoso', 'preocupado', 'estressado', 'tenso']
    anger_patterns = ['raiva', 'irritado', 'bravo', 'furioso', 'chateado']
    gratitude_patterns = ['obrigado', 'obrigada', 'valeu', 'thanks', 'thank you']
    goodbye_patterns = ['tchau', 'bye', 'adeus', 'até logo', 'até mais']
    
    # Verificar padrões
    if any(pattern in message_lower for pattern in greeting_patterns):
        return "Olá! Sou o Dr. Rogers, seu psicólogo virtual. É um prazer conhecê-lo. Como posso ajudá-lo hoje? Sinta-se à vontade para compartilhar o que está sentindo."
    
    elif any(pattern in message_lower for pattern in sadness_patterns):
        return "Entendo que você está passando por um momento difícil. É muito corajoso buscar ajuda e compartilhar seus sentimentos. Pode me contar mais sobre o que está sentindo? Lembre-se: você não está sozinho, e é normal ter dias difíceis."
    
    elif any(pattern in message_lower for pattern in anxiety_patterns):
        return "A ansiedade é algo muito comum e tratável. Vamos trabalhar juntos para encontrar estratégias que funcionem para você. Que situações costumam despertar essa ansiedade? Podemos explorar técnicas de respiração e mindfulness que podem ajudar."
    
    elif any(pattern in message_lower for pattern in anger_patterns):
        return "Vejo que você está se sentindo irritado. É importante reconhecer e validar esses sentimentos. Pode me contar o que aconteceu? Às vezes, falar sobre o que nos incomoda pode ajudar a processar melhor essas emoções."
    
    elif any(pattern in message_lower for pattern in gratitude_patterns):
        return "Fico muito feliz em poder ajudar! É um prazer acompanhá-lo nessa jornada de autoconhecimento e bem-estar. Como você está se sentindo agora? Há algo mais que gostaria de conversar?"
    
    elif any(pattern in message_lower for pattern in goodbye_patterns):
        return "Foi um prazer conversar com você hoje. Lembre-se: estou sempre aqui quando precisar de apoio. Cuide-se bem e continue cuidando da sua saúde mental. Até a próxima! 💙"
    
    else:
        # Resposta genérica mais terapêutica
        return f"Obrigado por compartilhar isso comigo. É importante que você tenha confiança para falar sobre seus sentimentos. Pode me contar mais sobre como isso afeta seu dia a dia? Juntos podemos explorar formas de lidar melhor com essa situação."

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-service",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "empatIA AI Service",
        "description": "Serviço de IA para conversas terapêuticas",
        "docs": "/docs"
    }

# Importar serviço OpenAI
from .services.openai_service import OpenAIService

# Inicializar serviço OpenAI
openai_service = OpenAIService()

# Chat endpoint (melhorado)
@app.post("/chat")
async def chat(message: dict):
    """
    Endpoint principal para conversas de chat
    """
    user_message = message.get("message", "")
    session_id = message.get("session_id", "default")
    conversation_history = message.get("conversation_history", None)
    session_objective = message.get("session_objective", None)
    
    try:
        # Usar OpenAI se disponível, senão fallback
        result = await openai_service.generate_therapeutic_response(
            user_message=user_message,
            session_id=session_id,
            conversation_history=conversation_history,
            session_objective=session_objective
        )
        
        return {
            "response": result["response"],
            "service": "ai-service",
            "status": "active",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "provider": result.get("provider", "fallback"),
            "model": result.get("model", "fallback")
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no chat: {e}")
        # Fallback para resposta básica
        response_text = generate_therapeutic_response(user_message)
        return {
            "response": response_text,
            "service": "ai-service",
            "status": "active",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "provider": "fallback",
            "model": "fallback"
        }

# Endpoint para configurações
@app.get("/config")
async def get_config():
    """Retorna configurações do serviço"""
    openai_status = openai_service.get_service_status()
    
    return {
        "openai_configured": openai_status["openai_configured"],
        "model": openai_status["model"],
        "service_port": os.getenv("AI_SERVICE_PORT", "8001"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "provider": "openai" if openai_status["openai_configured"] else "fallback"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 