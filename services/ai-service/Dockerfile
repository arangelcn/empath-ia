# syntax=docker/dockerfile:1.7
ARG AI_SERVICE_BASE_IMAGE=nvidia/cuda:12.4.1-devel-ubuntu22.04
FROM ${AI_SERVICE_BASE_IMAGE}

WORKDIR /app

ARG ENABLE_LOCAL_LLM=false
ARG LOCAL_MODEL_DIR=/models/local-llm
ARG LLAMA_CPP_CUDA=false
ARG LLAMA_CPP_VERSION=0.3.21
# CUDA version tag for pre-built wheels: cu121, cu122, cu123, cu124, cu125
ARG LLAMA_CPP_CUDA_VERSION=cu124
# Desabilita exemplos, tests, server e o llava para reduzir drasticamente o tempo de compilação.
# LDFLAGS garante que o linker encontre libcuda.so.1 (stub) durante o build from source.
ARG LLAMA_CPP_CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=86 -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_SERVER=OFF -DLLAMA_BUILD_LLAVA=OFF -DCMAKE_EXE_LINKER_FLAGS=-L/usr/local/cuda/lib64/stubs -DCMAKE_SHARED_LINKER_FLAGS=-L/usr/local/cuda/lib64/stubs"
ARG CMAKE_BUILD_PARALLEL_LEVEL=4
ARG LLAMA_CPP_PIP_EXTRA_ARGS=

ENV DEBIAN_FRONTEND=noninteractive \
    LOCAL_MODEL_DIR=${LOCAL_MODEL_DIR} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala dependências do sistema em uma única camada
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    cmake \
    curl \
    git \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    && ln -sf /usr/bin/python3 /usr/local/bin/python \
    && ln -sf /usr/bin/pip3 /usr/local/bin/pip \
    # Cria o symlink para o stub do libcuda necessário para linking em build-time (source build)
    && ln -sf /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
# --mount=type=cache reutiliza downloads do pip entre rebuilds (não vai para a imagem final)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Dependências opcionais para servir um modelo GGUF local dentro do AI Service.
# O download do GGUF acontece no startup/runtime para manter a imagem menor e cacheável.
#
# Estratégia de instalação (CUDA):
#   1. Tenta wheel pré-compilado via https://abetlen.github.io/llama-cpp-python/whl/<cu_version>
#      → sem compilação, download de ~200 MB, segundos de instalação
#   2. Fallback: compila do source com CMAKE_ARGS (pode levar 5–10 min)
COPY requirements-local-llm.txt .
COPY scripts/ ./scripts/
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "$ENABLE_LOCAL_LLM" = "true" ]; then \
    pip install "huggingface_hub[cli]>=0.26.0"; \
    if [ "$LLAMA_CPP_CUDA" = "true" ]; then \
    echo ">>> Trying pre-built CUDA wheel (llama-cpp-python==$LLAMA_CPP_VERSION $LLAMA_CPP_CUDA_VERSION)..." \
    && pip install "llama-cpp-python==$LLAMA_CPP_VERSION" \
    --extra-index-url "https://abetlen.github.io/llama-cpp-python/whl/$LLAMA_CPP_CUDA_VERSION" \
    ${LLAMA_CPP_PIP_EXTRA_ARGS} \
    || ( \
    echo ">>> Pre-built wheel not found; falling back to source build (5-10 min)..." \
    && CMAKE_ARGS="$LLAMA_CPP_CMAKE_ARGS" \
    FORCE_CMAKE=1 \
    CMAKE_BUILD_PARALLEL_LEVEL="$CMAKE_BUILD_PARALLEL_LEVEL" \
    LDFLAGS="-L/usr/local/cuda/lib64/stubs" \
    LD_LIBRARY_PATH="/usr/local/cuda/lib64/stubs:${LD_LIBRARY_PATH}" \
    pip install --force-reinstall --no-binary llama-cpp-python \
    ${LLAMA_CPP_PIP_EXTRA_ARGS} \
    "llama-cpp-python==$LLAMA_CPP_VERSION" \
    ); \
    else \
    pip install \
    ${LLAMA_CPP_PIP_EXTRA_ARGS} \
    -r requirements-local-llm.txt; \
    fi; \
    fi

# Copiar código
COPY src/ ./src/

# Expor porta
EXPOSE 8001

# Comando para iniciar a aplicação
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
