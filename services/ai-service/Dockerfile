# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

WORKDIR /app

ARG ENABLE_LOCAL_LLM=false
ARG LOCAL_MODEL_REPO_ID=google/gemma-3-4b-it-qat-q4_0-gguf
ARG LOCAL_MODEL_INCLUDE=*.gguf
ARG LOCAL_MODEL_DIR=/models/local-llm
ARG LLAMA_CPP_PIP_EXTRA_ARGS=
ARG LOCAL_MODEL_DOWNLOAD_REQUIRED=true

ENV LOCAL_MODEL_DIR=${LOCAL_MODEL_DIR}

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Dependências opcionais para servir um modelo GGUF local dentro do AI Service.
# Mantido atrás de ENABLE_LOCAL_LLM para não quebrar builds sem token/licença do modelo.
COPY requirements-local-llm.txt .
COPY scripts/ ./scripts/
RUN --mount=type=secret,id=hf_token,required=false \
    --mount=type=secret,id=hugging_face_token,required=false \
    --mount=type=secret,id=huggin_face_token,required=false \
    if [ "$ENABLE_LOCAL_LLM" = "true" ]; then \
        HF_TOKEN_VALUE=""; \
        for HF_TOKEN_SECRET_FILE in /run/secrets/hf_token /run/secrets/hugging_face_token /run/secrets/huggin_face_token; do \
            if [ -z "$HF_TOKEN_VALUE" ] && [ -s "$HF_TOKEN_SECRET_FILE" ]; then \
                HF_TOKEN_VALUE="$(cat "$HF_TOKEN_SECRET_FILE")"; \
            fi; \
        done; \
        apt-get update && apt-get install -y --no-install-recommends \
            build-essential \
            cmake \
            git \
        && rm -rf /var/lib/apt/lists/* \
        && pip install --no-cache-dir \
            ${LLAMA_CPP_PIP_EXTRA_ARGS} \
            -r requirements-local-llm.txt \
        && (LOCAL_MODEL_REPO_ID="${LOCAL_MODEL_REPO_ID}" \
            LOCAL_MODEL_INCLUDE="${LOCAL_MODEL_INCLUDE}" \
            LOCAL_MODEL_DIR="${LOCAL_MODEL_DIR}" \
            HF_TOKEN="${HF_TOKEN_VALUE}" \
            python scripts/download_local_model.py \
            || if [ "$LOCAL_MODEL_DOWNLOAD_REQUIRED" = "true" ]; then exit 1; else echo "WARNING: local model download failed; runtime can fall back to OpenAI"; fi); \
    fi

# Copiar código
COPY src/ ./src/

# Expor porta
EXPOSE 8001

# Comando para iniciar a aplicação
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"] 
