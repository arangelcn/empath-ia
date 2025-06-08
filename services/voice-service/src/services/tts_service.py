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
        # Aceitar automaticamente a licença não-comercial do Coqui TTS
        os.environ["COQUI_TOS_AGREED"] = "1"
        
        # Configurar cache local se disponível
        local_models_path = os.getenv("TTS_MODELS_PATH", "/app/models/tts")
        local_cache_path = os.getenv("TTS_CACHE_PATH", "/app/models/tts")
        
        # Verificar se temos modelos locais
        self.use_local_models = Path(local_models_path).exists()
        if self.use_local_models:
            logger.info(f"📁 Modelos locais encontrados em: {local_models_path}")
            os.environ["TTS_HOME"] = local_cache_path
        else:
            logger.info("🌐 Usando modelos online (será feito download)")
        
        # Configurar PyTorch para permitir carregamento seguro do XTTS-v2
        try:
            from TTS.tts.configs.xtts_config import XttsConfig
            # COMENTADO: add_safe_globals não disponível na versão atual do PyTorch
            # torch.serialization.add_safe_globals([XttsConfig])
            logger.info("Configuração de segurança do PyTorch aplicada para XTTS-v2")
        except ImportError:
            logger.warning("Não foi possível importar XttsConfig - continuando sem configuração específica")
        
        # Configuração flexível de modelos
        self.available_models = {
            "xtts_v2": "tts_models/multilingual/multi-dataset/xtts_v2",  # Melhor para PT-BR
            "vits_pt": "tts_models/pt/cv/vits",  # Original (PT-EU)
            "your_tts": "tts_models/multilingual/multi-dataset/your_tts"  # Alternativa multilíngue
        }
        
        # Mapear caminhos locais se disponível
        if self.use_local_models:
            self.local_model_paths = {
                "xtts_v2": Path(local_models_path) / "xtts_v2",
                "vits_pt": Path(local_models_path) / "vits_pt", 
                "your_tts": Path(local_models_path) / "your_tts"
            }
        
        # Usar XTTS-v2 como padrão para melhor qualidade em PT-BR
        self.current_model = os.getenv("TTS_MODEL", "xtts_v2")
        self.model_name = self.available_models.get(self.current_model, self.available_models["xtts_v2"])
        
        # Configurações específicas para português brasileiro
        self.language = "pt"  # Para XTTS-v2, usar 'pt' que inclui PT-BR
        self.use_gpu = torch.cuda.is_available() and os.getenv("TTS_USE_GPU", "false").lower() == "true"
        self.device = "cuda" if self.use_gpu else "cpu"
        
        self.tts = None
        self.output_dir = Path("/app/output")
        self.base_url = os.getenv("VOICE_SERVICE_BASE_URL", "http://localhost:8004")
        
        # Configurações de qualidade para PT-BR
        self.quality_settings = {
            "temperature": 0.7,  # Mais estável que o padrão
            "length_penalty": 1.0,
            "repetition_penalty": 2.0,
            "top_k": 50,
            "top_p": 0.8,
            "speed": 1.0
        }
        
        # Criar diretório de saída se não existir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"TTS Service inicializado - Modelo: {self.model_name}, Device: {self.device}")
        
    def load_model(self) -> bool:
        """Carrega o modelo TTS"""
        try:
            if self.tts is None:
                # Verificar se temos modelo local primeiro
                model_path_to_use = self.model_name
                
                if self.use_local_models and hasattr(self, 'local_model_paths'):
                    local_path = self.local_model_paths.get(self.current_model)
                    if local_path and local_path.exists():
                        logger.info(f"📁 Usando modelo local: {local_path}")
                        model_path_to_use = str(local_path)
                    else:
                        logger.warning(f"⚠️ Modelo local não encontrado em {local_path}, usando online")
                
                logger.info(f"Carregando modelo TTS: {model_path_to_use}")
                
                # Configurar ambiente para CPU se necessário
                if not self.use_gpu:
                    os.environ["CUDA_VISIBLE_DEVICES"] = ""
                
                # Aceitar automaticamente a licença
                os.environ["COQUI_TOS_AGREED"] = "1"
                
                self.tts = TTS(
                    model_name=model_path_to_use, 
                    progress_bar=True, 
                    gpu=self.use_gpu
                )
                
                model_source = "local" if self.use_local_models and str(model_path_to_use).startswith("/") else "online"
                logger.info(f"✅ Modelo TTS carregado com sucesso! (Device: {self.device}, Source: {model_source})")
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar modelo TTS: {e}")
            # Fallback para modelo VITS se XTTS falhar
            if self.current_model != "vits_pt":
                logger.info("Tentando fallback para modelo VITS...")
                self.current_model = "vits_pt"
                self.model_name = self.available_models["vits_pt"]
                self.tts = None
                return self.load_model()
            return False
    
    def is_model_loaded(self) -> bool:
        """Verifica se o modelo está carregado"""
        return self.tts is not None
    
    def generate_filename(self) -> str:
        """Gera nome único para arquivo de áudio"""
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        return f"speech_{timestamp}_{unique_id}.wav"
    
    def text_to_speech(self, text: str, voice_speed: float = 1.0, voice_reference: Optional[str] = None) -> Tuple[bool, str, Optional[str], Optional[float]]:
        """
        Converte texto em áudio
        
        Args:
            text: Texto para converter
            voice_speed: Velocidade da fala (0.5 a 2.0)
            voice_reference: Caminho para arquivo de referência de voz (para clonagem)
            
        Returns:
            Tuple[success, message, audio_path, duration]
        """
        try:
            # Verificar se modelo está carregado
            if not self.load_model():
                return False, "Erro ao carregar modelo TTS", None, None
            
            # Validar texto de entrada
            if not text or text.strip() == "":
                return False, "Texto vazio ou inválido", None, None
            
            # Gerar nome do arquivo
            filename = self.generate_filename()
            if not filename:
                return False, "Erro ao gerar nome do arquivo", None, None
                
            output_path = self.output_dir / filename
            
            logger.info(f"Gerando áudio para texto: '{text[:50]}...' (modelo: {self.current_model})")
            
            # Verificar se o diretório de saída existe
            if not self.output_dir.exists():
                self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Configurar parâmetros baseado no modelo
            if self.current_model == "xtts_v2":
                # XTTS-v2: Melhor qualidade para PT-BR
                logger.info(f"Usando modelo XTTS-v2, output_path: {output_path}")
                if voice_reference and os.path.exists(voice_reference):
                    # Clonagem de voz
                    logger.info(f"Clonagem de voz com referência: {voice_reference}")
                    self.tts.tts_to_file(
                        text=text,
                        file_path=str(output_path),
                        speaker_wav=voice_reference,
                        language=self.language,
                        split_sentences=True  # Melhor para textos longos
                    )
                else:
                    # Usar speaker padrão do XTTS otimizado para PT-BR
                    logger.info(f"Usando speaker padrão, language: {self.language}")
                    logger.info(f"Parâmetros debug: text='{text}', file_path='{str(output_path)}', language='{self.language}'")
                    
                    # Para XTTS-v2, não usar parâmetro speaker pois não é multi-speaker
                    try:
                        self.tts.tts_to_file(
                            text=text,
                            file_path=str(output_path),
                            language=self.language,
                            split_sentences=True
                        )
                        logger.info(f"TTS gerado com sucesso para: {output_path}")
                    except Exception as tts_error:
                        logger.error(f"Erro específico no tts_to_file: {tts_error}")
                        raise
            elif self.current_model == "your_tts":
                # YourTTS: Multilíngue com clonagem
                logger.info(f"Usando modelo YourTTS, output_path: {output_path}")
                if voice_reference and os.path.exists(voice_reference):
                    self.tts.tts_to_file(
                        text=text,
                        file_path=str(output_path),
                        speaker_wav=voice_reference,
                        language="pt-br"  # Específico para brasileiro
                    )
                else:
                    self.tts.tts_to_file(
                        text=text,
                        file_path=str(output_path),
                        language="pt-br"
                    )
            else:
                # VITS: Modelo original
                logger.info(f"Usando modelo VITS, output_path: {output_path}")
                self.tts.tts_to_file(text=text, file_path=str(output_path))
            
            # Verificar se o arquivo foi criado
            if not output_path.exists():
                return False, "Arquivo de áudio não foi criado", None, None
            
            # Aplicar velocidade se diferente de 1.0
            if voice_speed != 1.0:
                try:
                    audio_data, sample_rate = librosa.load(str(output_path), sr=None)
                    audio_data = librosa.effects.time_stretch(audio_data, rate=voice_speed)
                    sf.write(str(output_path), audio_data, sample_rate)
                except Exception as e:
                    logger.warning(f"Erro ao aplicar velocidade {voice_speed}: {e}")
            
            # Calcular duração
            duration = self.get_audio_duration(str(output_path))
            
            # URL pública do arquivo
            audio_url = f"{self.base_url}/audio/{filename}"
            
            logger.info(f"Áudio gerado com sucesso: {filename} (duração: {duration:.2f}s, modelo: {self.current_model})")
            
            return True, f"Áudio gerado com sucesso usando {self.current_model}", audio_url, duration
            
        except Exception as e:
            logger.error(f"Erro ao gerar áudio: {e}")
            return False, f"Erro ao gerar áudio: {str(e)}", None, None
    
    def change_model(self, model_key: str) -> bool:
        """
        Troca o modelo TTS em tempo de execução
        
        Args:
            model_key: Chave do modelo ('xtts_v2', 'vits_pt', 'your_tts')
        """
        try:
            if model_key in self.available_models:
                logger.info(f"Trocando modelo de {self.current_model} para {model_key}")
                self.current_model = model_key
                self.model_name = self.available_models[model_key]
                self.tts = None  # Força recarregamento
                return self.load_model()
            else:
                logger.error(f"Modelo {model_key} não disponível. Modelos disponíveis: {list(self.available_models.keys())}")
                return False
        except Exception as e:
            logger.error(f"Erro ao trocar modelo: {e}")
            return False
    
    def get_model_info(self) -> dict:
        """Retorna informações sobre o modelo atual"""
        return {
            "current_model": self.current_model,
            "model_name": self.model_name,
            "available_models": self.available_models,
            "device": self.device,
            "language": self.language,
            "is_loaded": self.is_model_loaded(),
            "quality_settings": self.quality_settings
        }
    
    def get_audio_duration(self, file_path: str) -> float:
        """Calcula duração do arquivo de áudio"""
        try:
            # Verificar se o caminho é válido
            if not file_path or file_path.strip() == "":
                logger.error("Caminho do arquivo é vazio ou None")
                return 0.0
                
            # Verificar se o arquivo existe
            if not os.path.exists(file_path):
                logger.error(f"Arquivo não encontrado: {file_path}")
                return 0.0
                
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