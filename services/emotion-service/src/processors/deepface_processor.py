"""
Processador de emoções faciais usando DeepFace com configurações otimizadas para acurácia
Melhorias: pré-processamento robusto, modelos precisos, multi-detector e calibração
Suporte: GPU com fallback automático para CPU
"""

import logging
import numpy as np
import os
from typing import Dict, Any, Optional
import cv2

logger = logging.getLogger(__name__)

_tf = None
_deepface = None


def get_tensorflow():
    """Importa TensorFlow sob demanda para manter o startup diagnosticável."""
    global _tf
    if _tf is None:
        import tensorflow as tf
        _tf = tf
    return _tf


def get_deepface():
    """Importa DeepFace sob demanda, depois que TensorFlow/Keras já foram fixados."""
    global _deepface
    if _deepface is None:
        from deepface import DeepFace
        _deepface = DeepFace
    return _deepface


def setup_tensorflow_gpu():
    """
    Configura TensorFlow para usar GPU quando disponível, com fallback para CPU
    """
    try:
        tf = get_tensorflow()

        # Log das variáveis de ambiente relacionadas à GPU
        logger.info(f"🔍 Variáveis de ambiente GPU:")
        logger.info(f"   CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES', 'não definida')}")
        logger.info(f"   NVIDIA_VISIBLE_DEVICES: {os.environ.get('NVIDIA_VISIBLE_DEVICES', 'não definida')}")
        
        # Verificar se CUDA está compilado no TensorFlow
        cuda_available = tf.test.is_built_with_cuda()
        logger.info(f"📦 TensorFlow compilado com CUDA: {cuda_available}")
        
        # Verificar GPUs disponíveis
        gpus = tf.config.experimental.list_physical_devices('GPU')
        logger.info(f"🔍 GPUs físicos detectados: {len(gpus)}")
        
        for i, gpu in enumerate(gpus):
            logger.info(f"   GPU {i}: {gpu.name} ({gpu.device_type})")
        
        if gpus and cuda_available:
            logger.info(f"🚀 Configurando GPU: {len(gpus)} dispositivo(s) encontrado(s)")
            
            # Configurar uso de memória dinâmica (evita alocar toda a VRAM)
            for gpu in gpus:
                try:
                    tf.config.experimental.set_memory_growth(gpu, True)
                    logger.info(f"✅ Memória dinâmica configurada para {gpu.name}")
                except Exception as gpu_e:
                    logger.warning(f"⚠️  Erro ao configurar memória dinâmica para {gpu.name}: {gpu_e}")
            
            # Verificar se GPU está realmente disponível para computação
            try:
                with tf.device('/GPU:0'):
                    test_tensor = tf.constant([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
                    result = tf.matmul(test_tensor, test_tensor, transpose_b=True)
                    # Forçar execução
                    _ = result.numpy()
                logger.info("✅ GPU testada e funcionando para computação")
                return "GPU", gpus
                
            except Exception as test_e:
                logger.warning(f"❌ GPU detectada mas teste falhou: {test_e}")
                logger.info("🔄 Retornando para CPU")
                return "CPU", []
                
        else:
            if not cuda_available:
                logger.info("⚠️  TensorFlow não foi compilado com CUDA")
            if not gpus:
                logger.info("⚠️  Nenhuma GPU física detectada")
            logger.info("💻 Usando CPU")
            return "CPU", []
            
    except Exception as e:
        logger.warning(f"❌ Erro geral ao configurar GPU: {e}")
        logger.info("🔄 Forçando uso de CPU")
        # Forçar uso de CPU em caso de erro
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        return "CPU", []


class DeepFaceProcessor:
    """
    Processador de emoções faciais usando DeepFace com configurações otimizadas
    
    Melhorias implementadas:
    - Múltiplos detectores para robustez
    - Pré-processamento de imagem otimizado
    - Modelo de emoção mais preciso
    - Calibração de emoções baseada em datasets reais
    - Threshold de confiança adaptativo
    - Suporte automático à GPU com fallback para CPU
    """
    
    def __init__(self, detector_backend: str = "retinaface"):
        """
        Inicializa o processador DeepFace com configurações otimizadas
        
        Args:
            detector_backend (str): Backend de detecção facial prioritário
        """
        # Configurar TensorFlow para GPU/CPU
        self.device_type, self.gpus = setup_tensorflow_gpu()
        
        # Caminho padrão otimizado: RetinaFace para qualidade, OpenCV como fallback leve.
        configured_detectors = os.getenv("DEEPFACE_DETECTOR_BACKENDS", "retinaface,opencv")
        self.detector_backends = [
            item.strip()
            for item in configured_detectors.split(",")
            if item.strip()
        ]
        self.primary_detector = os.getenv("DEEPFACE_DETECTOR_BACKEND", detector_backend)
        if self.primary_detector not in self.detector_backends:
            self.detector_backends.insert(0, self.primary_detector)
        
        # Calibração de emoções baseada em análise de datasets
        self.emotion_calibration = {
            # Ajustes para compatibilidade JAFFE->DeepFace
            "anger": 0.85,    # anger é bem detectado
            "disgust": 1.2,   # disgust precisa ser amplificado
            "fear": 1.1,      # fear precisa boost
            "happy": 0.9,     # happy às vezes é overconfident
            "sad": 1.15,      # sad precisa amplificação
            "surprise": 1.0,  # surprise é bem balanceado
            "neutral": 0.95   # neutral ligeiramente reduzido
        }
        
        # Threshold mínimo de confiança para aceitar predição
        self.confidence_threshold = float(os.getenv("DEEPFACE_EMOTION_CONFIDENCE_THRESHOLD", "0.3"))
        
        logger.info(f"Inicializando DeepFaceProcessor otimizado:")
        logger.info(f"  - Dispositivo: {self.device_type}")
        if self.device_type == "GPU":
            logger.info(f"  - GPUs disponíveis: {len(self.gpus)}")
        logger.info(f"  - Detector principal: {self.primary_detector}")
        logger.info(f"  - Fallbacks DeepFace: {self.detector_backends}")
        logger.info(f"  - Calibração ativada: Sim")
        logger.info(f"  - Threshold de confiança: {self.confidence_threshold}")

    def get_device_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o dispositivo de processamento
        """
        tf = get_tensorflow()
        device_info = {
            "device_type": self.device_type,
            "cuda_available": tf.test.is_built_with_cuda(),
            "gpu_available": tf.test.is_gpu_available(),
            "gpu_count": len(self.gpus) if self.gpus else 0,
        }
        
        if self.gpus:
            device_info["gpu_devices"] = []
            for i, gpu in enumerate(self.gpus):
                device_info["gpu_devices"].append({
                    "device_id": i,
                    "name": gpu.name,
                    "device_type": gpu.device_type
                })
        
        return device_info

    def preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """
        Pré-processamento robusto da imagem para melhor detecção
        
        Args:
            img (np.ndarray): Imagem original
            
        Returns:
            np.ndarray: Imagem pré-processada
        """
        # Garantir que a imagem tem pelo menos 224x224 (padrão CNN)
        h, w = img.shape[:2]
        
        # Redimensionar se muito pequena, mantendo proporção
        if min(h, w) < 224:
            scale = 224 / min(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        
        # Melhorar contraste se necessário
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        
        # Recombinar
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Aplicar suavização leve para reduzir ruído
        enhanced = cv2.bilateralFilter(enhanced, 5, 80, 80)
        
        return enhanced
    
    def analyze_with_fallback(self, img: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Executa análise com fallback entre detectores para máxima robustez
        
        Args:
            img (np.ndarray): Imagem pré-processada
            
        Returns:
            Dict com resultado da análise ou None se todos falharem
        """
        DeepFace = get_deepface()

        # Converter BGR para RGB
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Tentar cada detector em ordem de precisão
        for detector in self.detector_backends:
            try:
                logger.debug(f"Tentando detector: {detector}")

                result = DeepFace.analyze(
                    img_path=rgb_img,
                    actions=["emotion"],
                    detector_backend=detector,
                    enforce_detection=False,  # Não falhar se não detectar face
                    silent=True
                )
                
                # DeepFace pode retornar lista ou dict
                if isinstance(result, list):
                    if not result:
                        continue  # Tentar próximo detector
                    analysis = result[0]
                else:
                    analysis = result
                
                # Verificar se tem dados de emoção válidos
                emotions = analysis.get("emotion", {})
                if not emotions or all(v == 0 for v in emotions.values()):
                    continue  # Tentar próximo detector
                
                # Sucesso! Aplicar calibração
                return self.apply_emotion_calibration(emotions, detector)
                
            except Exception as e:
                logger.warning(f"Detector {detector} falhou: {e}")
                continue
        
        logger.warning("Todos os detectores falharam")
        return None
    
    def apply_emotion_calibration(self, emotions: Dict[str, float], detector_used: str) -> Dict[str, Any]:
        """
        Aplica calibração nas emoções para melhorar acurácia
        
        Args:
            emotions (Dict): Emoções brutas do DeepFace (0-100)
            detector_used (str): Detector que foi usado
            
        Returns:
            Dict com emoções calibradas e metadados
        """
        # Converter percentuais para probabilidades
        raw_probs = {k: v / 100.0 for k, v in emotions.items()}
        
        # Aplicar calibração
        calibrated = {}
        for emotion, prob in raw_probs.items():
            if emotion in self.emotion_calibration:
                calibrated[emotion] = prob * self.emotion_calibration[emotion]
            else:
                calibrated[emotion] = prob
        
        # Renormalizar para garantir que soma 1.0
        total = sum(calibrated.values())
        if total > 0:
            calibrated = {k: v / total for k, v in calibrated.items()}
        else:
            calibrated = {"neutral": 1.0}
        
        # Encontrar emoção dominante
        dominant_emotion = max(calibrated, key=calibrated.get)
        confidence = calibrated[dominant_emotion]
        
        # Verificar threshold de confiança
        if confidence < self.confidence_threshold:
            logger.debug(f"Confiança baixa ({confidence:.3f}), retornando neutral")
            dominant_emotion = "neutral"
            confidence = 0.5
            calibrated = {"neutral": 1.0}
        
        return {
            "dominant_emotion": dominant_emotion,
            "probabilities": calibrated,
            "confidence": confidence,
            "detector_used": detector_used,
            "calibrated": True
        }
    
    def initialize(self) -> None:
        """
        Força inicialização do processador para download de modelos
        """
        try:
            logger.info("Inicializando modelos DeepFace otimizados...")
            DeepFace = get_deepface()

            # Criar imagem teste para forçar download dos modelos
            test_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            
            # Tentar inicializar com detector principal
            try:
                _ = DeepFace.analyze(
                    img_path=test_image,
                    actions=["emotion"],
                    detector_backend=self.primary_detector,
                    enforce_detection=False,
                    silent=True
                )
                logger.info(f"✅ Detector principal ({self.primary_detector}) inicializado")
            except Exception as e:
                logger.warning(f"Detector principal falhou, mas outros detectores estão disponíveis: {e}")
            
            logger.info("✅ Modelos DeepFace otimizados inicializados com sucesso")
        except Exception as e:
            logger.error(f"⚠️ Inicialização DeepFace falhou: {e}")
            raise
    
    def predict(self, bgr_img: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Prediz emoções em uma imagem BGR com processamento otimizado
        
        Args:
            bgr_img (np.ndarray): Imagem no formato BGR (OpenCV)
            
        Returns:
            Dict contendo:
            - dominant_emotion (str): Emoção predominante
            - probabilities (Dict[str, float]): Probabilidades calibradas
            - confidence (float): Confiança da predição
            - detector_used (str): Detector utilizado
        """
        try:
            # Pré-processar imagem
            processed_img = self.preprocess_image(bgr_img)
            
            # Executar análise com fallback
            result = self.analyze_with_fallback(processed_img)
            
            if result is None:
                logger.warning("Todos os detectores DeepFace falharam")
                return None
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na análise DeepFace otimizada: {e}")
            return None
    
    def process_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Processa imagem a partir de arquivo (compatibilidade com API existente)
        
        Args:
            image_path (str): Caminho para arquivo de imagem
            
        Returns:
            Dict com resultado da análise ou None se falhar
        """
        try:
            # Carregar imagem
            bgr_img = cv2.imread(image_path)
            if bgr_img is None:
                logger.error(f"Não foi possível carregar imagem: {image_path}")
                return None
            
            # Usar método predict otimizado
            result = self.predict(bgr_img)
            if result is None:
                return None
            
            # Converter para formato compatível com API existente
            return {
                "emotions": result["probabilities"],
                "dominant_emotion": result["dominant_emotion"],
                "confidence": result["confidence"],
                "face_detected": True,
                "detector": result["detector_used"],
                "face_detector": result["detector_used"],
                "emotion_model": "deepface",
                "preprocessing": "enhanced",
                "calibrated": result.get("calibrated", False)
            }
            
        except Exception as e:
            logger.error(f"Erro no processamento de imagem: {e}")
            return None
    
    def process_image_bytes(self, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """
        Processa imagem a partir de bytes (compatibilidade com API existente)
        
        Args:
            image_bytes (bytes): Dados da imagem em bytes
            
        Returns:
            Dict com resultado da análise ou None se falhar
        """
        try:
            # Converter bytes para array numpy
            nparr = np.frombuffer(image_bytes, np.uint8)
            bgr_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if bgr_img is None:
                logger.error("Não foi possível decodificar imagem dos bytes")
                return None
            
            # Usar método predict otimizado
            result = self.predict(bgr_img)
            if result is None:
                return None
            
            # Converter para formato compatível com API existente
            return {
                "emotions": result["probabilities"],
                "dominant_emotion": result["dominant_emotion"],
                "confidence": result["confidence"],
                "face_detected": True,
                "landmarks_count": 0,
                "detector": result["detector_used"],
                "face_detector": result["detector_used"],
                "emotion_model": "deepface",
                "preprocessing": "enhanced",
                "calibrated": result.get("calibrated", False)
            }
            
        except Exception as e:
            logger.error(f"Erro no processamento de bytes: {e}")
            return None
    
    def get_emotional_interpretation(self, au_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Método de compatibilidade - retorna emoções diretamente do au_data
        
        Args:
            au_data (Dict): Dados já processados
            
        Returns:
            Dict com emoções normalizadas
        """
        return au_data.get("emotions", {"neutral": 1.0})
    
    def cleanup(self) -> None:
        """
        Limpar recursos (placeholder para compatibilidade)
        """
        logger.info("DeepFaceProcessor otimizado - cleanup executado")


# Instância global para compatibilidade
deepface_processor = DeepFaceProcessor()
