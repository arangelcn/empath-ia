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
    session_objective: Optional[Dict[str, Any]] = None
    initial_prompt: Optional[str] = None

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
            conversation_history=request.conversation_history,
            session_objective=request.session_objective,
            initial_prompt=request.initial_prompt
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

@router.post("/generate-session-context")
async def generate_session_context(request: dict):
    """
    Gerar contexto de uma sessão terapêutica baseado na conversa
    """
    try:
        conversation_text = request.get("conversation_text", "")
        emotions_data = request.get("emotions_data", [])
        
        if not conversation_text:
            raise HTTPException(status_code=400, detail="conversation_text é obrigatório")
        
        # Usar o serviço OpenAI para gerar contexto
        openai_service = OpenAIService()
        context = await openai_service.generate_session_context(conversation_text, emotions_data)
        
        return {
            "success": True,
            "context": context
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar contexto da sessão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/generate-next-session")
async def generate_next_session(request: dict):
    """
    Gerar próxima sessão terapêutica personalizada baseada no contexto do usuário
    """
    try:
        user_profile = request.get("user_profile", {})
        session_context = request.get("session_context", {})
        current_session_id = request.get("current_session_id", "")
        
        if not session_context:
            raise HTTPException(status_code=400, detail="session_context é obrigatório")
        
        # Usar o serviço OpenAI para gerar próxima sessão
        openai_service = OpenAIService()
        next_session = await openai_service.generate_next_session(
            user_profile=user_profile,
            session_context=session_context,
            current_session_id=current_session_id
        )
        
        return {
            "success": True,
            "next_session": next_session
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar próxima sessão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")