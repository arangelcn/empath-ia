#!/usr/bin/env python3
"""
Script para download de modelos TTS e LLM para cache local
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict
import torch

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_directories(base_path: str = "data/models") -> Dict[str, Path]:
    """Cria diretórios para organizar os modelos"""
    base_dir = Path(base_path)
    
    directories = {
        'tts': base_dir / 'tts',
        'llm': base_dir / 'llm',
        'embeddings': base_dir / 'embeddings',
        'cache': base_dir / 'cache'
    }
    
    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Diretório {name} criado: {path}")
    
    return directories

def download_tts_models(tts_dir: Path) -> bool:
    """Download dos modelos TTS do Coqui"""
    try:
        from TTS.api import TTS
        
        # Aceitar licença automaticamente
        os.environ["COQUI_TOS_AGREED"] = "1"
        
        # Modelos TTS para português brasileiro
        tts_models = {
            "xtts_v2": "tts_models/multilingual/multi-dataset/xtts_v2",
            "vits_pt": "tts_models/pt/cv/vits", 
            "your_tts": "tts_models/multilingual/multi-dataset/your_tts",
            "tacotron2_pt": "tts_models/pt/cv/tacotron2-DDC"
        }
        
        logger.info("🎤 Iniciando download dos modelos TTS...")
        
        for model_name, model_path in tts_models.items():
            try:
                logger.info(f"⬇️ Baixando {model_name}: {model_path}")
                
                # Definir cache específico para cada modelo
                cache_path = tts_dir / model_name
                cache_path.mkdir(exist_ok=True)
                
                # Configurar variável de ambiente para cache
                old_cache = os.environ.get('TTS_HOME')
                os.environ['TTS_HOME'] = str(cache_path)
                
                # Baixar modelo
                tts = TTS(model_name=model_path, progress_bar=True, gpu=False)
                
                # Restaurar cache original
                if old_cache:
                    os.environ['TTS_HOME'] = old_cache
                else:
                    os.environ.pop('TTS_HOME', None)
                
                logger.info(f"✅ {model_name} baixado com sucesso!")
                
            except Exception as e:
                logger.error(f"❌ Erro ao baixar {model_name}: {e}")
                continue
        
        return True
        
    except ImportError:
        logger.error("❌ TTS não está instalado. Instale com: pip install TTS")
        return False
    except Exception as e:
        logger.error(f"❌ Erro geral no download TTS: {e}")
        return False

def download_llm_models(llm_dir: Path) -> bool:
    """Download dos modelos LLM gratuitos"""
    try:
        from huggingface_hub import snapshot_download
        from transformers import AutoTokenizer, AutoModel
        
        # Modelos LLM úteis e gratuitos
        llm_models = {
            # Modelos de conversação em português
            "gpt2_portuguese": {
                "repo": "pierreguillou/gpt2-small-portuguese",
                "description": "GPT-2 treinado em português"
            },
            
            # Modelo de texto pequeno e eficiente
            "distilgpt2": {
                "repo": "distilgpt2", 
                "description": "DistilGPT-2 - versão compacta do GPT-2"
            },
            
            # Modelo para compreensão de texto em português
            "bert_portuguese": {
                "repo": "neuralmind/bert-base-portuguese-cased",
                "description": "BERT para português brasileiro"
            },
            
            # Modelo multilíngue pequeno
            "distilbert_multilingual": {
                "repo": "distilbert-base-multilingual-cased",
                "description": "DistilBERT multilíngue"
            },
            
            # Modelo para embeddings de texto
            "sentence_transformer_pt": {
                "repo": "rufimelo/Legal-BERTimbau-sts-base-ma-v3",
                "description": "Sentence transformer para português"
            }
        }
        
        logger.info("🤖 Iniciando download dos modelos LLM...")
        
        for model_name, config in llm_models.items():
            try:
                model_path = llm_dir / model_name
                repo_id = config["repo"]
                
                logger.info(f"⬇️ Baixando {model_name}: {repo_id}")
                logger.info(f"   📝 {config['description']}")
                
                # Download do modelo completo
                snapshot_download(
                    repo_id=repo_id,
                    local_dir=str(model_path),
                    local_dir_use_symlinks=False
                )
                
                logger.info(f"✅ {model_name} baixado com sucesso!")
                
            except Exception as e:
                logger.error(f"❌ Erro ao baixar {model_name}: {e}")
                continue
        
        return True
        
    except ImportError:
        logger.error("❌ Transformers/huggingface_hub não estão instalados.")
        logger.error("   Instale com: pip install transformers huggingface_hub")
        return False
    except Exception as e:
        logger.error(f"❌ Erro geral no download LLM: {e}")
        return False

def download_embedding_models(embeddings_dir: Path) -> bool:
    """Download de modelos de embeddings"""
    try:
        from sentence_transformers import SentenceTransformer
        
        # Modelos de embeddings eficientes
        embedding_models = {
            "all_minilm_l6_v2": {
                "name": "sentence-transformers/all-MiniLM-L6-v2",
                "description": "Modelo de embeddings leve e eficiente"
            },
            "multilingual_e5": {
                "name": "intfloat/multilingual-e5-small", 
                "description": "Embeddings multilíngues E5"
            },
            "portuguese_embeddings": {
                "name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "description": "Embeddings multilíngues para paráfrase"
            }
        }
        
        logger.info("🔤 Iniciando download dos modelos de embeddings...")
        
        for model_key, config in embedding_models.items():
            try:
                model_path = embeddings_dir / model_key
                model_name = config["name"]
                
                logger.info(f"⬇️ Baixando {model_key}: {model_name}")
                logger.info(f"   📝 {config['description']}")
                
                # Download e cache do modelo
                model = SentenceTransformer(model_name, cache_folder=str(model_path))
                
                logger.info(f"✅ {model_key} baixado com sucesso!")
                
            except Exception as e:
                logger.error(f"❌ Erro ao baixar {model_key}: {e}")
                continue
        
        return True
        
    except ImportError:
        logger.error("❌ sentence-transformers não está instalado.")
        logger.error("   Instale com: pip install sentence-transformers")
        return False
    except Exception as e:
        logger.error(f"❌ Erro geral no download de embeddings: {e}")
        return False

def create_docker_config(base_path: str):
    """Cria configuração para Docker usar os modelos locais"""
    
    docker_env_content = f"""# Configuração de modelos locais para Docker
