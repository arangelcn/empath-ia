"""
Wrapper para processador de emoções faciais
Usa DeepFace como principal e Legacy como fallback para máxima compatibilidade
Permite forçar uso do Legacy através de variável de ambiente
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Verificar se deve usar processador legacy como fallback ou como principal
USE_LEGACY_FALLBACK = os.getenv("USE_LEGACY_FALLBACK", "true").lower() == "true"
FORCE_LEGACY_PROCESSOR = os.getenv("FORCE_LEGACY_PROCESSOR", "false").lower() == "true"


class FacialEmotionProcessor:
    """Wrapper que permite escolher entre DeepFace e Legacy como processador principal"""
    
    def __init__(self):
        self.primary_processor = None
        self.fallback_processor = None
        
        # Determinar qual processador usar como principal
        if FORCE_LEGACY_PROCESSOR:
            self._setup_legacy_as_primary()
        else:
            self._setup_deepface_as_primary()
    
    def _setup_legacy_as_primary(self):
        """Configura Legacy como processador principal"""
        try:
            logger.info("🔄 FORÇA LEGACY ATIVADA - Usando Legacy como processador principal...")
            from .facial_emotion_processor_legacy import FacialEmotionProcessor as LegacyProcessor
            self.primary_processor = LegacyProcessor()
            
            # Carregar DeepFace como fallback se desejado
            if USE_LEGACY_FALLBACK:
                try:
                    logger.info("Carregando processador DeepFace como fallback...")
                    from .deepface_processor import deepface_processor
                    self.fallback_processor = deepface_processor
                    logger.info("✅ Fallback DeepFace carregado com sucesso")
                except Exception as e:
                    logger.warning(f"⚠️ Não foi possível carregar fallback DeepFace: {e}")
            
            logger.info(f"✅ Processador inicializado - Principal: Legacy, Fallback: {'DeepFace' if self.fallback_processor else 'Nenhum'}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Legacy (forçado): {e}")
            logger.info("Fallback para DeepFace...")
            self._setup_deepface_as_primary()
    
    def _setup_deepface_as_primary(self):
        """Configura DeepFace como processador principal"""
        try:
            logger.info("Carregando processador DeepFace como principal...")
            from .deepface_processor import deepface_processor
            self.primary_processor = deepface_processor
            
            # Carregar fallback se habilitado
            if USE_LEGACY_FALLBACK:
                try:
                    logger.info("Carregando processador Legacy como fallback...")
                    from .facial_emotion_processor_legacy import FacialEmotionProcessor as LegacyProcessor
                    self.fallback_processor = LegacyProcessor()
                    logger.info("✅ Fallback Legacy carregado com sucesso")
                except Exception as e:
                    logger.warning(f"⚠️ Não foi possível carregar fallback Legacy: {e}")
            
            logger.info(f"✅ Processador inicializado - Principal: DeepFace, Fallback: {'Legacy' if self.fallback_processor else 'Nenhum'}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar DeepFace: {e}")
            logger.info("Tentando apenas processador Legacy...")
            
            # Fallback para apenas Legacy
            try:
                from .facial_emotion_processor_legacy import FacialEmotionProcessor as LegacyProcessor
                self.primary_processor = LegacyProcessor()
                logger.info("✅ Usando apenas processador Legacy")
            except Exception as legacy_e:
                logger.error(f"❌ Erro crítico - nenhum processador disponível: DeepFace={e}, Legacy={legacy_e}")
                raise RuntimeError("Nenhum processador de emoções disponível")
    
    def initialize(self):
        """Força inicialização dos processadores"""
        try:
            if hasattr(self.primary_processor, 'initialize'):
                self.primary_processor.initialize()
            
            if self.fallback_processor and hasattr(self.fallback_processor, 'initialize'):
                self.fallback_processor.initialize()
        except Exception as e:
            logger.warning(f"Erro na inicialização: {e}")
    
    def process_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Processa imagem usando processador principal, com fallback se falhar"""
        processor_name = "Legacy" if FORCE_LEGACY_PROCESSOR else "DeepFace"
        
        try:
            # Tentar processador principal
            result = self.primary_processor.process_image(image_path)
            if result is not None:
                result["processor_used"] = processor_name.lower()
                return result
            
            logger.warning(f"{processor_name} falhou, tentando fallback...")
            
        except Exception as e:
            logger.error(f"Erro no processador {processor_name}: {e}")
        
        # Tentar fallback se disponível
        if self.fallback_processor:
            try:
                fallback_name = "DeepFace" if FORCE_LEGACY_PROCESSOR else "Legacy"
                result = self.fallback_processor.process_image(image_path)
                if result is not None:
                    result["processor_used"] = fallback_name.lower()
                    return result
            except Exception as e:
                logger.error(f"Erro no processador fallback: {e}")
        
        logger.error("Todos os processadores falharam")
        return None
    
    def process_image_bytes(self, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """Processa bytes de imagem usando processador principal, com fallback se falhar"""
        processor_name = "Legacy" if FORCE_LEGACY_PROCESSOR else "DeepFace"
        
        try:
            # Tentar processador principal
            result = self.primary_processor.process_image_bytes(image_bytes)
            if result is not None:
                result["processor_used"] = processor_name.lower()
                return result
            
            logger.warning(f"{processor_name} falhou, tentando fallback...")
            
        except Exception as e:
            logger.error(f"Erro no processador {processor_name}: {e}")
        
        # Tentar fallback se disponível
        if self.fallback_processor:
            try:
                fallback_name = "DeepFace" if FORCE_LEGACY_PROCESSOR else "Legacy"
                result = self.fallback_processor.process_image_bytes(image_bytes)
                if result is not None:
                    result["processor_used"] = fallback_name.lower()
                    return result
            except Exception as e:
                logger.error(f"Erro no processador fallback: {e}")
        
        logger.error("Todos os processadores falharam")
        return None
    
    def get_emotional_interpretation(self, au_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Método de compatibilidade - retorna emoções diretamente do au_data
        """
        return au_data.get("emotions", {"neutral": 1.0})
    
    def cleanup(self):
        """Limpar recursos de todos os processadores"""
        try:
            if hasattr(self.primary_processor, 'cleanup'):
                self.primary_processor.cleanup()
            
            if self.fallback_processor and hasattr(self.fallback_processor, 'cleanup'):
                self.fallback_processor.cleanup()
        except Exception as e:
            logger.warning(f"Erro no cleanup: {e}")


# Criar instância global
try:
    facial_emotion_processor = FacialEmotionProcessor()
except Exception as e:
    logger.error(f"❌ Erro crítico ao inicializar processador: {e}")
    # Criar um processador dummy para evitar falhas de importação
    class DummyProcessor:
        def process_image(self, *args, **kwargs):
            return {"emotions": {"neutral": 1.0}, "dominant_emotion": "neutral", "confidence": 0.5}
        def process_image_bytes(self, *args, **kwargs):
            return {"emotions": {"neutral": 1.0}, "dominant_emotion": "neutral", "confidence": 0.5}
        def get_emotional_interpretation(self, *args, **kwargs):
            return {"neutral": 1.0}
        def initialize(self): pass
        def cleanup(self): pass
    
    facial_emotion_processor = DummyProcessor()
    logger.warning("⚠️ Usando processador dummy - funcionalidade limitada") 
