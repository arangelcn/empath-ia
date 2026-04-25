# syntax=docker/dockerfile:1.7
ARG AI_SERVICE_BASE_IMAGE=nvidia/cuda:12.4.1-devel-ubuntu22.04
FROM ${AI_SERVICE_BASE_IMAGE}

WORKDIR /app

ARG ENABLE_LOCAL_LLM=false
ARG LOCAL_MODEL_DIR=/models/local-llm
ARG LLAMA_CPP_CUDA=false
ARG LLAMA_CPP_VERSION=0.3.7
ARG LLAMA_CPP_CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=86 -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_SERVER=OFF"
ARG CMAKE_BUILD_PARALLEL_LEVEL=2
ARG LLAMA_CPP_PIP_EXTRA_ARGS=

ENV DEBIAN_FRONTEND=noninteractive \
    LOCAL_MODEL_DIR=${LOCAL_MODEL_DIR} \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

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
    && ln -sf /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Dependências opcionais para servir um modelo GGUF local dentro do AI Service.
# O download do GGUF acontece no startup/runtime para manter a imagem menor e cacheável.
COPY requirements-local-llm.txt .
COPY scripts/ ./scripts/
RUN if [ "$ENABLE_LOCAL_LLM" = "true" ]; then \
        if [ "$LLAMA_CPP_CUDA" = "true" ]; then \
            pip install "huggingface_hub[cli]>=0.26.0" \
            && CMAKE_ARGS="$LLAMA_CPP_CMAKE_ARGS" FORCE_CMAKE=1 CMAKE_BUILD_PARALLEL_LEVEL="$CMAKE_BUILD_PARALLEL_LEVEL" \
                pip install --force-reinstall --no-binary llama-cpp-python \
                ${LLAMA_CPP_PIP_EXTRA_ARGS} \
                "llama-cpp-python==$LLAMA_CPP_VERSION"; \
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