# Adicione estas variáveis ao seu .env ou docker-compose.yml

# Diretórios de modelos
TTS_MODELS_PATH={os.path.abspath(base_path)}/tts
LLM_MODELS_PATH={os.path.abspath(base_path)}/llm
EMBEDDINGS_MODELS_PATH={os.path.abspath(base_path)}/embeddings

# Cache do Hugging Face
HF_HOME={os.path.abspath(base_path)}/cache
TTS_HOME={os.path.abspath(base_path)}/tts

# Configuração do TTS
COQUI_TOS_AGREED=1
TTS_CACHE_PATH={os.path.abspath(base_path)}/tts
"""
    
    config_file = Path(base_path).parent / "docker-models.env"
    with open(config_file, 'w') as f:
        f.write(docker_env_content)
    
    logger.info(f"📄 Configuração Docker criada: {config_file}")
    
    # Criar também um docker-compose override sugerido
    docker_compose_override = f"""# docker-compose.override.yml sugerido
# Para usar os modelos locais

version: '3.8'

services:
  voice-service:
    volumes:
      - {os.path.abspath(base_path)}/tts:/app/models/tts:ro
      - {os.path.abspath(base_path)}/cache:/root/.cache:rw
    environment:
      - TTS_HOME=/app/models/tts
      - HF_HOME=/root/.cache
      - COQUI_TOS_AGREED=1
      - TTS_CACHE_PATH=/app/models/tts

  # Adicionar para futuros serviços de LLM
  # ai-service:
  #   volumes:
  #     - {os.path.abspath(base_path)}/llm:/app/models/llm:ro
  #     - {os.path.abspath(base_path)}/embeddings:/app/models/embeddings:ro
  #     - {os.path.abspath(base_path)}/cache:/root/.cache:rw
"""
    
    override_file = Path(base_path).parent / "docker-compose.models.yml"
    with open(override_file, 'w') as f:
        f.write(docker_compose_override)
    
    logger.info(f"📄 Docker Compose override criado: {override_file}")

def main():
    """Função principal"""
    logger.info("🚀 Iniciando download de modelos para EmpathIA")
    
    # Verificar dependências básicas
    try:
        import torch
        logger.info(f"✅ PyTorch {torch.__version__} detectado")
    except ImportError:
        logger.error("❌ PyTorch não encontrado. Instale com: pip install torch")
        return 1
    
    # Configurar diretórios
    base_path = "data/models"
    directories = setup_directories(base_path)
    
    # Status dos downloads
    downloads_status = {
        "tts": False,
        "llm": False, 
        "embeddings": False
    }
    
    # Download TTS models
    logger.info("\n" + "="*50)
    logger.info("🎤 MODELOS TTS (Text-to-Speech)")
    logger.info("="*50)
    downloads_status["tts"] = download_tts_models(directories['tts'])
    
    # Download LLM models
    logger.info("\n" + "="*50)
    logger.info("🤖 MODELOS LLM (Large Language Models)")
    logger.info("="*50)
    downloads_status["llm"] = download_llm_models(directories['llm'])
    
    # Download embedding models
    logger.info("\n" + "="*50)
    logger.info("🔤 MODELOS DE EMBEDDINGS")
    logger.info("="*50)
    downloads_status["embeddings"] = download_embedding_models(directories['embeddings'])
    
    # Criar configuração Docker
    logger.info("\n" + "="*50)
    logger.info("🐳 CONFIGURAÇÃO DOCKER")
    logger.info("="*50)
    create_docker_config(base_path)
    
    # Resumo final
    logger.info("\n" + "="*50)
    logger.info("📊 RESUMO DO DOWNLOAD")
    logger.info("="*50)
    
    for category, success in downloads_status.items():
        status = "✅ Sucesso" if success else "❌ Falhou"
        logger.info(f"{category.upper()}: {status}")
    
    if any(downloads_status.values()):
        logger.info("\n🎉 Download concluído!")
        logger.info("💡 Próximos passos:")
        logger.info("   1. Verifique os arquivos em data/models/")
        logger.info("   2. Use docker-compose.models.yml como referência")
        logger.info("   3. Configure as variáveis de ambiente")
        logger.info("   4. Reconstrua os containers com os volumes montados")
        return 0
    else:
        logger.error("❌ Nenhum download foi bem-sucedido")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 