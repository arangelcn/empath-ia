FROM python:3.11-slim as builder

# Instalar dependências do sistema para build
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    git \
    libsndfile1-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Estágio final - runtime
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências runtime necessárias para F5-TTS
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar dependências instaladas do builder
COPY --from=builder /root/.local /root/.local

# Copiar script de instalação do F5-TTS
COPY install_f5tts.sh .
RUN chmod +x install_f5tts.sh

# Executar instalação do F5-TTS
RUN ./install_f5tts.sh

# Copiar código
COPY src/ ./src/

# Criar diretórios necessários
RUN mkdir -p /app/output \
    && mkdir -p /app/models \
    && mkdir -p /tmp/f5_tts_cache \
    && mkdir -p /tmp/huggingface_cache

# Adicionar diretório local ao PATH
ENV PATH=/root/.local/bin:$PATH

# Variáveis de ambiente para F5-TTS
ENV PYTHONPATH=/app
ENV F5_TTS_MODEL=firstpixel/F5-TTS-pt-br
ENV F5_TTS_DEVICE=cpu
ENV F5_TTS_OUTPUT_DIR=/app/output

# Configurações de cache e performance
ENV TORCH_HOME=/tmp/torch_cache
ENV HF_HOME=/tmp/huggingface_cache
ENV TRANSFORMERS_CACHE=/tmp/transformers_cache
ENV HF_HUB_CACHE=/tmp/huggingface_cache

# Configurações específicas do serviço
ENV VOICE_SERVICE_HOST=0.0.0.0
ENV VOICE_SERVICE_PORT=8004

# Pré-baixar modelo F5-TTS (opcional - descomente se quiser incluir no build)
# RUN python -c "
# try:
#     from transformers import AutoModel, AutoTokenizer
#     model_name = 'firstpixel/F5-TTS-pt-br'
#     print(f'Baixando modelo {model_name}...')
#     tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
#     model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
#     print('Modelo baixado com sucesso!')
# except Exception as e:
#     print(f'Aviso: Não foi possível pré-baixar o modelo: {e}')
# "

# Expor porta
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# Comando para iniciar a aplicação
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004", "--workers", "1"] 