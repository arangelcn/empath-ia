FROM python:3.11-slim as builder

# Instalar dependências do sistema apenas para build
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    git \
    libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Estágio final - runtime
FROM python:3.11-slim

WORKDIR /app

# Instalar apenas dependências runtime necessárias
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    espeak \
    espeak-data \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar dependências instaladas do builder
COPY --from=builder /root/.local /root/.local

# Copiar código
COPY src/ ./src/

# Criar diretório para arquivos de áudio
RUN mkdir -p /app/output

# Criar diretório para cache do Bark
RUN mkdir -p /root/.cache/bark

# Adicionar diretório local ao PATH
ENV PATH=/root/.local/bin:$PATH

# Variáveis de ambiente para Bark
ENV BARK_USE_GPU=false
ENV BARK_DEFAULT_VOICE=v2/pt_speaker_1
ENV SUNO_OFFLOAD_CPU=True
ENV SUNO_USE_SMALL_MODELS=False

# Expor porta
EXPOSE 8004

# Comando para iniciar a aplicação
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004"] 