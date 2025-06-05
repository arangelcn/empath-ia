"""
Integração com o serviço OpenFace para análise de expressões faciais
"""

import os
import subprocess
import pandas as pd
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class OpenFaceProcessor:
    """Classe para processar imagens usando o serviço OpenFace via Docker"""
    
    def __init__(self, shared_data_dir: str = None):
        # Determinar o caminho do diretório compartilhado
        if shared_data_dir is None:
            # Se estamos dentro do container backend, usar caminho absoluto
            if os.path.exists("/app"):
                shared_data_dir = "/shared_data"
            else:
                # Se estamos no desenvolvimento local, usar caminho relativo
                current_dir = Path(__file__).parent
                # Navegar até a raiz do projeto (backend/app/utils -> ../../..)
                project_root = current_dir.parent.parent.parent
                shared_data_dir = str(project_root / "shared_data")
        
        self.shared_data_dir = Path(shared_data_dir)
        self.input_path = self.shared_data_dir / "input.jpg"
        self.output_path = self.shared_data_dir / "AU_output.csv"
        
        # Garantir que o diretório existe
        self.shared_data_dir.mkdir(exist_ok=True)
    
    def process_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Processa uma imagem para extrair Unidades de Ação
        
        Args:
            image_path: Caminho para a imagem a ser processada
            
        Returns:
            Dict com dados das AUs ou None se falhar
        """
        try:
            # Limpar arquivos anteriores
            self._cleanup_files()
            
            # Copiar imagem para o diretório compartilhado
            self._copy_input_image(image_path)
            
            # Executar processamento OpenFace
            success = self._run_openface()
            
            if success and self.output_path.exists():
                # Ler e processar resultados
                return self._parse_results()
            else:
                logger.error("OpenFace processing failed or output file not found")
                return None
                
        except Exception as e:
            logger.error(f"Error processing image with OpenFace: {e}")
            return None
    
    def _cleanup_files(self):
        """Remove arquivos anteriores"""
        for file_path in [self.input_path, self.output_path]:
            if file_path.exists():
                file_path.unlink()
    
    def _copy_input_image(self, image_path: str):
        """Copia a imagem para o diretório compartilhado"""
        import shutil
        shutil.copy2(image_path, self.input_path)
        logger.info(f"Image copied to {self.input_path}")
    
    def _run_openface(self) -> bool:
        """Executa o container OpenFace"""
        try:
            logger.info("Starting OpenFace processing...")
            
            # Determinar o diretório de trabalho correto para docker-compose
            if os.path.exists("/app"):
                # Estamos dentro do container backend - precisamos executar do host
                # Isso não funcionará dentro do container, então vamos usar uma abordagem diferente
                logger.error("Cannot run docker-compose from inside container. OpenFace processing should be called from outside.")
                return False
            else:
                # Estamos no desenvolvimento local
                current_dir = Path(__file__).parent
                project_root = current_dir.parent.parent.parent
                working_dir = str(project_root)
            
            # Executar o container OpenFace
            result = subprocess.run([
                "docker", "compose", "run", "--rm", "openface"
            ], 
            capture_output=True, 
            text=True,
            cwd=working_dir
            )
            
            if result.returncode == 0:
                logger.info("OpenFace processing completed successfully")
                logger.debug(f"OpenFace output: {result.stdout}")
                return True
            else:
                logger.error(f"OpenFace processing failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error running OpenFace container: {e}")
            return False
    
    def _parse_results(self) -> Dict[str, Any]:
        """Parse dos resultados do CSV gerado pelo OpenFace"""
        try:
            # Ler CSV
            df = pd.read_csv(self.output_path)
            
            if df.empty:
                logger.warning("OpenFace output CSV is empty")
                return None
            
            # Pegar primeira linha (primeira face detectada)
            row = df.iloc[0]
            
            # Extrair informações básicas
            result = {
                "success": bool(row.get("success", False)),
                "confidence": float(row.get("confidence", 0.0)),
                "timestamp": row.get("timestamp", ""),
                "face_detected": True,
                "action_units": {}
            }
            
            # Extrair Unidades de Ação (AUs)
            au_names = [
                "AU01", "AU02", "AU04", "AU05", "AU06", "AU07", "AU09", "AU10",
                "AU12", "AU14", "AU15", "AU17", "AU20", "AU23", "AU25", "AU26", "AU45"
            ]
            
            for au in au_names:
                # Intensidade (regression)
                intensity_col = f"{au}_r"
                # Presença (classification)
                presence_col = f"{au}_c"
                
                if intensity_col in row and presence_col in row:
                    result["action_units"][au] = {
                        "intensity": float(row[intensity_col]),
                        "present": bool(row[presence_col])
                    }
            
            logger.info(f"Successfully parsed {len(result['action_units'])} Action Units")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing OpenFace results: {e}")
            return None
    
    def get_emotional_interpretation(self, au_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Interpreta as AUs para emoções básicas
        
        Esta é uma interpretação simplificada baseada em combinações típicas de AUs
        """
        if not au_data or not au_data.get("action_units"):
            return {}
        
        aus = au_data["action_units"]
        emotions = {}
        
        # Alegria - AU06 + AU12
        joy_score = 0
        if "AU06" in aus and aus["AU06"]["present"]:  # Cheek Raiser
            joy_score += aus["AU06"]["intensity"] * 0.5
        if "AU12" in aus and aus["AU12"]["present"]:  # Lip Corner Puller
            joy_score += aus["AU12"]["intensity"] * 0.7
        emotions["joy"] = min(joy_score, 1.0)
        
        # Tristeza - AU01 + AU04 + AU15
        sadness_score = 0
        if "AU01" in aus and aus["AU01"]["present"]:  # Inner Brow Raiser
            sadness_score += aus["AU01"]["intensity"] * 0.4
        if "AU04" in aus and aus["AU04"]["present"]:  # Brow Lowerer
            sadness_score += aus["AU04"]["intensity"] * 0.3
        if "AU15" in aus and aus["AU15"]["present"]:  # Lip Corner Depressor
            sadness_score += aus["AU15"]["intensity"] * 0.6
        emotions["sadness"] = min(sadness_score, 1.0)
        
        # Raiva - AU04 + AU05 + AU07 + AU23
        anger_score = 0
        if "AU04" in aus and aus["AU04"]["present"]:  # Brow Lowerer
            anger_score += aus["AU04"]["intensity"] * 0.5
        if "AU05" in aus and aus["AU05"]["present"]:  # Upper Lid Raiser
            anger_score += aus["AU05"]["intensity"] * 0.3
        if "AU07" in aus and aus["AU07"]["present"]:  # Lid Tightener
            anger_score += aus["AU07"]["intensity"] * 0.4
        if "AU23" in aus and aus["AU23"]["present"]:  # Lip Tightener
            anger_score += aus["AU23"]["intensity"] * 0.3
        emotions["anger"] = min(anger_score, 1.0)
        
        # Surpresa - AU01 + AU02 + AU05 + AU26
        surprise_score = 0
        if "AU01" in aus and aus["AU01"]["present"]:  # Inner Brow Raiser
            surprise_score += aus["AU01"]["intensity"] * 0.3
        if "AU02" in aus and aus["AU02"]["present"]:  # Outer Brow Raiser
            surprise_score += aus["AU02"]["intensity"] * 0.4
        if "AU05" in aus and aus["AU05"]["present"]:  # Upper Lid Raiser
            surprise_score += aus["AU05"]["intensity"] * 0.4
        if "AU26" in aus and aus["AU26"]["present"]:  # Jaw Drop
            surprise_score += aus["AU26"]["intensity"] * 0.5
        emotions["surprise"] = min(surprise_score, 1.0)
        
        # Medo - AU01 + AU02 + AU04 + AU05 + AU07 + AU20 + AU26
        fear_score = 0
        if "AU01" in aus and aus["AU01"]["present"]:
            fear_score += aus["AU01"]["intensity"] * 0.3
        if "AU02" in aus and aus["AU02"]["present"]:
            fear_score += aus["AU02"]["intensity"] * 0.3
        if "AU04" in aus and aus["AU04"]["present"]:
            fear_score += aus["AU04"]["intensity"] * 0.2
        if "AU05" in aus and aus["AU05"]["present"]:
            fear_score += aus["AU05"]["intensity"] * 0.3
        if "AU20" in aus and aus["AU20"]["present"]:  # Lip Stretcher
            fear_score += aus["AU20"]["intensity"] * 0.3
        emotions["fear"] = min(fear_score, 1.0)
        
        # Nojo - AU09 + AU15 + AU16
        disgust_score = 0
        if "AU09" in aus and aus["AU09"]["present"]:  # Nose Wrinkler
            disgust_score += aus["AU09"]["intensity"] * 0.6
        if "AU15" in aus and aus["AU15"]["present"]:
            disgust_score += aus["AU15"]["intensity"] * 0.4
        emotions["disgust"] = min(disgust_score, 1.0)
        
        return emotions


# Instância global para uso no backend
openface_processor = OpenFaceProcessor() 