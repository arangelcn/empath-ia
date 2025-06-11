import os
import uuid
import time
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import torch
import soundfile as sf
import librosa
from bark import SAMPLE_RATE, generate_audio, preload_models
from bark.generation import generate_text_semantic
from bark.api import semantic_to_waveform
import scipy.io.wavfile

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BarkService:
    """Serviço de Text-to-Speech usando Bark (Suno AI)"""
    
    def __init__(self):
        # Configurações do Bark
        self.sample_rate = SAMPLE_RATE  # 22050 Hz
        self.use_gpu = torch.cuda.is_available() and os.getenv("BARK_USE_GPU", "true").lower() == "true"
        self.device = "cuda" if self.use_gpu else "cpu"
        
        # Vozes disponíveis para português brasileiro
        self.available_voices = {
            "v2/pt_speaker_0": "Voz masculina brasileira 1",
            "v2/pt_speaker_1": "Voz feminina brasileira 1", 
            "v2/pt_speaker_2": "Voz masculina brasileira 2",
            "v2/pt_speaker_3": "Voz feminina brasileira 2",
            "v2/pt_speaker_4": "Voz masculina brasileira 3",
            "v2/pt_speaker_5": "Voz feminina brasileira 3",
            "v2/pt_speaker_6": "Voz masculina brasileira 4",
            "v2/pt_speaker_7": "Voz feminina brasileira 4",
            "v2/pt_speaker_8": "Voz masculina brasileira 5",
            "v2/pt_speaker_9": "Voz feminina brasileira 5"
        }
        
        # Voz padrão
        self.default_voice = os.getenv("BARK_DEFAULT_VOICE", "v2/pt_speaker_1")
        self.current_voice = self.default_voice
        
        # Configurações de qualidade
        self.quality_settings = {
            "temperature": 0.7,
            "fine_tuning": True,
            "use_kv_caching": True,
            "silent": False
        }
        
        self.output_dir = Path(os.getenv("F5_TTS_OUTPUT_DIR", "/app/tts_output"))
        self.base_url = os.getenv("VOICE_SERVICE_BASE_URL", "http://localhost:8004")
        
        # Estado do modelo
        self.models_loaded = False
        
        # Criar diretório de saída se não existir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Bark Service inicializado - Device: {self.device}")
        logger.info(f"Vozes disponíveis: {len(self.available_voices)}")
    
    def load_models(self) -> bool:
        """Carrega os modelos do Bark"""
        try:
            if not self.models_loaded:
                logger.info("Carregando modelos do Bark...")
                
                # Configurar dispositivo
                if not self.use_gpu:
                    os.environ["CUDA_VISIBLE_DEVICES"] = ""
                
                # Corrigir problema do PyTorch 2.6+ com weights_only
                # Fazer monkey patch temporário do torch.load
                original_load = torch.load
                def patched_load(*args, **kwargs):
                    # Sempre usar weights_only=False para compatibilidade com modelos Bark
                    kwargs['weights_only'] = False
                    return original_load(*args, **kwargs)
                
                # Aplicar patch temporário
                torch.load = patched_load
                
                try:
                    # Adicionar globals seguros para numpy
                    torch.serialization.add_safe_globals([
                        "numpy.core.multiarray.scalar",
                        "numpy.dtype",
                        "collections.OrderedDict",
                        "torch._utils._rebuild_tensor_v2"
                    ])
                    
                    # Pré-carregar modelos do Bark
                    preload_models(
                        text_use_gpu=self.use_gpu,
                        text_use_small=False,  # Usar modelo completo para melhor qualidade
                        coarse_use_gpu=self.use_gpu,
                        coarse_use_small=False,
                        fine_use_gpu=self.use_gpu,
                        fine_use_small=False,
                        codec_use_gpu=self.use_gpu
                    )
                    
                    self.models_loaded = True
                    logger.info(f"Modelos do Bark carregados com sucesso! (Device: {self.device})")
                    
                except Exception as load_error:
                    logger.error(f"Erro ao carregar modelos: {load_error}")
                    return False
                    
                finally:
                    # Sempre restaurar torch.load original
                    torch.load = original_load
                
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar modelos do Bark: {e}")
            return False
    
    def are_models_loaded(self) -> bool:
        """Verifica se os modelos estão carregados"""
        return self.models_loaded
    
    def generate_filename(self) -> str:
        """Gera nome único para arquivo de áudio"""
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        return f"bark_speech_{timestamp}_{unique_id}.wav"
    
    def text_to_speech(self, text: str, voice_speed: float = 1.0, voice_preset: Optional[str] = None) -> Tuple[bool, str, Optional[str], Optional[float]]:
        """
        Converte texto em áudio usando Bark
        
        Args:
            text: Texto para converter
            voice_speed: Velocidade da fala (será aplicada via librosa)
            voice_preset: Preset de voz (ex: "v2/pt_speaker_1")
            
        Returns:
            Tuple[success, message, audio_url, duration]
        """
        try:
            # Verificar se modelos estão carregados
            if not self.load_models():
                return False, "Erro ao carregar modelos do Bark", None, None
            
            # Usar voz especificada ou padrão
            voice = voice_preset if voice_preset and voice_preset in self.available_voices else self.current_voice
            
            # Gerar nome do arquivo
            filename = self.generate_filename()
            output_path = self.output_dir / filename
            
            logger.info(f"Gerando áudio com Bark para texto: '{text[:50]}...' (voz: {voice})")
            
            # Preparar texto com instruções para português brasileiro
            # Bark entende instruções em texto natural
            prompt_text = f"[pt-BR] {text}"
            
            # Gerar áudio com Bark
            audio_array = generate_audio(
                prompt_text,
                history_prompt=voice,
                text_temp=self.quality_settings["temperature"],
                waveform_temp=self.quality_settings["temperature"]
            )
            
            # Salvar áudio inicial
            sf.write(str(output_path), audio_array, self.sample_rate)
            
            # Aplicar velocidade se diferente de 1.0
            if voice_speed != 1.0:
                audio_data, sample_rate = librosa.load(str(output_path), sr=None)
                audio_data = librosa.effects.time_stretch(audio_data, rate=voice_speed)
                sf.write(str(output_path), audio_data, sample_rate)
            
            # Calcular duração
            duration = len(audio_array) / self.sample_rate
            if voice_speed != 1.0:
                duration = duration / voice_speed
            
            # URL pública do arquivo
            audio_url = f"{self.base_url}/audio/{filename}"
            
            logger.info(f"Áudio gerado com sucesso usando Bark: {filename} (duração: {duration:.2f}s, voz: {voice})")
            
            return True, f"Áudio gerado com sucesso usando Bark (voz: {voice})", audio_url, duration
            
        except Exception as e:
            logger.error(f"Erro ao gerar áudio com Bark: {e}")
            return False, f"Erro ao gerar áudio com Bark: {str(e)}", None, None
    
    def change_voice(self, voice_key: str) -> bool:
        """
        Troca a voz em tempo de execução
        
        Args:
            voice_key: Chave da voz ('v2/pt_speaker_0', etc.)
        """
        try:
            if voice_key in self.available_voices:
                logger.info(f"Trocando voz de {self.current_voice} para {voice_key}")
                self.current_voice = voice_key
                return True
            else:
                logger.error(f"Voz {voice_key} não disponível. Vozes disponíveis: {list(self.available_voices.keys())}")
                return False
        except Exception as e:
            logger.error(f"Erro ao trocar voz: {e}")
            return False
    
    def get_service_info(self) -> dict:
        """Retorna informações sobre o serviço Bark"""
        return {
            "service_name": "bark_service",
            "model_type": "Bark (Suno AI)",
            "current_voice": self.current_voice,
            "available_voices": self.available_voices,
            "device": self.device,
            "sample_rate": self.sample_rate,
            "models_loaded": self.models_loaded,
            "quality_settings": self.quality_settings,
            "features": [
                "Voz natural com expressividade",
                "Múltiplas vozes em português brasileiro",
                "Suporte a emoções e entonação",
                "Geração rápida",
                "Controle de velocidade"
            ]
        }
    
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
            
            for file_path in self.output_dir.glob("bark_speech_*.wav"):
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
    
    def clone_voice_from_audio(self, audio_file_path: str) -> Optional[str]:
        """
        Cria um preset de voz a partir de um arquivo de áudio (feature futura)
        Por enquanto, retorna uma das vozes disponíveis baseada no arquivo
        """
        try:
            # Esta é uma implementação simplificada
            # O Bark não suporta clonagem direta como outros modelos
            # Mas podemos analisar o áudio e sugerir uma voz similar
            
            logger.info(f"Analisando áudio para seleção de voz similar: {audio_file_path}")
            
            # Carregar e analisar o áudio
            audio_data, sr = librosa.load(audio_file_path, sr=None)
            duration = len(audio_data) / sr
            
            # Análise básica do pitch para determinar se é voz masculina ou feminina
            pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sr)
            pitch_values = pitches[magnitudes > np.median(magnitudes)]
            avg_pitch = np.mean(pitch_values[pitch_values > 0]) if len(pitch_values) > 0 else 150
            
            # Selecionar voz baseada no pitch
            if avg_pitch > 180:  # Voz mais aguda (tipicamente feminina)
                suggested_voices = ["v2/pt_speaker_1", "v2/pt_speaker_3", "v2/pt_speaker_5", "v2/pt_speaker_7", "v2/pt_speaker_9"]
            else:  # Voz mais grave (tipicamente masculina)
                suggested_voices = ["v2/pt_speaker_0", "v2/pt_speaker_2", "v2/pt_speaker_4", "v2/pt_speaker_6", "v2/pt_speaker_8"]
            
            # Retornar uma voz sugerida
            import random
            suggested_voice = random.choice(suggested_voices)
            
            logger.info(f"Voz sugerida baseada na análise: {suggested_voice} (pitch médio: {avg_pitch:.1f}Hz)")
            
            return suggested_voice
            
        except Exception as e:
            logger.error(f"Erro na análise de voz: {e}")
            return None 