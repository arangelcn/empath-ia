# Imagem base Python 3.11 slim
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema para áudio
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fonte
COPY src/ ./src/

# Criar diretórios necessários
RUN mkdir -p /app/output \
    && mkdir -p /app/logs \
    && mkdir -p /app/credentials

# Configurar credenciais do Google Cloud
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/empathia-462921-734245aa641d.json

# Expor porta
EXPOSE 8004

# Comando padrão
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004"] 