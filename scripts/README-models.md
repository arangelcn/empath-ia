# 🤖 Sistema de Modelos Locais - EmpathIA

Este sistema permite baixar e usar modelos de IA localmente, evitando downloads repetidos e melhorando a performance.

## 🚀 Quick Start

### 1. Executar Setup Automático

```bash
# Torna o script executável
chmod +x scripts/setup_models.sh

# Executa o download completo
bash scripts/setup_models.sh
```

### 2. Configurar Docker

```bash
# Copiar exemplo de configuração
cp docker-compose.models.example.yml docker-compose.override.yml

# Reconstruir containers com modelos locais
docker compose up --build
```

## 📁 Estrutura dos Modelos

```
data/models/
├── tts/                    # Modelos TTS (Text-to-Speech)
│   ├── xtts_v2/           # XTTS-v2 (melhor para PT-BR)
│   ├── vits_pt/           # VITS português
│   ├── your_tts/          # YourTTS multilíngue
│   └── tacotron2_pt/      # Tacotron2 português
├── llm/                    # Modelos LLM (Large Language Models)
│   ├── gpt2_portuguese/   # GPT-2 em português
│   ├── distilgpt2/        # DistilGPT-2 compacto
│   ├── bert_portuguese/   # BERT português
│   └── distilbert_multilingual/
├── embeddings/             # Modelos de embeddings
│   ├── all_minilm_l6_v2/  # Embeddings gerais
│   ├── multilingual_e5/   # E5 multilíngue
│   └── portuguese_embeddings/
└── cache/                  # Cache do Hugging Face
```

## 🎤 Modelos TTS Incluídos

### XTTS-v2 (Recomendado)
- **Qualidade**: Excelente para português brasileiro
- **Funcionalidades**: Clonagem de voz, múltiplas línguas
- **Tamanho**: ~1.9GB
- **Uso**: Produção

### VITS Português
- **Qualidade**: Boa para português europeu
- **Funcionalidades**: Síntese básica
- **Tamanho**: ~100MB
- **Uso**: Desenvolvimento/testes

### YourTTS
- **Qualidade**: Boa para múltiplas línguas
- **Funcionalidades**: Clonagem de voz multilíngue
- **Tamanho**: ~500MB
- **Uso**: Aplicações multilíngues

## 🤖 Modelos LLM Incluídos

### GPT-2 Português
- **Modelo**: pierreguillou/gpt2-small-portuguese
- **Uso**: Geração de texto em português
- **Tamanho**: ~500MB

### BERT Português
- **Modelo**: neuralmind/bert-base-portuguese-cased
- **Uso**: Compreensão e análise de texto
- **Tamanho**: ~400MB

### DistilGPT-2
- **Modelo**: distilgpt2
- **Uso**: Geração de texto compacta
- **Tamanho**: ~350MB

## 🔤 Modelos de Embeddings

### all-MiniLM-L6-v2
- **Uso**: Embeddings gerais, busca semântica
- **Tamanho**: ~90MB
- **Performance**: Excelente custo-benefício

### Multilingual E5
- **Uso**: Embeddings multilíngues
- **Tamanho**: ~400MB
- **Performance**: Estado da arte

## ⚙️ Configuração Manual

### Variáveis de Ambiente

```bash
# Caminhos dos modelos
export TTS_MODELS_PATH=/path/to/data/models/tts
export LLM_MODELS_PATH=/path/to/data/models/llm
export EMBEDDINGS_MODELS_PATH=/path/to/data/models/embeddings

# Cache
export HF_HOME=/path/to/data/models/cache
export TTS_HOME=/path/to/data/models/tts

# Configurações TTS
export COQUI_TOS_AGREED=1
export TTS_MODEL=xtts_v2
export TTS_USE_GPU=false
```

### Docker Compose Override

```yaml
services:
  voice-service:
    volumes:
      - ./data/models/tts:/app/models/tts:ro
      - ./data/models/cache:/root/.cache:rw
    environment:
      - TTS_MODELS_PATH=/app/models/tts
      - TTS_HOME=/app/models/tts
      - COQUI_TOS_AGREED=1
```

## 🔧 Troubleshooting

### Problema: Modelos não são encontrados

```bash
# Verificar se os diretórios existem
ls -la data/models/

# Verificar permissões
chmod -R 755 data/models/

# Reexecutar download
python scripts/download_models.py
```

### Problema: Erro de memória

```bash
# Usar apenas modelos menores
export TTS_MODEL=vits_pt

# Ou aumentar swap do sistema
sudo swapon --show
```

### Problema: Download lento

```bash
# Usar mirror brasileiro do Hugging Face
export HF_ENDPOINT=https://huggingface.co

# Ou baixar modelos específicos
python scripts/download_models.py --model-type tts
```

## 🚀 Performance

### Com Modelos Locais
- ✅ Inicialização instantânea
- ✅ Sem dependência de internet
- ✅ Performance consistente
- ✅ Privacidade total

### Sem Modelos Locais
- ❌ Download a cada rebuild (~2GB)
- ❌ Dependência de internet
- ❌ Latência variável
- ❌ Possível rate limiting

## 📊 Uso de Disco

```bash
# Verificar espaço usado
du -sh data/models/

# Típico:
# TTS: ~2.5GB
# LLM: ~2.0GB  
# Embeddings: ~1.0GB
# Total: ~5.5GB
```

## 🔄 Atualização de Modelos

```bash
# Atualizar todos os modelos
rm -rf data/models/
bash scripts/setup_models.sh

# Atualizar apenas TTS
rm -rf data/models/tts/
python scripts/download_models.py --tts-only
```

## 🐳 Docker Tips

```bash
# Verificar volumes montados
docker compose config

# Verificar se modelos estão acessíveis no container
docker compose exec voice-service ls -la /app/models/

# Logs para debug
docker compose logs voice-service | grep -i "modelo\|model"
```

## 🎯 Próximos Passos

1. **Implementar cache inteligente**: Verificar idade dos modelos
2. **Compressão**: Usar modelos quantizados para economizar espaço
3. **Auto-update**: Script para atualizar modelos automaticamente
4. **Health check**: Verificar integridade dos modelos
5. **Metrics**: Monitorar uso e performance dos modelos 