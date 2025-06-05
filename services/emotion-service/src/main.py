from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime

# Criar app FastAPI
app = FastAPI(
    title="empatIA Emotion Service",
    description="Serviço de análise emocional facial com OpenFace",
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
        "service": "emotion-service",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "empatIA Emotion Service",
        "description": "Serviço de análise emocional facial",
        "docs": "/docs"
    }

# Endpoint para análise de expressão facial
@app.post("/analyze-facial-expression")
async def analyze_facial_expression(file: UploadFile = File(...)):
    """
    Endpoint para análise de expressão facial
    TODO: Implementar integração com OpenFace
    """
    return {
        "emotions": {
            "joy": 0.7,
            "sadness": 0.1,
            "anger": 0.05,
            "fear": 0.05,
            "surprise": 0.05,
            "disgust": 0.05
        },
        "dominant_emotion": "joy",
        "confidence": 0.85,
        "status": "development",
        "message": "Análise de emoções em desenvolvimento - OpenFace será integrado em breve",
        "service": "emotion-service",
        "filename": file.filename
    }

# Endpoint para análise de vídeo
@app.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    """
    Endpoint para análise emocional de vídeo
    TODO: Implementar análise frame por frame
    """
    return {
        "timeline": [
            {
                "timestamp": 0.0,
                "emotions": {"joy": 0.8, "sadness": 0.2},
                "dominant_emotion": "joy"
            },
            {
                "timestamp": 1.0,
                "emotions": {"joy": 0.6, "sadness": 0.4},
                "dominant_emotion": "joy"
            }
        ],
        "summary": {
            "avg_emotions": {"joy": 0.7, "sadness": 0.3},
            "dominant_emotion": "joy",
            "duration": 2.0
        },
        "status": "development",
        "service": "emotion-service",
        "filename": file.filename
    }

# Endpoint para configurações
@app.get("/config")
async def get_config():
    """Retorna configurações do serviço"""
    return {
        "openface_path": os.getenv("OPENFACE_MODEL_PATH", "/models/openface"),
        "confidence_threshold": float(os.getenv("EMOTION_CONFIDENCE_THRESHOLD", "0.7")),
        "service_port": os.getenv("EMOTION_SERVICE_PORT", "8003"),
        "debug": os.getenv("DEBUG", "false").lower() == "true"
    }

# Endpoint para estatísticas
@app.get("/stats")
async def get_stats():
    """Retorna estatísticas do serviço"""
    return {
        "total_analyses": 0,
        "avg_confidence": 0.85,
        "most_common_emotion": "joy",
        "uptime": "just started",
        "service": "emotion-service"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 