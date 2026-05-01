# Usar imagem TensorFlow compatível com driver NVIDIA 535.x (CUDA 12.2)
FROM tensorflow/tensorflow:2.13.0-gpu

WORKDIR /app

# Atualizar sistema e instalar dependências essenciais
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
    # Dependências para compilação
    gcc \
    g++ \
    build-essential \
    pkg-config \
    # Dependências extras para processamento de imagem
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libglib2.0-0 \
    # Limpeza
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Atualizar pip (a imagem TensorFlow já tem Python configurado)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copiar requirements primeiro (para cache do Docker)
COPY requirements.txt .

# Não usar --ignore-installed aqui: a imagem base já traz TensorFlow 2.13.0.
# Ignorar pacotes instalados permite que dependências transitivas reinstalem
# TensorFlow/Keras incompatíveis com Python 3.8 e quebrem o import do DeepFace.
RUN sed -i '/^tensorflow/d' requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Criar diretórios necessários
RUN mkdir -p /app/models /app/data /shared_data

# Copiar código
COPY src/ ./src/

# Expor porta
EXPOSE 8003

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
# Configurações TensorFlow GPU otimizadas
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV TF_FORCE_GPU_ALLOW_GROWTH=true
ENV TF_XLA_FLAGS=--tf_xla_enable_xla_devices
# Configurações CUDA para melhor performance
ENV CUDA_CACHE_DISABLE=0
ENV CUDA_CACHE_MAXSIZE=2147483648

# Comando para iniciar a aplicação
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"] 
