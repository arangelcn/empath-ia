from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime

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

# Chat endpoint (básico por enquanto)
@app.post("/chat")
async def chat(message: dict):
    """
    Endpoint principal para conversas de chat
    TODO: Implementar lógica OpenAI e psicólogo Rogers
    """
    return {
        "response": "Olá! Sou o empatIA AI Service. Ainda estou sendo configurado para conversas terapêuticas.",
        "service": "ai-service",
        "status": "development"
    }

# Endpoint para configurações
@app.get("/config")
async def get_config():
    """Retorna configurações do serviço"""
    return {
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "model": os.getenv("MODEL_NAME", "gpt-4o"),
        "service_port": os.getenv("AI_SERVICE_PORT", "8001"),
        "debug": os.getenv("DEBUG", "false").lower() == "true"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 