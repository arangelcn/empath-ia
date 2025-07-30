#!/usr/bin/env python3
"""
Script para exportar modelos EmotiEffLib quantizados em ONNX FP16 e INT8
Usado para otimização de performance em produção
"""

import os
import sys
import logging
import argparse
from pathlib import Path
import torch
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType
from onnxruntime.quantization.quantize import quantize_static
from onnxruntime.quantization.calibrate import CalibrationDataReader
import numpy as np

try:
    from emotiefflib import EmotionPredictor
    EMOTIEFFLIB_AVAILABLE = True
except ImportError:
    EMOTIEFFLIB_AVAILABLE = False
    print("ERRO: EmotiEffLib não está disponível. Instale com: pip install emotiefflib>=0.4.2")
    sys.exit(1)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalibrationDataset(CalibrationDataReader):
    """Dataset para calibração de quantização INT8"""
    
    def __init__(self, data_dir: str = None, num_samples: int = 100):
        """
        Args:
            data_dir: Diretório com imagens para calibração
            num_samples: Número de amostras para calibração
        """
        self.data_dir = data_dir
        self.num_samples = num_samples
        self.sample_data = self._generate_calibration_data()
        self.iterator = iter(self.sample_data)
    
    def _generate_calibration_data(self):
        """Gera dados sintéticos de calibração se não houver dataset real"""
        logger.info(f"Gerando {self.num_samples} amostras sintéticas para calibração")
        
        # Gerar dados sintéticos 224x224x3 (formato esperado pelo EfficientFormer)
        samples = []
        for i in range(self.num_samples):
            # Dados aleatórios normalizados [0, 1]
            sample = np.random.rand(1, 3, 224, 224).astype(np.float32)
            samples.append({"input": sample})
        
        return samples
    
    def get_next(self):
        """Retorna próxima amostra para calibração"""
        try:
            return next(self.iterator)
        except StopIteration:
            return None

def export_to_onnx(model_name: str = "efficientformer_lite_s0", output_dir: str = "models") -> str:
    """
    Exporta modelo EmotiEff para ONNX FP32
    
    Args:
        model_name: Nome do modelo EmotiEff
        output_dir: Diretório de saída
        
    Returns:
        Caminho do modelo ONNX exportado
    """
    logger.info(f"Exportando modelo {model_name} para ONNX...")
    
    try:
        # Inicializar modelo
        predictor = EmotionPredictor(model_name=model_name, device="cpu")
        
        # Dados de exemplo para tracing
        dummy_input = torch.randn(1, 3, 224, 224)
        
        # Caminho de saída
        output_path = os.path.join(output_dir, f"{model_name}_fp32.onnx")
        
        # Exportar para ONNX
        torch.onnx.export(
            predictor.model,
            dummy_input,
            output_path,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'}
            }
        )
        
        logger.info(f"Modelo ONNX FP32 exportado: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Erro ao exportar para ONNX: {e}")
        raise

def quantize_to_fp16(onnx_path: str, output_dir: str) -> str:
    """
    Quantiza modelo ONNX para FP16
    
    Args:
        onnx_path: Caminho do modelo ONNX FP32
        output_dir: Diretório de saída
        
    Returns:
        Caminho do modelo quantizado FP16
    """
    logger.info("Quantizando modelo para FP16...")
    
    try:
        # Carregar modelo
        model = onnx.load(onnx_path)
        
        # Converter para FP16
        from onnxconverter_common import float16
        model_fp16 = float16.convert_float_to_float16(model)
        
        # Salvar modelo FP16
        base_name = os.path.splitext(os.path.basename(onnx_path))[0]
        fp16_path = os.path.join(output_dir, f"{base_name.replace('_fp32', '')}_fp16.onnx")
        
        onnx.save(model_fp16, fp16_path)
        
        logger.info(f"Modelo FP16 salvo: {fp16_path}")
        return fp16_path
        
    except Exception as e:
        logger.error(f"Erro na quantização FP16: {e}")
        raise

