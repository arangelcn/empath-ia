FROM ubuntu:20.04

# Evitar prompts interativos durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    wget \
    unzip \
    # OpenCV dependencies
    libopencv-dev \
    libopencv-contrib-dev \
    # dlib dependencies  
    libboost-all-dev \
    libopenblas-dev \
    liblapack-dev \
    # TBB (Threading Building Blocks)
    libtbb-dev \
    # Additional dependencies
    libgtk-3-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    gfortran \
    openexr \
    libatlas-base-dev \
    python3-dev \
    python3-numpy \
    libtbb2 \
    libtbb-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libdc1394-22-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /opt

# Clonar o repositório OpenFace
RUN git clone https://github.com/TadasBaltrusaitis/OpenFace.git

# Navegar para o diretório OpenFace
WORKDIR /opt/OpenFace

# Criar diretório de build
RUN mkdir build

# Navegar para o diretório de build
WORKDIR /opt/OpenFace/build

# Configurar com CMake
RUN cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D BUILD_SHARED_LIBS=OFF \
    ..

# Compilar (usando múltiplos cores para acelerar)
RUN make -j$(nproc)

# Criar diretório para dados compartilhados
RUN mkdir -p /data

# Definir diretório de trabalho para execução
WORKDIR /opt/OpenFace/build/bin

# Script de entrada para executar o FeatureExtraction
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Comando padrão
ENTRYPOINT ["/entrypoint.sh"] 