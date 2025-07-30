FROM python:3.10-slim

WORKDIR /app

# Instalar dependências essenciais para MediaPipe, OpenCV e processamento básico
RUN apt-get update && apt-get install -y \
    # Ferramentas básicas
    git \
    wget \
    curl \
    # Dependências do sistema para OpenCV e MediaPipe
    libglib2.0-0 \
    libgl1-mesa-glx \
    libxrender1 \
    libxext6 \
    libsm6 \
    libfontconfig1 \
    # Dependências básicas do OpenCV
    libgtk-3-0 \
    libjpeg-dev \
    libpng-dev \
    # Dependências para compilação (mínimas)
    gcc \
    g++ \
    build-essential \
    # Limpeza
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Atualizar pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copiar requirements primeiro (para cache do Docker)
COPY requirements.txt .

# Instalar dependências Python (otimizado e rápido)
RUN pip install --no-cache-dir -r requirements.txt

# Criar diretórios necessários
RUN mkdir -p /app/models /app/data /shared_data

# Copiar código
COPY src/ ./src/

# Expor porta
EXPOSE 8003

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Comando para iniciar a aplicação
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"] 