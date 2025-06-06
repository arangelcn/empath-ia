import os
import uuid
import time
import logging
from pathlib import Path
from typing import Optional, Tuple
import torch
from TTS.api import TTS
import librosa
import soundfile as sf

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSService:
    """Serviço de Text-to-Speech usando Coqui TTS"""
    
    def __init__(self):
        self.model_name = "tts_models/pt/cv/vits"
        self.tts = None
        # Forçar uso da CPU apenas
        self.device = "cpu"
        self.output_dir = Path("/shared_tts")
        # Usar gateway como base URL para melhor integração
        self.base_url = os.getenv("VOICE_SERVICE_BASE_URL", "http://localhost:8000/api/voice")
        
        # Criar diretório de saída se não existir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"TTS Service inicializado - Device: {self.device} (CPU-only)")
        
    def load_model(self) -> bool:
        """Carrega o modelo TTS"""
        try:
            if self.tts is None:
                logger.info(f"Carregando modelo TTS: {self.model_name}")
                # Forçar CPU e desabilitar GPU
                os.environ["CUDA_VISIBLE_DEVICES"] = ""
                self.tts = TTS(model_name=self.model_name, progress_bar=True, gpu=False)
                logger.info("Modelo TTS carregado com sucesso (CPU-only)!")
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar modelo TTS: {e}")
            return False
    
    def is_model_loaded(self) -> bool:
        """Verifica se o modelo está carregado"""
        return self.tts is not None
    
    def generate_filename(self) -> str:
        """Gera nome único para arquivo de áudio"""
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        return f"speech_{timestamp}_{unique_id}.wav"
    
    def text_to_speech(self, text: str, voice_speed: float = 1.0) -> Tuple[bool, str, Optional[str], Optional[float]]:
        """
        Converte texto em áudio
        
        Args:
            text: Texto para converter
            voice_speed: Velocidade da fala (0.5 a 2.0)
            
        Returns:
            Tuple[success, message, audio_path, duration]
        """
        try:
            # Verificar se modelo está carregado
            if not self.load_model():
                return False, "Erro ao carregar modelo TTS", None, None
            
            # Gerar nome do arquivo
            filename = self.generate_filename()
            output_path = self.output_dir / filename
            
            logger.info(f"Gerando áudio para texto: '{text[:50]}...'")
            
            # Gerar áudio
            self.tts.tts_to_file(text=text, file_path=str(output_path))
            
            # Aplicar velocidade se diferente de 1.0
            if voice_speed != 1.0:
                audio_data, sample_rate = librosa.load(str(output_path), sr=None)
                audio_data = librosa.effects.time_stretch(audio_data, rate=voice_speed)
                sf.write(str(output_path), audio_data, sample_rate)
            
            # Calcular duração
            duration = self.get_audio_duration(str(output_path))
            
            # URL pública do arquivo
            audio_url = f"{self.base_url}/audio/{filename}"
            
            logger.info(f"Áudio gerado com sucesso: {filename} (duração: {duration:.2f}s)")
            
            return True, "Áudio gerado com sucesso", audio_url, duration
            
        except Exception as e:
            logger.error(f"Erro ao gerar áudio: {e}")
            return False, f"Erro ao gerar áudio: {str(e)}", None, None
    
    def get_audio_duration(self, file_path: str) -> float:
        """Calcula duração do arquivo de áudio"""
        try:
            audio_data, sample_rate = librosa.load(file_path, sr=None)
            duration = len(audio_data) / sample_rate
            return duration
        except Exception as e:
            logger.error(f"Erro ao calcular duração: {e}")
            return 0.0
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Remove arquivos antigos do diretório de saída
        
        Args:
            max_age_hours: Idade máxima em horas para manter arquivos
            
        Returns:
            Número de arquivos removidos
        """
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            removed_count = 0
            
            for file_path in self.output_dir.glob("*.wav"):
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    removed_count += 1
                    logger.info(f"Arquivo removido: {file_path.name}")
            
            if removed_count > 0:
                logger.info(f"Limpeza concluída: {removed_count} arquivos removidos")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Erro na limpeza de arquivos: {e}")
            return 0 