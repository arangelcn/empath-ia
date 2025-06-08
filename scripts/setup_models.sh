#!/bin/bash

# Script de setup para download de modelos EmpathIA
set -e

echo "🚀 Setup de Modelos EmpathIA"
echo "=============================="

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Execute este script no diretório raiz do projeto (onde está o docker-compose.yml)"
    exit 1
fi

# Criar ambiente virtual se não existir
VENV_DIR="venv-models"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv $VENV_DIR
fi

# Ativar ambiente virtual
echo "🔌 Ativando ambiente virtual..."
source $VENV_DIR/bin/activate

# Atualizar pip
echo "⬆️ Atualizando pip..."
pip install --upgrade pip

# Instalar dependências
echo "📥 Instalando dependências..."
pip install -r scripts/requirements-download.txt

# Executar download
echo "⬇️ Iniciando download dos modelos..."
python scripts/download_models.py

# Verificar se download foi bem-sucedido
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Download concluído com sucesso!"
    echo ""
    echo "📁 Estrutura criada:"
    echo "   data/models/tts/      - Modelos TTS"
    echo "   data/models/llm/      - Modelos LLM"
    echo "   data/models/embeddings/ - Modelos de embeddings"
    echo "   data/models/cache/    - Cache geral"
    echo ""
    echo "📄 Arquivos de configuração:"
    echo "   data/docker-models.env       - Variáveis de ambiente"
    echo "   data/docker-compose.models.yml - Configuração Docker"
    echo ""
    echo "🐳 Próximos passos:"
    echo "   1. Configure o docker-compose.yml com os volumes dos modelos"
    echo "   2. Reconstrua os containers: docker compose up --build"
    echo "   3. Os modelos serão carregados do cache local"
    echo ""
else
    echo "❌ Erro no download. Verifique os logs acima."
    exit 1
fi

# Desativar ambiente virtual
deactivate

echo "🎉 Setup concluído!" 