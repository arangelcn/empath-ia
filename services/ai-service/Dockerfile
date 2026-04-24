FROM python:3.11-slim

WORKDIR /app

ARG ENABLE_LOCAL_LLM=false
ARG LOCAL_MODEL_REPO_ID=google/gemma-3-4b-it-qat-q4_0-gguf
ARG LOCAL_MODEL_INCLUDE=*.gguf
ARG LOCAL_MODEL_DIR=/models/local-llm
ARG LLAMA_CPP_PIP_EXTRA_ARGS=
ARG HF_TOKEN=

ENV LOCAL_MODEL_DIR=${LOCAL_MODEL_DIR}

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Dependências opcionais para servir um modelo GGUF local dentro do AI Service.
# Mantido atrás de ENABLE_LOCAL_LLM para não quebrar builds sem token/licença do modelo.
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
            -r requirements-local-llm.txt \
        && LOCAL_MODEL_REPO_ID="${LOCAL_MODEL_REPO_ID}" \
           LOCAL_MODEL_INCLUDE="${LOCAL_MODEL_INCLUDE}" \
           LOCAL_MODEL_DIR="${LOCAL_MODEL_DIR}" \
           HF_TOKEN="${HF_TOKEN}" \
           python scripts/download_local_model.py; \
    fi

# Copiar código
COPY src/ ./src/

# Expor porta
EXPOSE 8001

# Comando para iniciar a aplicação
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"] 