def quantize_to_int8(onnx_path: str, output_dir: str, calibration_data_dir: str = None) -> str:
    """
    Quantiza modelo ONNX para INT8
    
    Args:
        onnx_path: Caminho do modelo ONNX FP32
        output_dir: Diretório de saída
        calibration_data_dir: Diretório com dados de calibração
        
    Returns:
        Caminho do modelo quantizado INT8
    """
    logger.info("Quantizando modelo para INT8...")
    
    try:
        # Caminho de saída
        base_name = os.path.splitext(os.path.basename(onnx_path))[0]
        int8_path = os.path.join(output_dir, f"{base_name.replace('_fp32', '')}_int8.onnx")
        
        # Quantização dinâmica (mais simples, não requer calibração)
        quantize_dynamic(
            onnx_path,
            int8_path,
            weight_type=QuantType.QInt8
        )
        
        logger.info(f"Modelo INT8 salvo: {int8_path}")
        return int8_path
        
    except Exception as e:
        logger.error(f"Erro na quantização INT8: {e}")
        raise

def validate_quantized_model(original_path: str, quantized_path: str) -> bool:
    """
    Valida modelo quantizado comparando com original
    
    Args:
        original_path: Caminho do modelo original
        quantized_path: Caminho do modelo quantizado
        
    Returns:
        True se validação passou
    """
    logger.info("Validando modelo quantizado...")
    
    try:
        import onnxruntime as ort
        
        # Criar sessões
        sess_original = ort.InferenceSession(original_path)
        sess_quantized = ort.InferenceSession(quantized_path)
        
        # Dados de teste
        test_input = np.random.rand(1, 3, 224, 224).astype(np.float32)
        
        # Executar inferências
        output_original = sess_original.run(None, {"input": test_input})[0]
        output_quantized = sess_quantized.run(None, {"input": test_input})[0]
        
        # Calcular diferença
        mse = np.mean((output_original - output_quantized) ** 2)
        max_diff = np.max(np.abs(output_original - output_quantized))
        
        logger.info(f"MSE entre modelos: {mse:.6f}")
        logger.info(f"Diferença máxima: {max_diff:.6f}")
        
        # Critério de validação (ajustável)
        if mse < 0.01 and max_diff < 0.1:
            logger.info("✅ Validação passou!")
            return True
        else:
            logger.warning("⚠️ Validação falhou - diferenças muito grandes")
            return False
            
    except Exception as e:
        logger.error(f"Erro na validação: {e}")
        return False

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Exportar modelos EmotiEff quantizados")
    parser.add_argument(
        "--model-name", 
        default="efficientformer_lite_s0",
        help="Nome do modelo EmotiEff (default: efficientformer_lite_s0)"
    )
    parser.add_argument(
        "--output-dir",
        default="models",
        help="Diretório de saída (default: models)"
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=["fp16", "int8", "all"],
        default=["all"],
        help="Formatos para exportar (default: all)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validar modelos quantizados"
    )
    parser.add_argument(
        "--calibration-dir",
        help="Diretório com dados de calibração para INT8"
    )
    
    args = parser.parse_args()
    
    # Verificar se EmotiEffLib está disponível
    if not EMOTIEFFLIB_AVAILABLE:
        return 1
    
    # Criar diretório de saída
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # 1. Exportar modelo base para ONNX FP32
        logger.info("🚀 Iniciando exportação de modelos quantizados...")
        onnx_fp32_path = export_to_onnx(args.model_name, args.output_dir)
        
        formats_to_export = args.formats
        if "all" in formats_to_export:
            formats_to_export = ["fp16", "int8"]
        
        exported_models = [onnx_fp32_path]
        
        # 2. Quantização FP16
        if "fp16" in formats_to_export:
            try:
                fp16_path = quantize_to_fp16(onnx_fp32_path, args.output_dir)
                exported_models.append(fp16_path)
            except Exception as e:
                logger.error(f"Falha na quantização FP16: {e}")
        
        # 3. Quantização INT8
        if "int8" in formats_to_export:
            try:
                int8_path = quantize_to_int8(onnx_fp32_path, args.output_dir, args.calibration_dir)
                exported_models.append(int8_path)
            except Exception as e:
                logger.error(f"Falha na quantização INT8: {e}")
        
        # 4. Validação (opcional)
        if args.validate:
            for model_path in exported_models[1:]:  # Pular o original
                validate_quantized_model(onnx_fp32_path, model_path)
        
        # 5. Resumo
        logger.info("✅ Exportação concluída!")
        logger.info("📁 Modelos exportados:")
        for model_path in exported_models:
            size_mb = os.path.getsize(model_path) / (1024 * 1024)
            logger.info(f"  - {model_path} ({size_mb:.2f} MB)")
        
        # 6. Instruções de uso
        logger.info("\n💡 Para usar modelos quantizados:")
        logger.info("   export EMOTION_MODEL_PATH=/path/to/model.onnx")
        logger.info("   # ou configure no docker-compose.yml")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Erro durante exportação: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 