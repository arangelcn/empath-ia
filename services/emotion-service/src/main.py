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

# Usar wrapper otimizado com DeepFace + Legacy fallback
processor_type = "DeepFace + MediaPipe (with Legacy fallback)"
use_legacy = False  # Principal é DeepFace, legacy apenas como fallback

# Criar app FastAPI
app = FastAPI(
    title="empatIA Emotion Service",
    description=f"Serviço de análise emocional facial com {processor_type}",
    version="2.0.0",
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

# Inicializar processador de emoções faciais (Wrapper DeepFace + Legacy)
emotion_engine = facial_emotion_processor

# Variável global para controlar inicialização
_processor_initialized = False

@app.on_event("startup")
async def startup_event():
    """Evento executado no startup da aplicação para inicializar processadores"""
    global _processor_initialized
    
    logger.info("🚀 Iniciando Emotion Service v2.0...")
    logger.info(f"📊 Processador configurado: {processor_type}")
    logger.info(f"🔧 Legacy mode: {use_legacy}")
    logger.info(f"💻 Detector: MediaPipe (CPU optimized)")
    
    try:
        logger.info("🔄 Inicializando processador DeepFace...")
        
        # Forçar inicialização do processador DeepFace
        logger.info("📥 Baixando/carregando modelos DeepFace...")
        if hasattr(emotion_engine, 'initialize'):
            emotion_engine.initialize()
        else:
            # Se não existe método initialize, criar uma imagem teste para forçar inicialização
            import numpy as np
            test_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            
            # Usar PIL para criar imagem temporária
            from PIL import Image
            import tempfile
            test_pil = Image.fromarray(test_image)
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                test_pil.save(tmp.name)
                logger.info("🧪 Executando inicialização com imagem de teste...")
                result = emotion_engine.process_image(tmp.name)
                os.unlink(tmp.name)
                logger.info(f"✅ Processador DeepFace inicializado: {result is not None}")
        
        _processor_initialized = True
        logger.info("🎉 Emotion Service inicializado com sucesso!")
        
        # Log de informações finais
        logger.info("📋 Configuração final:")
        logger.info(f"   - Processador: {processor_type}")
        logger.info(f"   - Device: {getattr(emotion_engine, 'device', 'cpu')}")
        logger.info(f"   - Detector: {getattr(emotion_engine, 'detector_backend', 'mediapipe')}")
        logger.info(f"   - Status: Pronto para receber requisições")
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização do processador: {e}")
        logger.error("⚠️ Serviço pode funcionar em modo degradado")
        _processor_initialized = False

@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no shutdown da aplicação"""
    logger.info("🛑 Encerrando Emotion Service...")
    
    # Cleanup se necessário
    if hasattr(emotion_engine, 'cleanup'):
        try:
            emotion_engine.cleanup()
            logger.info("🧹 Cleanup realizado com sucesso")
        except Exception as e:
            logger.warning(f"⚠️ Erro no cleanup: {e}")
    
    logger.info("👋 Emotion Service encerrado")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Verifica saúde do serviço e status de inicialização do processador"""
    global _processor_initialized
    
    # Verificar disponibilidade do processador
    processor_status = _processor_initialized
    device_info = "cpu"
    processor_details = {}
    
    try:
        if _processor_initialized:
            # DeepFace processor com informações de GPU
            gpu_info = {}
            if hasattr(emotion_engine, 'get_device_info'):
                gpu_info = emotion_engine.get_device_info()
            
            processor_details = {
                "type": "DeepFace",
                "model_loaded": True,
                "device_type": gpu_info.get("device_type", "CPU"),
                "cuda_available": gpu_info.get("cuda_available", False),
                "gpu_available": gpu_info.get("gpu_available", False),
                "gpu_count": gpu_info.get("gpu_count", 0),
                "detector_backend": getattr(emotion_engine, 'primary_detector', 'mediapipe'),
                "gpu_devices": gpu_info.get("gpu_devices", [])
            }
            device_info = {
                "type": gpu_info.get("device_type", "CPU"),
                "cuda_available": gpu_info.get("cuda_available", False),
                "gpu_available": gpu_info.get("gpu_available", False),
                "gpu_count": gpu_info.get("gpu_count", 0)
            }
        else:
            processor_details = {
                "type": "DeepFace",
                "model_loaded": False,
                "device_type": "unknown",
                "cuda_available": False,
                "gpu_available": False,
                "detector_backend": "unknown"
            }
            device_info = {
                "type": "unknown",
                "cuda_available": False,
                "gpu_available": False
            }
    except Exception as e:
        logger.warning(f"Processor status check failed: {e}")
        processor_status = False
        processor_details = {
            "type": "Error",
            "model_loaded": False,
            "device_type": "unknown",
            "cuda_available": False,
            "gpu_available": False,
            "error": str(e)
        }
        device_info = {
            "type": "error",
            "cuda_available": False,
            "gpu_available": False
        }
    
    # Determinar status geral
    overall_status = "healthy" if processor_status else "initializing" if not _processor_initialized else "degraded"
    
    return {
        "status": overall_status,
        "service": "emotion-service", 
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "processor_type": processor_type,
        "processor_initialized": _processor_initialized,
        "processor_available": processor_status,
        "processor_details": processor_details,
        "device": device_info,
        "cuda_available": device_info.get("cuda_available", False),
        "gpu_available": device_info.get("gpu_available", False),
        "ready_for_requests": processor_status
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "empatIA Emotion Service",
        "description": f"Serviço de análise emocional facial com {processor_type}",
        "version": "2.0.0",
        "processor": processor_type,
        "docs": "/docs"
    }

# Endpoint para análise de expressão facial
@app.post("/analyze-facial-expression")
async def analyze_facial_expression(file: UploadFile = File(...)):
    """
    Endpoint para análise de expressão facial usando DeepFace
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
            # Processar com DeepFace
            result = emotion_engine.process_image(temp_file_path)
            
            if result is None:
                # Retornar erro 422 para nenhuma face detectada (conforme especificação)
                raise HTTPException(
                    status_code=422, 
                    detail="Nenhuma face detectada na imagem. Verifique se a imagem contém uma face claramente visível."
                )
            
            # Extrair emoções e emoção dominante do resultado
            emotions = result.get("emotions", {"neutral": 1.0})
            dominant_emotion = result.get("dominant_emotion", "neutral")
            confidence = result.get("confidence", 0.0)
            
            # Normalizar emoções para garantir que somem 1.0
            total_score = sum(emotions.values())
            if total_score > 0:
                emotions = {k: v/total_score for k, v in emotions.items()}
            else:
                emotions = {"neutral": 1.0}
            
            return {
                "dominant_emotion": dominant_emotion,
                "probabilities": emotions,
                "emotions": emotions,  # Manter compatibilidade
                "confidence": confidence,
                "status": "success",
                "message": "Análise facial realizada com sucesso",
                "service": "emotion-service",
                "filename": file.filename,
                "face_detected": result.get("face_detected", True),
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
        
        # Processar diretamente com DeepFace (sem arquivos temporários)
        result = emotion_engine.process_image_bytes(image_bytes)
        
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
        
        # Processar diretamente com DeepFace (com debug)
        result = emotion_engine.process_image_bytes(image_bytes)
        
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
        "processor_type": processor_type,
        "use_legacy_landmarks": use_legacy,
        "emotion_model_path": os.getenv("EMOTION_MODEL_PATH"),
        "confidence_threshold": float(os.getenv("EMOTION_CONFIDENCE_THRESHOLD", "0.7")),
        "service_port": os.getenv("EMOTION_SERVICE_PORT", "8003"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "device": getattr(emotion_engine, 'device', 'cpu'),
        "cuda_available": False,  # MediaPipe usa CPU
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
        "processor_type": processor_type,
        "processor_status": "available"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 