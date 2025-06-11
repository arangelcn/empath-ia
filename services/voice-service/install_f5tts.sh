#!/bin/bash

# Script de instalação do F5-TTS
echo "🔧 Instalando F5-TTS..."

# Atualizar pip
pip install --upgrade pip

# Instalar dependências básicas primeiro
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Tentar instalar F5-TTS via git (se disponível)
if git --version > /dev/null 2>&1; then
    echo "📦 Tentando instalar F5-TTS via git..."
    
    # Clonar repositório F5-TTS (exemplo - ajustar URL conforme necessário)
    if [ ! -d "/tmp/F5-TTS" ]; then
        git clone https://github.com/SWivid/F5-TTS.git /tmp/F5-TTS || echo "⚠️ Falha ao clonar F5-TTS"
    fi
    
    # Instalar se o clone foi bem-sucedido
    if [ -d "/tmp/F5-TTS" ]; then
        cd /tmp/F5-TTS
        pip install -e . || echo "⚠️ Falha na instalação do F5-TTS"
        cd -
    fi
else
    echo "⚠️ Git não disponível, pulando instalação do F5-TTS"
fi

# Instalar dependências alternativas se F5-TTS não estiver disponível
echo "📦 Instalando dependências alternativas..."
pip install \
    transformers \
    tokenizers \
    accelerate \
    librosa \
    soundfile \
    numpy

# Verificar instalação
python -c "
try:
    import torch
    import torchaudio
    import transformers
    print('✅ Dependências básicas instaladas com sucesso!')
except ImportError as e:
    print(f'❌ Erro na instalação: {e}')
    exit(1)

try:
    import f5_tts
    print('✅ F5-TTS instalado com sucesso!')
except ImportError:
    print('⚠️ F5-TTS não disponível - usando fallback')
"

echo "🎉 Instalação concluída!" 