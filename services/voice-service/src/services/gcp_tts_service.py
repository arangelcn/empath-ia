"""
GCP Text-to-Speech Service - Serviço de síntese de voz usando Google Cloud Text-to-Speech API
Documentação oficial: https://cloud.google.com/text-to-speech/docs/quickstart-client-libraries
"""

import os
import uuid
import time
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

from google.cloud import texttospeech
from google.api_core import exceptions as gcp_exceptions
import librosa
import soundfile as sf

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GCPTextToSpeechService:
    """Serviço de Text-to-Speech usando Google Cloud Text-to-Speech API"""
    
    def __init__(self):
        """
        Inicializa o serviço GCP Text-to-Speech
        """
        # Configurações do GCP
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not self.credentials_path:
            logger.warning("⚠️ GOOGLE_APPLICATION_CREDENTIALS não definida. Tentando usar credenciais padrão do ambiente.")
        
        # Configurações de saída
        self.output_dir = Path(os.getenv("TTS_OUTPUT_DIR", "/app/output"))
        self.base_url = os.getenv("VOICE_SERVICE_BASE_URL", "http://localhost:8004")
        
        # Configurações de repetição (retry)
        self.max_retries = 3
        self.initial_backoff = 1.0  # segundos
        
        # Configurações de voz padrão para português brasileiro
        self.default_language_code = "pt-BR"
        self.default_voice_name = "pt-BR-Wavenet-A"  # Voz feminina de alta qualidade
        self.default_ssml_gender = texttospeech.SsmlVoiceGender.FEMALE
        
        # Configurações de áudio
        self.audio_encoding = texttospeech.AudioEncoding.MP3
        self.sample_rate_hertz = 24000  # Taxa de amostragem para MP3
        
        # Vozes disponíveis para português brasileiro
        self.available_voices = {
            "pt-BR-Wavenet-A": {"gender": "FEMALE", "type": "Wavenet", "description": "Voz feminina brasileira (Wavenet)"},
            "pt-BR-Wavenet-B": {"gender": "MALE", "type": "Wavenet", "description": "Voz masculina brasileira (Wavenet)"},
            "pt-BR-Wavenet-C": {"gender": "FEMALE", "type": "Wavenet", "description": "Voz feminina brasileira 2 (Wavenet)"},
            "pt-BR-Neural2-A": {"gender": "FEMALE", "type": "Neural2", "description": "Voz feminina brasileira (Neural2)"},
            "pt-BR-Neural2-B": {"gender": "MALE", "type": "Neural2", "description": "Voz masculina brasileira (Neural2)"},
            "pt-BR-Neural2-C": {"gender": "FEMALE", "type": "Neural2", "description": "Voz feminina brasileira 2 (Neural2)"},
            "pt-BR-Standard-A": {"gender": "FEMALE", "type": "Standard", "description": "Voz feminina brasileira (Standard)"},
            "pt-BR-Standard-B": {"gender": "MALE", "type": "Standard", "description": "Voz masculina brasileira (Standard)"},
            "pt-BR-Standard-C": {"gender": "FEMALE", "type": "Standard", "description": "Voz feminina brasileira 2 (Standard)"},
        }
        
        # Cliente GCP
        self.client = None
        
        # Criar diretório de saída se não existir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"GCP TTS Service inicializado - Output: {self.output_dir}")
        
    def _initialize_client(self) -> bool:
        """Inicializa o cliente GCP Text-to-Speech"""
        try:
            if self.client is None:
                logger.info("Inicializando cliente GCP Text-to-Speech...")
                if self.credentials_path and os.path.exists(self.credentials_path):
                    logger.info(f"Carregando credenciais de: {self.credentials_path}")
                    self.client = texttospeech.TextToSpeechClient.from_service_account_file(self.credentials_path)
                else:
                    logger.warning("Credenciais não encontradas ou caminho inválido. Usando credenciais padrão do ambiente.")
                    self.client = texttospeech.TextToSpeechClient()
                
                logger.info("✅ Cliente GCP Text-to-Speech inicializado com sucesso!")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar cliente GCP: {e}", exc_info=True)
            return False
    
    def is_client_initialized(self) -> bool:
        """Verifica se o cliente está inicializado"""
        return self.client is not None
    
    def generate_filename(self, extension: str = "mp3") -> str:
        """Gera nome único para arquivo de áudio"""
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        return f"output_{timestamp}_{unique_id}.{extension}"
    
    def text_to_speech(
        self, 
        text: str, 
        voice_name: Optional[str] = None,
        language_code: Optional[str] = None,
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        volume_gain_db: float = 0.0
    ) -> Tuple[bool, str, Optional[str], Optional[float]]:
        """
        Converte texto em áudio usando Google Cloud Text-to-Speech
        
        Args:
            text: Texto para converter
            voice_name: Nome da voz (ex: "pt-BR-Wavenet-A")
            language_code: Código do idioma (ex: "pt-BR")
            speaking_rate: Velocidade da fala (0.25 a 4.0)
            pitch: Tom da voz (-20.0 a 20.0)
            volume_gain_db: Ganho de volume (-96.0 a 16.0)
            
        Returns:
            Tuple[success, message, audio_url, duration]
        """
        try:
            # Verificar se cliente está inicializado
            if not self._initialize_client():
                return False, "Erro ao inicializar cliente GCP", None, None
            
            # Validar texto de entrada
            if not text or text.strip() == "":
                return False, "Texto vazio ou inválido", None, None
            
            # Usar valores padrão se não especificados
            voice_name = voice_name or self.default_voice_name
            language_code = language_code or self.default_language_code
            
            # Validar voz usando a lista dinâmica do GCP
            available_voices_gcp = self.get_available_voices()
            if voice_name not in available_voices_gcp:
                logger.warning(f"Voz {voice_name} não encontrada no GCP, usando padrão {self.default_voice_name}")
                voice_name = self.default_voice_name
            
            # Gerar nome do arquivo
            filename = self.generate_filename("mp3")
            output_path = self.output_dir / filename
            
            logger.info(f"Gerando áudio para texto: '{text[:50]}...' (voz: {voice_name})")
            
            # Configurar entrada de texto
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configurar voz - usar informações do GCP se disponível, senão usar fallback
            voice_gender = texttospeech.SsmlVoiceGender.FEMALE  # padrão
            if voice_name in available_voices_gcp:
                gcp_voice_info = available_voices_gcp[voice_name]
                if gcp_voice_info.get("ssml_gender") == "MALE":
                    voice_gender = texttospeech.SsmlVoiceGender.MALE
                elif gcp_voice_info.get("ssml_gender") == "FEMALE":
                    voice_gender = texttospeech.SsmlVoiceGender.FEMALE
            elif voice_name in self.available_voices:
                # Fallback para lista hardcoded se não encontrar no GCP
                voice_gender = getattr(
                    texttospeech.SsmlVoiceGender, 
                    self.available_voices[voice_name]["gender"]
                )
            
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name,
                ssml_gender=voice_gender,
            )
            
            # Configurar áudio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=self.audio_encoding,
                sample_rate_hertz=self.sample_rate_hertz,
                speaking_rate=speaking_rate,
                pitch=pitch,
                volume_gain_db=volume_gain_db,
            )
            
            # Fazer a requisição para o GCP
            logger.info(f"Fazendo requisição para GCP TTS...")
            
            response = None
            for attempt in range(self.max_retries):
                try:
                    response = self.client.synthesize_speech(
                        input=synthesis_input,
                        voice=voice,
                        audio_config=audio_config
                    )
                    break  # Sucesso, sair do loop
                except gcp_exceptions.ServiceUnavailable as e:
                    logger.warning(f"⚠️ GCP indisponível (tentativa {attempt + 1}/{self.max_retries}): {e}")
                    if attempt + 1 == self.max_retries:
                        raise  # Levanta a exceção na última tentativa
                    time.sleep(self.initial_backoff * (2 ** attempt))
                except gcp_exceptions.GoogleAPICallError as e:
                    logger.error(f"❌ Erro na API do GCP (tentativa {attempt + 1}/{self.max_retries}): Status={e.code()} Details='{e.message}'")
                    # Erros como 'PERMISSION_DENIED' não devem ser repetidos
                    if e.code() == gcp_exceptions.StatusCode.PERMISSION_DENIED:
                        raise
                    
                    if attempt + 1 == self.max_retries:
                        raise
                    time.sleep(self.initial_backoff * (2 ** attempt))

            if response is None:
                return False, "Não foi possível obter resposta do GCP após várias tentativas.", None, None

            # Salvar o arquivo de áudio
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            
            # Verificar se o arquivo foi criado
            if not output_path.exists():
                return False, "Arquivo de áudio não foi criado", None, None
            
            # Calcular duração
            duration = self.get_audio_duration(str(output_path))
            
            # URL pública do arquivo
            audio_url = f"{self.base_url}/audio/{filename}"
            
            logger.info(f"✅ Áudio gerado com sucesso: {filename} (duração: {duration:.2f}s, voz: {voice_name})")
            
            return True, f"Áudio gerado com sucesso usando {voice_name}", audio_url, duration
            
        except gcp_exceptions.GoogleAPICallError as e:
            logger.error(f"❌ Erro final na API do GCP: Status={e.code()} Details='{e.message}'")
            return False, f"Erro final na API do GCP: {str(e)}", None, None
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao gerar áudio: {e}", exc_info=True)
            return False, f"Erro inesperado ao gerar áudio: {str(e)}", None, None
    
    def get_available_voices(self) -> Dict[str, Any]:
        """
        Retorna lista de vozes disponíveis
        """
        try:
            if not self._initialize_client():
                return {"error": "Cliente GCP não inicializado"}
            
            # Fazer requisição para listar vozes
            voices = self.client.list_voices(language_code=self.default_language_code)
            
            available = {}
            for voice in voices.voices:
                for language_code in voice.language_codes:
                    if language_code.startswith("pt-BR"):
                        available[voice.name] = {
                            "language_codes": list(voice.language_codes),
                            "ssml_gender": voice.ssml_gender.name,
                            "natural_sample_rate_hertz": voice.natural_sample_rate_hertz
                        }
            
            return available
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar vozes: {e}")
            return {"error": str(e)}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o serviço"""
        return {
            "service": "Google Cloud Text-to-Speech",
            "default_language": self.default_language_code,
            "default_voice": self.default_voice_name,
            "audio_encoding": self.audio_encoding.name,
            "sample_rate": self.sample_rate_hertz,
            "available_voices": self.available_voices,
            "output_dir": str(self.output_dir),
            "is_initialized": self.is_client_initialized(),
            "credentials_configured": bool(self.credentials_path)
        }
    
    def get_audio_duration(self, file_path: str) -> float:
        """Calcula duração do arquivo de áudio"""
        try:
            # Verificar se o caminho é válido
            if not file_path or not isinstance(file_path, (str, Path)):
                logger.error(f"Caminho do arquivo inválido: {file_path}")
                return 0.0
                
            file_path = str(file_path)
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
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Remove arquivos antigos do diretório de saída
        
        Args:
            max_age_hours: Idade máxima em horas para manter arquivos
            
        Returns:
            Dicionário com resultado da limpeza
        """
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            removed_count = 0
            removed_files = []
            
            for file_path in self.output_dir.glob("output_*.mp3"):
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    removed_count += 1
                    removed_files.append(file_path.name)
                    logger.info(f"Arquivo removido: {file_path.name}")
            
            if removed_count > 0:
                logger.info(f"Limpeza concluída: {removed_count} arquivos removidos")
            
            return {
                "success": True,
                "removed_count": removed_count,
                "removed_files": removed_files,
                "max_age_hours": max_age_hours
            }
            
        except Exception as e:
            logger.error(f"Erro na limpeza de arquivos: {e}")
            return {
                "success": False,
                "error": str(e),
                "removed_count": 0
            }
    
    def list_audio_files(self) -> Dict[str, Any]:
        """
        Lista arquivos de áudio no diretório de saída
        """
        try:
            files = []
            for file_path in self.output_dir.glob("output_*.mp3"):
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size_bytes": stat.st_size,
                    "created_at": stat.st_ctime,
                    "modified_at": stat.st_mtime,
                    "url": f"{self.base_url}/audio/{file_path.name}"
                })
            
            # Ordenar por data de criação (mais recente primeiro)
            files.sort(key=lambda x: x["created_at"], reverse=True)
            
            return {
                "success": True,
                "files": files,
                "total_count": len(files),
                "output_dir": str(self.output_dir)
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar arquivos: {e}")
            return {
                "success": False,
                "error": str(e),
                "files": []
            } 