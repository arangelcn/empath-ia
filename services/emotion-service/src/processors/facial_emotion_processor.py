"""
Processador de emoções faciais usando MediaPipe e regras baseadas em landmarks
Alternativa moderna e eficiente ao OpenFace sem dependências Docker
"""

import cv2
import mediapipe as mp
import numpy as np
import logging
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image
import io
import math

logger = logging.getLogger(__name__)

class FacialEmotionProcessor:
    """Processador de emoções faciais usando MediaPipe"""
    
    def __init__(self):
        # Inicializar MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        # Pontos-chave para análise emocional - ÍNDICES CORRETOS DO MEDIAPIPE
        self.landmark_indices = {
            # Olhos - baseado na documentação oficial
            'left_eye': [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246],
            'right_eye': [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398],
            
            # Sobrancelhas
            'left_eyebrow': [70, 63, 105, 66, 107, 55, 65, 52, 53, 46],
            'right_eyebrow': [296, 334, 293, 300, 276, 283, 282, 295, 285, 336],
            
            # Boca - índices corretos
            'mouth_outer': [61, 146, 91, 181, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318],
            'mouth_inner': [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308],
            
            # Pontos específicos para análise
            'mouth_corners': [61, 291],  # Cantos da boca
            'mouth_top': [13],           # Centro superior do lábio
            'mouth_bottom': [14],        # Centro inferior do lábio
            
            # Olhos - pontos específicos
            'left_eye_center': [159],
            'right_eye_center': [386],
            'left_eye_top': [159],
            'left_eye_bottom': [145],
            'right_eye_top': [386], 
            'right_eye_bottom': [374],
            
            # Sobrancelhas - pontos específicos
            'left_eyebrow_inner': [70],
            'left_eyebrow_outer': [46],
            'right_eyebrow_inner': [300],
            'right_eyebrow_outer': [285],
            
            # Nariz
            'nose_tip': [1],
            'nose_bridge': [6, 168, 8, 9, 10, 151]
        }
    
    def process_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Processa uma imagem para detectar emoções faciais
        
        Args:
            image_path: Caminho para a imagem
            
        Returns:
            Dict com dados das emoções ou None se falhar
        """
        try:
            # Carregar imagem
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return None
            
            # Converter BGR para RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Processar com MediaPipe
            results = self.face_mesh.process(rgb_image)
            
            if not results.multi_face_landmarks:
                logger.warning("No face detected in image")
                return None
            
            # Pegar primeiro rosto detectado
            face_landmarks = results.multi_face_landmarks[0]
            
            # Extrair coordenadas dos landmarks
            landmarks = self._extract_landmarks(face_landmarks, rgb_image.shape)
            
            # Analisar emoções
            emotions = self._analyze_emotions(landmarks)
            
            return {
                "success": True,
                "confidence": 0.85,  # MediaPipe não fornece confiança específica
                "face_detected": True,
                "emotions": emotions,
                "landmarks_count": len(landmarks),
                "image_size": rgb_image.shape[:2]
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return None
    
    def process_image_bytes(self, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """
        Processa uma imagem a partir de bytes (para base64)
        """
        try:
            # Converter bytes para array numpy
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error("Could not decode image from bytes")
                return None
            
            # Converter BGR para RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Processar com MediaPipe
            results = self.face_mesh.process(rgb_image)
            
            if not results.multi_face_landmarks:
                logger.warning("No face detected in image")
                return None
            
            # Pegar primeiro rosto detectado
            face_landmarks = results.multi_face_landmarks[0]
            
            # Extrair coordenadas dos landmarks
            landmarks = self._extract_landmarks(face_landmarks, rgb_image.shape)
            
            # Analisar emoções
            emotions = self._analyze_emotions(landmarks)
            
            return {
                "success": True,
                "confidence": 0.85,
                "face_detected": True,
                "emotions": emotions,
                "landmarks_count": len(landmarks),
                "image_size": rgb_image.shape[:2]
            }
            
        except Exception as e:
            logger.error(f"Error processing image bytes: {e}")
            return None
    
    def _extract_landmarks(self, face_landmarks, image_shape) -> List[Tuple[float, float]]:
        """Extrai coordenadas dos landmarks faciais"""
        height, width = image_shape[:2]
        landmarks = []
        
        for landmark in face_landmarks.landmark:
            x = landmark.x * width
            y = landmark.y * height
            landmarks.append((x, y))
        
        return landmarks
    
    def _analyze_emotions(self, landmarks: List[Tuple[float, float]]) -> Dict[str, float]:
        """
        Analisa emoções baseadas nos landmarks faciais - versão simplificada
        """
        emotions = {
            "joy": 0.0,
            "sadness": 0.0,
            "anger": 0.0,
            "surprise": 0.0,
            "fear": 0.0,
            "disgust": 0.0,
            "neutral": 0.0
        }
        
        try:
            # Análise da boca (sorriso/tristeza)
            mouth_score = self._analyze_mouth(landmarks)
            
            # Análise dos olhos (surpresa/raiva)
            eye_score = self._analyze_eyes(landmarks)
            
            # Análise das sobrancelhas (raiva/surpresa/medo)
            eyebrow_score = self._analyze_eyebrows(landmarks)
            
            # Log para debug - sempre aparece
            print(f"[DEBUG] Mouth: {mouth_score:.3f}, Eyes: {eye_score:.3f}, Eyebrows: {eyebrow_score:.3f}")
            logger.info(f"[DEBUG] Mouth: {mouth_score:.3f}, Eyes: {eye_score:.3f}, Eyebrows: {eyebrow_score:.3f}")
            
            # LÓGICA SIMPLIFICADA - começar do zero
            
            # 1. Análise de SORRISO - mais sensível
            if mouth_score > 0.05:  # Threshold muito baixo
                joy_score = min(mouth_score * 5.0, 1.0)  # Amplificar muito
                emotions["joy"] = joy_score
                print(f"[DEBUG] JOY detected: {joy_score:.3f}")
                
            # 2. Análise de TRISTEZA 
            elif mouth_score < -0.05:  # Threshold baixo
                sadness_score = min(abs(mouth_score) * 3.0, 1.0)
                emotions["sadness"] = sadness_score
                print(f"[DEBUG] SADNESS detected: {sadness_score:.3f}")
            
            # 3. Análise de SURPRESA - apenas se olhos muito abertos
            if eye_score > 0.8:  # Threshold muito alto
                surprise_score = min(eye_score * 0.5, 0.8)
                emotions["surprise"] = surprise_score
                print(f"[DEBUG] SURPRISE detected: {surprise_score:.3f}")
            
            # 4. Análise de RAIVA - sobrancelhas franzidas
            if eyebrow_score < -0.3:
                anger_score = min(abs(eyebrow_score) * 2.0, 1.0)
                emotions["anger"] = anger_score
                print(f"[DEBUG] ANGER detected: {anger_score:.3f}")
            
            # 5. Se não detectou nada significativo, é NEUTRO
            total_emotion = sum(emotions.values())
            if total_emotion < 0.2:
                emotions["neutral"] = 1.0
                print(f"[DEBUG] NEUTRAL - total emotion too low: {total_emotion:.3f}")
            else:
                # Distribuir o restante como neutro se necessário
                emotions["neutral"] = max(0.0, 0.3 - total_emotion)
            
            # Normalizar
            total = sum(emotions.values())
            if total > 0:
                emotions = {k: v/total for k, v in emotions.items()}
            else:
                emotions = {"neutral": 1.0}
            
            # Filtrar valores muito baixos
            filtered_emotions = {k: v for k, v in emotions.items() if v > 0.1}
            if not filtered_emotions:
                filtered_emotions = {"neutral": 1.0}
            else:
                # Re-normalizar
                total_filtered = sum(filtered_emotions.values())
                filtered_emotions = {k: v/total_filtered for k, v in filtered_emotions.items()}
            
            # Log resultado final
            dominant = max(filtered_emotions, key=filtered_emotions.get)
            print(f"[DEBUG] Final: {filtered_emotions}")
            print(f"[DEBUG] Dominant: {dominant} ({filtered_emotions[dominant]:.3f})")
            logger.info(f"[DEBUG] Final emotions: {filtered_emotions}, Dominant: {dominant}")
            
            return filtered_emotions
            
        except Exception as e:
            print(f"[ERROR] Exception in _analyze_emotions: {e}")
            logger.error(f"Error analyzing emotions: {e}")
            return {"neutral": 1.0}
    
    def _analyze_mouth(self, landmarks: List[Tuple[float, float]]) -> float:
        """Analisa a curvatura da boca - versão corrigida com índices validados"""
        try:
            # Verificar se temos landmarks suficientes
            if len(landmarks) < 468:
                print(f"[WARNING] Insufficient landmarks: {len(landmarks)}, expected 468")
                return 0.0
            
            # Pontos dos cantos da boca - ÍNDICES CORRETOS
            left_corner = landmarks[61]   # Canto esquerdo da boca
            right_corner = landmarks[291] # Canto direito da boca
            center_top = landmarks[13]    # Centro superior do lábio
            center_bottom = landmarks[14] # Centro inferior do lábio
            
            print(f"[DEBUG] Mouth points - Left: {left_corner}, Right: {right_corner}, Top: {center_top}, Bottom: {center_bottom}")
            
            # Calcular curvatura mais precisa
            mouth_width = abs(right_corner[0] - left_corner[0])
            if mouth_width == 0:
                return 0.0
                
            mouth_center_y = (left_corner[1] + right_corner[1]) / 2
            lip_center_y = (center_top[1] + center_bottom[1]) / 2
            
            # Diferença relativa à largura da boca
            y_diff = (mouth_center_y - lip_center_y)
            curvature = y_diff / mouth_width
            
            print(f"[DEBUG] Mouth analysis - Width: {mouth_width:.3f}, Y_diff: {y_diff:.3f}, Curvature: {curvature:.3f}")
            
            # Aplicar função de suavização para evitar valores extremos
            smoothed_curvature = math.tanh(curvature * 3)  # Reduzir multiplicador
            
            return smoothed_curvature
            
        except (IndexError, ZeroDivisionError) as e:
            print(f"[ERROR] Mouth analysis error: {e}")
            return 0.0
    
    def _analyze_eyes(self, landmarks: List[Tuple[float, float]]) -> float:
        """Analisa a abertura dos olhos - versão corrigida"""
        try:
            # Verificar se temos landmarks suficientes
            if len(landmarks) < 468:
                return 0.0
            
            # Olho esquerdo - ÍNDICES CORRETOS
            left_eye_top = landmarks[159]    # Ponto superior do olho esquerdo
            left_eye_bottom = landmarks[145] # Ponto inferior do olho esquerdo
            left_eye_left = landmarks[33]    # Canto interno do olho esquerdo
            left_eye_right = landmarks[133]  # Canto externo do olho esquerdo
            
            # Olho direito - ÍNDICES CORRETOS
            right_eye_top = landmarks[386]    # Ponto superior do olho direito
            right_eye_bottom = landmarks[374] # Ponto inferior do olho direito
            right_eye_left = landmarks[362]   # Canto interno do olho direito
            right_eye_right = landmarks[263]  # Canto externo do olho direito
            
            # Calcular proporção altura/largura para cada olho
            left_eye_height = abs(left_eye_top[1] - left_eye_bottom[1])
            left_eye_width = abs(left_eye_right[0] - left_eye_left[0])
            
            right_eye_height = abs(right_eye_top[1] - right_eye_bottom[1])
            right_eye_width = abs(right_eye_right[0] - right_eye_left[0])
            
            print(f"[DEBUG] Eyes - Left H/W: {left_eye_height:.3f}/{left_eye_width:.3f}, Right H/W: {right_eye_height:.3f}/{right_eye_width:.3f}")
            
            # Evitar divisão por zero
            if left_eye_width == 0 or right_eye_width == 0:
                return 0.0
            
            # Proporção altura/largura (olhos arregalados têm proporção maior)
            left_ratio = left_eye_height / left_eye_width
            right_ratio = right_eye_height / right_eye_width
            
            avg_ratio = (left_ratio + right_ratio) / 2
            
            print(f"[DEBUG] Eye ratios - Left: {left_ratio:.3f}, Right: {right_ratio:.3f}, Avg: {avg_ratio:.3f}")
            
            # Normalizar - valores típicos estão entre 0.1 e 0.4
            # Ajustar range para ser menos sensível
            normalized_score = max(0, min(1, (avg_ratio - 0.2) / 0.3))
            
            return normalized_score
            
        except (IndexError, ZeroDivisionError) as e:
            print(f"[ERROR] Eyes analysis error: {e}")
            return 0.0
    
    def _analyze_eyebrows(self, landmarks: List[Tuple[float, float]]) -> float:
        """Analisa a posição das sobrancelhas - versão corrigida"""
        try:
            # Verificar se temos landmarks suficientes
            if len(landmarks) < 468:
                return 0.0
            
            # Pontos das sobrancelhas - ÍNDICES CORRETOS
            left_brow_inner = landmarks[70]   # Sobrancelha esquerda interna
            left_brow_outer = landmarks[46]   # Sobrancelha esquerda externa
            left_eye_center = landmarks[159]  # Centro do olho esquerdo
            
            right_brow_inner = landmarks[300] # Sobrancelha direita interna
            right_brow_outer = landmarks[285] # Sobrancelha direita externa
            right_eye_center = landmarks[386] # Centro do olho direito
            
            # Calcular distância vertical média das sobrancelhas aos olhos
            left_brow_y = (left_brow_inner[1] + left_brow_outer[1]) / 2
            right_brow_y = (right_brow_inner[1] + right_brow_outer[1]) / 2
            
            left_distance = left_eye_center[1] - left_brow_y
            right_distance = right_eye_center[1] - right_brow_y
            
            avg_distance = (left_distance + right_distance) / 2
            
            print(f"[DEBUG] Eyebrows - Left dist: {left_distance:.3f}, Right dist: {right_distance:.3f}, Avg: {avg_distance:.3f}")
            
            # Normalizar baseado em proporções faciais típicas
            # Valores positivos = sobrancelhas levantadas
            # Valores negativos = sobrancelhas franzidas
            normalized_score = avg_distance / 25  # Ajustar divisor
            
            # Limitar entre -1 e 1
            normalized_score = max(-1, min(1, normalized_score))
            
            return normalized_score
            
        except (IndexError, ZeroDivisionError) as e:
            print(f"[ERROR] Eyebrows analysis error: {e}")
            return 0.0
    
    def debug_landmarks(self, landmarks: List[Tuple[float, float]]) -> Dict[str, Any]:
        """Método para debug detalhado dos landmarks"""
        try:
            debug_info = {
                "total_landmarks": len(landmarks),
                "mouth_landmarks": {},
                "eye_landmarks": {},
                "eyebrow_landmarks": {}
            }
            
            # Verificar se os índices existem
            key_indices = [61, 291, 13, 14, 159, 145, 386, 374, 70, 300]
            for idx in key_indices:
                if idx < len(landmarks):
                    debug_info[f"landmark_{idx}"] = landmarks[idx]
                else:
                    debug_info[f"landmark_{idx}"] = "INDEX_OUT_OF_RANGE"
            
            return debug_info
            
        except Exception as e:
            return {"error": str(e)}

    def _classify_emotion(self, mouth_score: float, eye_score: float, eyebrow_score: float) -> Tuple[str, float]:
        """Classifica a emoção baseada nos scores - versão corrigida e calibrada"""
        
        print(f"[DEBUG] Classification input - Mouth: {mouth_score:.3f}, Eyes: {eye_score:.3f}, Eyebrows: {eyebrow_score:.3f}")
        
        # Dicionário para armazenar scores de cada emoção
        emotion_scores = {
            'happy': 0.0,
            'sad': 0.0,
            'angry': 0.0,
            'surprised': 0.0,
            'fear': 0.0,
            'disgust': 0.0,
            'neutral': 0.0
        }
        
        # FELICIDADE - boca curvada para cima, olhos podem estar mais fechados (sorriso)
        if mouth_score > 0.1:  # Boca curvada para cima
            emotion_scores['happy'] = mouth_score * 0.7
            if eye_score < 0.4:  # Olhos ligeiramente fechados (sorriso genuíno)
                emotion_scores['happy'] += 0.2
            if eyebrow_score > -0.1:  # Sobrancelhas neutras ou ligeiramente levantadas
                emotion_scores['happy'] += 0.1
        
        # TRISTEZA - boca curvada para baixo, sobrancelhas baixas
        if mouth_score < -0.1:  # Boca curvada para baixo
            emotion_scores['sad'] = abs(mouth_score) * 0.6
            if eyebrow_score < -0.2:  # Sobrancelhas franzidas/baixas
                emotion_scores['sad'] += 0.3
            if eye_score < 0.3:  # Olhos mais fechados
                emotion_scores['sad'] += 0.1
        
        # RAIVA - boca tensa, sobrancelhas franzidas, olhos normais/abertos
        if eyebrow_score < -0.3:  # Sobrancelhas muito franzidas
            emotion_scores['angry'] = abs(eyebrow_score) * 0.5
            if mouth_score < 0.05 and mouth_score > -0.05:  # Boca tensa (neutra)
                emotion_scores['angry'] += 0.2
            if eye_score > 0.3:  # Olhos abertos/tensos
                emotion_scores['angry'] += 0.2
        
        # SURPRESA - olhos muito abertos, sobrancelhas levantadas, boca aberta
        if eye_score > 0.6:  # Olhos muito abertos
            emotion_scores['surprised'] = eye_score * 0.5
            if eyebrow_score > 0.3:  # Sobrancelhas levantadas
                emotion_scores['surprised'] += 0.3
            if abs(mouth_score) < 0.1:  # Boca neutra/ligeiramente aberta
                emotion_scores['surprised'] += 0.2
        
        # MEDO - olhos abertos, sobrancelhas levantadas, boca ligeiramente aberta
        if eye_score > 0.4 and eyebrow_score > 0.2:
            emotion_scores['fear'] = (eye_score + eyebrow_score) * 0.3
            if abs(mouth_score) < 0.15:  # Boca neutra
                emotion_scores['fear'] += 0.1
        
        # NOJO - boca curvada para baixo, sobrancelhas franzidas
        if mouth_score < -0.2 and eyebrow_score < -0.1:
            emotion_scores['disgust'] = (abs(mouth_score) + abs(eyebrow_score)) * 0.3
        
        # NEUTRO - valores próximos ao centro
        neutral_threshold = 0.15
        if (abs(mouth_score) < neutral_threshold and 
            abs(eyebrow_score) < neutral_threshold and 
            eye_score < 0.5):
            emotion_scores['neutral'] = 0.6 - (abs(mouth_score) + abs(eyebrow_score) + eye_score * 0.2)
        
        print(f"[DEBUG] Emotion scores: {emotion_scores}")
        
        # Encontrar a emoção com maior score
        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        # Se nenhuma emoção tem score significativo, retornar neutro
        if dominant_emotion[1] < 0.1:
            return 'neutral', 0.5
        
        # Normalizar confiança entre 0.5 e 1.0
        confidence = min(1.0, max(0.5, dominant_emotion[1]))
        
        print(f"[DEBUG] Final classification: {dominant_emotion[0]} with confidence {confidence:.3f}")
        
        return dominant_emotion[0], confidence

# Instância global
facial_emotion_processor = FacialEmotionProcessor() 