"""
Endpoints para integração com OpenAI
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from ..services.openai_service import OpenAIService

# Configurar logging
logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(prefix="/openai", tags=["OpenAI"])

# Inicializar serviço
openai_service = OpenAIService()

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    conversation_history: Optional[List[Dict[str, Any]]] = None

class ChatResponse(BaseModel):
    response: str
    model: str
    session_id: str
    timestamp: str
    provider: str
    success: bool

@router.post("/chat", response_model=ChatResponse)
async def chat_with_openai(request: ChatRequest):
    """
    Endpoint para conversa com OpenAI
    """
    try:
        result = await openai_service.generate_therapeutic_response(
            user_message=request.message,
            session_id=request.session_id,
            conversation_history=request.conversation_history
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Erro no endpoint OpenAI chat: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.get("/status")
async def get_openai_status():
    """
    Verificar status do serviço OpenAI
    """
    try:
        status = openai_service.get_service_status()
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        logger.error(f"❌ Erro ao obter status OpenAI: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.post("/test")
async def test_openai_connection():
    """
    Teste simples de conexão com OpenAI
    """
    try:
        # Teste com mensagem simples
        test_message = "Olá, como você está?"
        result = await openai_service.generate_therapeutic_response(
            user_message=test_message,
            session_id="test"
        )
        
        return {
            "status": "success",
            "test_message": test_message,
            "result": result,
            "openai_available": openai_service.is_available()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no teste OpenAI: {e}")
        return {
            "status": "error",
            "error": str(e),
            "openai_available": openai_service.is_available()
        } 