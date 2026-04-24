# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

WORKDIR /app

ARG ENABLE_LOCAL_LLM=false
ARG LOCAL_MODEL_DIR=/models/local-llm
ARG LLAMA_CPP_PIP_EXTRA_ARGS=

ENV LOCAL_MODEL_DIR=${LOCAL_MODEL_DIR}

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Dependências opcionais para servir um modelo GGUF local dentro do AI Service.
# O download do GGUF acontece no startup/runtime para manter a imagem menor e cacheável.
COPY requirements-local-llm.txt .
COPY scripts/ ./scripts/
RUN if [ "$ENABLE_LOCAL_LLM" = "true" ]; then \
        apt-get update && apt-get install -y --no-install-recommends \
            build-essential \
            cmake \
            git \
        && rm -rf /var/lib/apt/lists/* \
        && pip install --no-cache-dir \
            ${LLAMA_CPP_PIP_EXTRA_ARGS} \
            -r requirements-local-llm.txt; \
    fi

# Copiar código
COPY src/ ./src/

# Expor porta
EXPOSE 8001

# Comando para iniciar a aplicação
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"] 
