FROM python:3.11-slim

WORKDIR /app

# Instalar dependências essenciais para MediaPipe, OpenCV e análise facial
RUN apt-get update && apt-get install -y \
    # Dependências básicas do sistema
    libglib2.0-0 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    # Dependências específicas do MediaPipe
    libxrender1 \
    libxext6 \
    libsm6 \
    libxrandr2 \
    libfontconfig1 \
    libice6 \
    libxt6 \
    libxss1 \
    libgconf-2-4 \
    # Dependências do OpenCV
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libatlas-base-dev \
    gfortran \
    # Ferramentas de build
    gcc \
    g++ \
    cmake \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para cache do Docker)
COPY requirements.txt .

# Instalar dependências Python (com cache otimizado)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY src/ ./src/

# Expor porta
EXPOSE 8003

# Comando para iniciar a aplicação
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"] 