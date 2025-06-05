from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime

# Criar app FastAPI
app = FastAPI(
    title="empatIA Avatar Service",
    description="Serviço de geração de avatares falantes com DID-AI",
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
        "service": "avatar-service",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "empatIA Avatar Service",
        "description": "Serviço de geração de avatares falantes",
        "docs": "/docs"
    }

# Endpoint para gerar avatar falante
@app.post("/generate-avatar")
async def generate_avatar(request: dict):
    """
    Endpoint para gerar avatar falante
    TODO: Implementar integração com DID-AI
    """
    return {
        "video_url": "https://placeholder.video/avatar-demo.mp4",
        "status": "development",
        "message": "Avatar service em desenvolvimento - DID-AI será integrado em breve",
        "service": "avatar-service"
    }

# Endpoint para listar avatares disponíveis
@app.get("/avatars")
async def list_avatars():
    """Lista avatares disponíveis"""
    return {
        "avatars": [
            {
                "id": "default-therapist",
                "name": "Terapeuta Padrão",
                "type": "professional",
                "status": "available"
            }
        ],
        "total": 1,
        "service": "avatar-service"
    }

# Endpoint para configurações
@app.get("/config")
async def get_config():
    """Retorna configurações do serviço"""
    return {
        "did_configured": bool(os.getenv("DID_API_KEY")),
        "did_url": os.getenv("DID_API_URL", "https://api.d-id.com"),
        "service_port": os.getenv("AVATAR_SERVICE_PORT", "8002"),
        "debug": os.getenv("DEBUG", "false").lower() == "true"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 