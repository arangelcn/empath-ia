from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import io
import tempfile
import logging
from datetime import datetime
from typing import Dict, Any
from PIL import Image
from .processors.facial_emotion_processor import facial_emotion_processor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Inicializar processador de emoções faciais
emotion_processor = facial_emotion_processor

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "emotion-service",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "mediapipe_available": True
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "empatIA Emotion Service",
        "description": "Serviço de análise emocional facial com OpenFace",
        "docs": "/docs"
    }

# Endpoint para análise de expressão facial
@app.post("/analyze-facial-expression")
async def analyze_facial_expression(file: UploadFile = File(...)):
    """
    Endpoint para análise de expressão facial usando OpenFace
    """
    try:
        logger.info(f"Processing image: {file.filename}")
        
        # Validar tipo de arquivo
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")
        
        # Ler conteúdo da imagem
        image_content = await file.read()
        
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            # Converter e salvar imagem como JPEG
            try:
                image = Image.open(io.BytesIO(image_content))
                # Converter para RGB se necessário
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                image.save(temp_file.name, 'JPEG')
                temp_file_path = temp_file.name
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Erro ao processar imagem: {str(e)}")
        
        try:
            # Processar com OpenFace
            au_data = emotion_processor.process_image(temp_file_path)
            
            if au_data is None:
                # Fallback para dados mock se OpenFace falhar
                logger.warning("OpenFace processing failed, using mock data")
                return {
                    "emotions": {
                        "joy": 0.5,
                        "sadness": 0.1,
                        "anger": 0.1,
                        "fear": 0.1,
                        "surprise": 0.1,
                        "disgust": 0.1
                    },
                    "dominant_emotion": "joy",
                    "confidence": 0.5,
                    "status": "mock_data",
                    "message": "OpenFace não disponível - dados simulados",
                    "service": "emotion-service",
                    "filename": file.filename,
                    "face_detected": False,
                    "action_units": {}
                }
            
            # Interpretar emoções a partir das AUs
            emotions = emotion_processor.get_emotional_interpretation(au_data)
            
            # Encontrar emoção dominante
            dominant_emotion = "neutral"
            max_score = 0.0
            if emotions:
                dominant_emotion = max(emotions, key=emotions.get)
                max_score = emotions[dominant_emotion]
            
            # Normalizar emoções para somar 1.0
            if emotions:
                total_score = sum(emotions.values())
                if total_score > 0:
                    emotions = {k: v/total_score for k, v in emotions.items()}
                else:
                    emotions = {"neutral": 1.0}
            else:
                emotions = {"neutral": 1.0}
            
            return {
                "emotions": emotions,
                "dominant_emotion": dominant_emotion,
                "confidence": au_data.get("confidence", max_score),
                "status": "success",
                "message": "Análise facial realizada com sucesso",
                "service": "emotion-service",
                "filename": file.filename,
                "face_detected": au_data.get("face_detected", True),
                "action_units": au_data.get("action_units", {}),
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            # Limpar arquivo temporário
            try:
                os.unlink(temp_file_path)
            except:
                pass
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in facial expression analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

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

# Novo endpoint para análise em tempo real (Base64)
@app.post("/analyze-realtime")
async def analyze_realtime(data: Dict[str, Any]):
    """
    Endpoint para análise em tempo real a partir de dados Base64
    """
    try:
        if "image" not in data:
            raise HTTPException(status_code=400, detail="Campo 'image' (base64) é obrigatório")
        
        # Decodificar imagem Base64
        import base64
        try:
            # Remover prefixo data:image se presente
            image_data = data["image"]
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao decodificar Base64: {str(e)}")
        
        # Processar diretamente com MediaPipe (sem arquivos temporários)
        result = emotion_processor.process_image_bytes(image_bytes)
        
        if result is None:
            return {
                "emotions": {"neutral": 1.0},
                "dominant_emotion": "neutral",
                "confidence": 0.5,
                "status": "no_face_detected",
                "message": "Nenhuma face detectada",
                "face_detected": False,
                "timestamp": datetime.now().isoformat()
            }
        
        # Extrair emoções do resultado
        emotions = result.get("emotions", {"neutral": 1.0})
        
        # Encontrar emoção dominante
        dominant_emotion = max(emotions, key=emotions.get) if emotions else "neutral"
        max_score = emotions.get(dominant_emotion, 0.0)
        
        return {
            "emotions": emotions,
            "dominant_emotion": dominant_emotion,
            "confidence": result.get("confidence", max_score),
            "status": "success",
            "face_detected": True,
            "landmarks_count": result.get("landmarks_count", 0),
            "timestamp": datetime.now().isoformat()
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in realtime analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Novo endpoint para debug
@app.post("/debug-emotions")
async def debug_emotions(data: Dict[str, Any]):
    """
    Endpoint para debug detalhado da análise emocional
    """
    try:
        if "image" not in data:
            raise HTTPException(status_code=400, detail="Campo 'image' (base64) é obrigatório")
        
        # Decodificar imagem Base64
        import base64
        try:
            # Remover prefixo data:image se presente
            image_data = data["image"]
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            print(f"[DEBUG] Image decoded, size: {len(image_bytes)} bytes")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao decodificar Base64: {str(e)}")
        
        # Processar diretamente com MediaPipe (com debug)
        result = emotion_processor.process_image_bytes(image_bytes)
        
        print(f"[DEBUG] Process result: {result}")
        
        if result is None:
            return {
                "status": "no_face_detected",
                "message": "Nenhuma face detectada",
                "debug_info": "No landmarks found"
            }
        
        # Extrair emoções do resultado
        emotions = result.get("emotions", {"neutral": 1.0})
        
        # Encontrar emoção dominante
        dominant_emotion = max(emotions, key=emotions.get) if emotions else "neutral"
        max_score = emotions.get(dominant_emotion, 0.0)
        
        return {
            "emotions": emotions,
            "dominant_emotion": dominant_emotion,
            "confidence": result.get("confidence", max_score),
            "status": "success",
            "face_detected": True,
            "landmarks_count": result.get("landmarks_count", 0),
            "image_size": result.get("image_size", [0, 0]),
            "debug_info": {
                "raw_result": result,
                "total_landmarks": result.get("landmarks_count", 0)
            },
            "timestamp": datetime.now().isoformat()
        }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Debug endpoint error: {str(e)}")
        logger.error(f"Error in debug analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Endpoint para configurações
@app.get("/config")
async def get_config():
    """Retorna configurações do serviço"""
    return {
        "openface_path": os.getenv("OPENFACE_MODEL_PATH", "/models/openface"),
        "confidence_threshold": float(os.getenv("EMOTION_CONFIDENCE_THRESHOLD", "0.7")),
        "service_port": os.getenv("EMOTION_SERVICE_PORT", "8003"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "shared_data_dir": "/shared_data"
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
        "service": "emotion-service",
        "openface_status": "available"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 