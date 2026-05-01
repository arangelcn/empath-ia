import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging
from ..models.database import get_collection

logger = logging.getLogger(__name__)

class UserEmotionService:
    """
    Serviço para gerenciar emoções detectadas dos usuários
    Salva emoções em tempo real de forma assíncrona
    """
    
    def __init__(self):
        self.collection_name = "user_emotions"

    @property
    def emotions_collection(self):
        """Obter coleção de emoções"""
        return get_collection(self.collection_name)

    async def save_emotion_async(self, emotion_data: Dict[str, Any]) -> None:
        """
        Salvar emoção de forma assíncrona sem bloquear a resposta
        """
        try:
            # Executar o salvamento em background
            asyncio.create_task(self._save_emotion_internal(emotion_data))
        except Exception as e:
            logger.error(f"❌ Erro ao agendar salvamento de emoção: {e}")
            # Não falhamos - apenas logamos o erro

    async def _save_emotion_internal(self, emotion_data: Dict[str, Any]) -> Optional[str]:
        """
        Salvamento interno da emoção
        """
        try:
            # Preparar documento para salvamento
            document = {
                "username": emotion_data.get("username"),
                "chat_id": emotion_data.get("chat_id"),
                "session_id": emotion_data.get("session_id"),
                "therapeutic_session_id": emotion_data.get("therapeutic_session_id"),
                "dominant_emotion": emotion_data.get("dominant_emotion"),
                "emotions": emotion_data.get("emotions", {}),
                "confidence": emotion_data.get("confidence", 0),
                "face_detected": emotion_data.get("face_detected", False),
                "timestamp": datetime.now(timezone.utc),
                "created_at": datetime.now(timezone.utc)
            }
            
            # Salvar no MongoDB
            result = await self.emotions_collection.insert_one(document)
            
            if result.inserted_id:
                logger.info(f"✅ Emoção salva: {emotion_data.get('username')} - {emotion_data.get('dominant_emotion')}")
                return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar emoção: {e}")
            return None

    async def get_user_emotions(self, username: str, session_id: Optional[str] = None, 
                               limit: int = 100, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Obter emoções de um usuário em uma sessão específica ou todas
        """
        try:
            # Construir filtro
            filter_query = {"username": username}
            
            if session_id:
                filter_query["session_id"] = session_id
            
            # Filtrar por tempo (últimas X horas)
            if hours_back > 0:
                from datetime import timedelta
                time_limit = datetime.now(timezone.utc) - timedelta(hours=hours_back)
                filter_query.update({"timestamp": {"$gte": time_limit}})
            
            # Buscar emoções
            cursor = self.emotions_collection.find(filter_query).sort("timestamp", -1).limit(limit)
            emotions = await cursor.to_list(length=limit)
            
            # Converter ObjectId para string
            for emotion in emotions:
                emotion["_id"] = str(emotion["_id"])
            
            return emotions
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar emoções: {e}")
            return []

    async def get_emotion_summary(self, username: str, session_id: Optional[str] = None, 
                                 hours_back: int = 24) -> Dict[str, Any]:
        """
        Obter resumo das emoções de um usuário
        """
        try:
            # Construir filtro
            filter_query = {"username": username}
            
            if session_id:
                filter_query["session_id"] = session_id
            
            # Filtrar por tempo
            if hours_back > 0:
                from datetime import timedelta
                time_limit = datetime.now(timezone.utc) - timedelta(hours=hours_back)
                filter_query["timestamp"] = {"$gte": time_limit}
            
            # Buscar todas as emoções
            cursor = self.emotions_collection.find(filter_query)
            emotions = await cursor.to_list(length=None)
            
            if not emotions:
                return {
                    "total_detections": 0,
                    "dominant_emotion": None,
                    "emotion_distribution": {},
                    "average_confidence": 0,
                    "face_detection_rate": 0,
                    "time_range_hours": hours_back
                }
            
            # Calcular estatísticas
            total_detections = len(emotions)
            face_detections = sum(1 for e in emotions if e.get("face_detected", False))
            
            # Distribuição de emoções
            emotion_counts = {}
            total_confidence = 0
            
            for emotion in emotions:
                dominant = emotion.get("dominant_emotion", "neutral")
                emotion_counts[dominant] = emotion_counts.get(dominant, 0) + 1
                total_confidence += emotion.get("confidence", 0)
            
            # Emoção dominante geral
            dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else None
            
            # Calcular percentuais
            emotion_distribution = {}
            for emotion, count in emotion_counts.items():
                emotion_distribution[emotion] = {
                    "count": count,
                    "percentage": round((count / total_detections) * 100, 2)
                }
            
            return {
                "total_detections": total_detections,
                "dominant_emotion": dominant_emotion,
                "emotion_distribution": emotion_distribution,
                "average_confidence": round(total_confidence / total_detections, 2) if total_detections > 0 else 0,
                "face_detection_rate": round((face_detections / total_detections) * 100, 2) if total_detections > 0 else 0,
                "time_range_hours": hours_back
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular resumo de emoções: {e}")
            return {
                "total_detections": 0,
                "dominant_emotion": None,
                "emotion_distribution": {},
                "average_confidence": 0,
                "face_detection_rate": 0,
                "time_range_hours": hours_back,
                "error": str(e)
            }

    async def get_emotion_timeline(self, username: str, session_id: Optional[str] = None, 
                                  hours_back: int = 24, interval_minutes: int = 5) -> List[Dict[str, Any]]:
        """
        Obter timeline de emoções agrupadas por intervalos de tempo
        """
        try:
            # Construir filtro
            filter_query = {"username": username}
            
            if session_id:
                filter_query["session_id"] = session_id
            
            # Filtrar por tempo
            if hours_back > 0:
                from datetime import timedelta
                time_limit = datetime.now(timezone.utc) - timedelta(hours=hours_back)
                filter_query["timestamp"] = {"$gte": time_limit}
            
            # Buscar emoções
            cursor = self.emotions_collection.find(filter_query).sort("timestamp", 1)
            emotions = await cursor.to_list(length=None)
            
            if not emotions:
                return []
            
            # Agrupar por intervalos de tempo
            timeline = []
            current_interval = None
            current_emotions = []
            
            for emotion in emotions:
                # Calcular intervalo atual
                timestamp = emotion["timestamp"]
                interval_start = timestamp.replace(
                    minute=(timestamp.minute // interval_minutes) * interval_minutes,
                    second=0,
                    microsecond=0
                )
                
                if current_interval != interval_start:
                    # Processar intervalo anterior
                    if current_emotions:
                        timeline.append(self._process_interval(current_interval, current_emotions))
                    
                    # Iniciar novo intervalo
                    current_interval = interval_start
                    current_emotions = []
                
                current_emotions.append(emotion)
            
            # Processar último intervalo
            if current_emotions:
                timeline.append(self._process_interval(current_interval, current_emotions))
            
            return timeline
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar timeline de emoções: {e}")
            return []

    def _process_interval(self, interval_start: datetime, emotions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processar emoções de um intervalo de tempo
        """
        if not emotions:
            return {
                "timestamp": interval_start.isoformat(),
                "dominant_emotion": "neutral",
                "emotion_counts": {},
                "average_confidence": 0,
                "detection_count": 0
            }
        
        # Contar emoções
        emotion_counts = {}
        total_confidence = 0
        
        for emotion in emotions:
            dominant = emotion.get("dominant_emotion", "neutral")
            emotion_counts[dominant] = emotion_counts.get(dominant, 0) + 1
            total_confidence += emotion.get("confidence", 0)
        
        # Emoção dominante do intervalo
        dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutral"
        
        return {
            "timestamp": interval_start.isoformat(),
            "dominant_emotion": dominant_emotion,
            "emotion_counts": emotion_counts,
            "average_confidence": round(total_confidence / len(emotions), 2),
            "detection_count": len(emotions)
        }

    async def cleanup_old_emotions(self, days_to_keep: int = 30) -> int:
        """
        Limpar emoções antigas (manutenção)
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            result = await self.emotions_collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"✅ Limpeza de emoções: {deleted_count} registros removidos")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza de emoções: {e}")
            return 0 
