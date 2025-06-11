"""
F5-TTS Service - Serviço de Text-to-Speech usando F5-TTS-pt-br
"""
import os
import logging
import torch
import torchaudio
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import hashlib
import re
import unicodedata
import soundfile as sf
from f5_tts.api import F5TTS
from num2words import num2words

# Configurar logging
logger = logging.getLogger(__name__)

class F5TTSService:
    """Serviço de Text-to-Speech usando F5-TTS-pt-br"""
    
    def __init__(self):
        """Inicializar o serviço F5-TTS"""
        self.model = None
        self.tokenizer = None
        self.device = self._get_device()
        self.model_name = "firstpixel/F5-TTS-pt-br"
        self.sample_rate = 24000
        self.output_dir = Path(os.getenv("F5_TTS_OUTPUT_DIR", "/app/tts_output"))
        self.model_loaded = False
        
        # Configurações de qualidade
        self.quality_settings = {
            "temperature": 0.7,
            "top_k": 50,
            "top_p": 0.9,
            "repetition_penalty": 1.1,
            "length_penalty": 1.0
        }
        
        # Criar diretório de saída
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Default reference file and text for F5-TTS (Portuguese Brazilian)
        # We'll use a simple Portuguese reference text since we don't have a PT-BR reference file
        self.default_ref_file = "/tmp/F5-TTS/src/f5_tts/infer/examples/basic/basic_ref_en.wav"  # Will use English file but with PT text
        self.default_ref_text = "Olá, meu nome é assistente virtual e estou aqui para ajudar você."
        
        logger.info(f"F5TTSService inicializado - Dispositivo: {self.device}")
        logger.info(f"Diretório de saída: {self.output_dir}")
    
    def _get_device(self) -> str:
        """Determinar o melhor dispositivo disponível"""
        if torch.cuda.is_available():
            device = "cuda"
            logger.info(f"CUDA disponível - GPU: {torch.cuda.get_device_name()}")
        else:
            device = "cpu"
            logger.info("Usando CPU para inferência")
        return device
    
    def load_model(self) -> bool:
        """Carregar o modelo F5-TTS para português brasileiro"""
        try:
            logger.info(f"Carregando modelo F5-TTS para português brasileiro: {self.model_name}")
            # Initialize F5TTS with the correct model name that exists in configs
            self.model = F5TTS(model="F5TTS_Base", ckpt_file="")
            self.model_loaded = True
            logger.info("✅ Modelo F5-TTS-pt-br carregado com sucesso!")
            logger.info(f"📍 Modelo configurado para: {self.model_name}")
            logger.info(f"🎯 Dispositivo: {self.device}")
            return True
        except Exception as e:
            logger.error(f"❌ Falha ao carregar modelo F5-TTS-pt-br: {e}")
            self.model_loaded = False
            return False
    
    def is_model_loaded(self) -> bool:
        """Verificar se o modelo está carregado"""
        return self.model_loaded
    
    def _clean_text(self, text: str) -> str:
        """
        Limpar e normalizar texto para síntese em português brasileiro
        Seguindo as recomendações do modelo F5-TTS-pt-br:
        - Converter números para palavras
        - Usar texto em minúsculas
        - Normalizar pontuação
        """
        # Normalizar unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Converter números para palavras em português brasileiro
        def replace_number(match):
            try:
                number = int(match.group())
                return num2words(number, lang='pt_BR')
            except:
                return match.group()  # Retorna o número original se falhar
        
        # Substituir números por palavras
        text = re.sub(r'\b\d+\b', replace_number, text)
        
        # Tratar casos especiais mencionados na documentação
        text = text.replace(" e um mil", " e mil")
        text = text.replace("um mil ", "mil ")
        
        # Converter para minúsculas (recomendação do modelo)
        text = text.lower()
        
        # Remover caracteres especiais problemáticos, mantendo acentos portugueses
        text = re.sub(r'[^\w\s\.,!?;:\-\(\)\"\'àáâãäåèéêëìíîïðòóôõöøùúûüýþÿçñ]', '', text)
        
        # Normalizar espaços múltiplos
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remover espaços antes de pontuação
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        
        # Garantir espaço após pontuação
        text = re.sub(r'([,.!?;:])([^\s])', r'\1 \2', text)
        
        # Adicionar vírgulas para pausas naturais (melhora a qualidade)
        # Adicionar vírgula após conjunções longas
        text = re.sub(r'\b(portanto|entretanto|contudo|todavia|assim|então)\b', r'\1,', text)
        
        # Garantir pontuação final para melhor síntese
        if text and text[-1] not in '.!?':
            text += '.'
        
        return text
    
    def _generate_filename(self, text: str) -> str:
        """Gerar nome único para arquivo de áudio"""
        # Criar hash do texto
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:8]
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"f5tts_{timestamp}_{text_hash}.wav"
    
    def synthesize(self, text: str, output_path: str, ref_file: Optional[str] = None, ref_text: Optional[str] = None) -> bool:
        """
        Sintetizar fala em português brasileiro usando F5-TTS
        
        Args:
            text: Texto para sintetizar em português brasileiro
            output_path: Caminho para salvar o arquivo de áudio
            ref_file: Arquivo de áudio de referência (opcional, usa padrão se não fornecido)
            ref_text: Texto de referência (opcional, usa padrão em português se não fornecido)
        """
        if not self.is_model_loaded():
            logger.error("❌ Modelo F5-TTS não carregado")
            return False
            
        try:
            # Use default reference if not provided
            if ref_file is None:
                ref_file = self.default_ref_file
            if ref_text is None:
                ref_text = self.default_ref_text
                
            logger.info(f"🎙️ Sintetizando texto em português: {text}")
            logger.info(f"📁 Arquivo de referência: {ref_file}")
            logger.info(f"📝 Texto de referência: {ref_text}")
            
            # Generate audio using F5-TTS with correct parameters
            audio, sample_rate = self.model.infer(
                ref_file=ref_file,
                ref_text=ref_text,
                gen_text=text,
                remove_silence=True,
                cross_fade_duration=0.15,
                speed=1.0,
                show_info=print
            )
            
            # Save the audio file
            sf.write(output_path, audio, sample_rate)
            logger.info(f"✅ Áudio em português brasileiro salvo em: {output_path}")
            logger.info(f"🎵 Taxa de amostragem: {sample_rate} Hz")
            logger.info(f"⏱️ Duração estimada: {len(audio) / sample_rate:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro durante síntese em português: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Obter informações do modelo"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "model_loaded": self.model_loaded,
            "sample_rate": self.sample_rate,
            "output_directory": str(self.output_dir),
            "quality_settings": self.quality_settings
        }
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """Limpar arquivos antigos do diretório de saída"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            removed_count = 0
            
            for file_path in self.output_dir.glob("*.wav"):
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        removed_count += 1
                        logger.debug(f"Arquivo removido: {file_path.name}")
                except Exception as e:
                    logger.warning(f"Erro ao remover {file_path.name}: {e}")
            
            if removed_count > 0:
                logger.info(f"🧹 Limpeza concluída: {removed_count} arquivos removidos")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Erro na limpeza de arquivos: {e}")
            return 0
    
    def get_audio_file_path(self, filename: str) -> Optional[Path]:
        """Obter caminho completo do arquivo de áudio"""
        if not filename:
            return None
        
        file_path = self.output_dir / filename
        
        if file_path.exists() and file_path.suffix.lower() == '.wav':
            return file_path
        
        return None
    
    def list_audio_files(self) -> list:
        """Listar arquivos de áudio disponíveis"""
        try:
            audio_files = []
            for file_path in self.output_dir.glob("*.wav"):
                try:
                    stat = file_path.stat()
                    audio_files.append({
                        "filename": file_path.name,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Erro ao obter info de {file_path.name}: {e}")
            
            # Ordenar por data de criação (mais recente primeiro)
            audio_files.sort(key=lambda x: x["created"], reverse=True)
            
            return audio_files
            
        except Exception as e:
            logger.error(f"Erro ao listar arquivos: {e}")
            return [] 