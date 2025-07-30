# Emotion Service - Empath.IA v3.1

Serviço de análise emocional facial para o Empath.IA, utilizando **DeepFace otimizado** como processador principal para detecção e análise de emoções faciais com **acurácia aprimorada** e **múltiplos detectores** com fallback automático.

## 🎯 Visão Geral

O **Emotion Service v3.1** é responsável por:

- **Análise otimizada** de expressões faciais usando DeepFace com múltiplos detectores
- **Detecção robusta** de 7 emoções: angry, disgust, fear, happy, sad, surprise, neutral
- **Múltiplos detectores** com fallback automático: RetinaFace → MTCNN → OpenCV → MediaPipe
- **Pré-processamento inteligente** com CLAHE e redução de ruído
- **Calibração de emoções** baseada em datasets reais (JAFFE)
- **Controle flexível** entre processadores DeepFace e Legacy
- **Processamento em tempo real** com `enforce_detection=False`
- **API compatível** com versões anteriores
- **Integração completa** com sistema de captura de emoções do Gateway

## 🚀 Tecnologias Utilizadas

### 🎯 Processador Principal - DeepFace Otimizado v3.1
- **DeepFace**: Framework moderno para análise facial e reconhecimento de emoções
- **7 Emoções**: angry, disgust, fear, happy, sad, surprise, neutral
- **Múltiplos Detectores**: RetinaFace, MTCNN, OpenCV, MediaPipe (fallback automático)
- **Pré-processamento**: CLAHE, redução de ruído, redimensionamento inteligente
- **Calibração**: Ajustes baseados em datasets reais para maior acurácia
- **Threshold Adaptativo**: Confiança mínima configurável (padrão: 0.3)
- **Enforce Detection False**: Permite análise mesmo com faces parcialmente detectadas
- **Real-time**: Processamento otimizado para aplicações em tempo real

## 🏗️ Arquitetura v3.1

```
Emotion Service v3.1 (Otimizado)
├── FastAPI (Framework Web)
├── DeepFace Otimizado (Processador Principal)
│   ├── Multiple Detector Backends
│   │   ├── RetinaFace (Máxima Precisão)
│   │   ├── MTCNN (Alta Precisão)
│   │   ├── OpenCV (Rapidez)
│   │   └── MediaPipe (Fallback Robusto)
│   ├── Enhanced Preprocessing
│   │   ├── CLAHE (Contrast Enhancement)
│   │   ├── Bilateral Filter (Noise Reduction)
│   │   └── Smart Resizing (224x224+)
│   ├── Emotion Calibration Engine
│   │   ├── JAFFE Dataset Tuning
│   │   ├── Per-emotion Scaling
│   │   └── Confidence Thresholding
│   └── 7 Standard Emotions + Confidence
├── Legacy Processor (Fallback)
│   ├── OpenFace/MediaPipe Pipeline
│   ├── Action Units Detection
│   └── Emotion Mapping
├── Flexible Control System
│   ├── Environment Variables
│   ├── Runtime Processor Selection
│   └── Automatic Fallback Logic
├── OpenCV (Enhanced Processing)
│   ├── BGR/RGB Conversion
│   ├── Advanced Image Enhancement
│   └── Format Compatibility
└── Comprehensive Testing
    ├── Integration Tests (pytest)
    ├── Performance Tests (latency)
    ├── Accuracy Evaluation (JAFFE)
    └── Multi-detector Validation
```

## 🎯 Otimizações de Acurácia v3.1

### Melhorias Implementadas

#### 1. **Múltiplos Detectores com Fallback**
- **RetinaFace**: Detector mais preciso para faces bem definidas
- **MTCNN**: Alternativa robusta com boa precisão
- **OpenCV**: Detector rápido para casos simples
- **MediaPipe**: Fallback final, sempre funcional

#### 2. **Pré-processamento Inteligente**
```python
# Melhorias automáticas aplicadas:
- Redimensionamento mínimo para 224x224 (padrão CNN)
- CLAHE para melhoria de contraste
- Filtro bilateral para redução de ruído
- Conversão de espaço de cores otimizada
```

#### 3. **Calibração de Emoções**
```python
# Ajustes baseados em análise JAFFE:
emotion_calibration = {
    "anger": 0.85,    # Bem detectado
    "disgust": 1.2,   # Amplificado
    "fear": 1.1,      # Boost necessário
    "happy": 0.9,     # Reduzido overconfidence
    "sad": 1.15,      # Amplificado
    "surprise": 1.0,  # Balanceado
    "neutral": 0.95   # Ligeiramente reduzido
}
```

#### 4. **Threshold de Confiança Adaptativo**
- **Threshold padrão**: 0.3 (configurável)
- **Fallback para neutral**: Quando confiança < threshold
- **Normalização**: Garantia de probabilidades somando 1.0

## ⚙️ Configuração Avançada v3.1

### Variáveis de Ambiente

O serviço pode ser configurado através das seguintes variáveis de ambiente:

```bash
# === CONFIGURAÇÕES BÁSICAS ===
EMOTION_SERVICE_PORT=8003                    # Porta do serviço
EMOTION_CONFIDENCE_THRESHOLD=0.3             # Threshold mínimo de confiança
SHARED_DATA_DIR=/shared_data                 # Diretório compartilhado
DEBUG=false                                  # Modo debug

# === CONTROLE DE PROCESSADORES ===
FORCE_LEGACY_PROCESSOR=false                # Usar Legacy como principal
USE_LEGACY_FALLBACK=true                     # Habilitar fallback entre processadores
```

### Modos de Operação

#### 1. **Modo DeepFace Otimizado (Padrão Recomendado)**
```bash
FORCE_LEGACY_PROCESSOR=false
USE_LEGACY_FALLBACK=true
```
- **Processador principal**: DeepFace com múltiplos detectores e calibração
- **Fallback**: Legacy (OpenFace/MediaPipe)
- **Características**: Máxima acurácia com robustez
- **Uso**: Produção, análise crítica

#### 2. **Modo Legacy Forçado**
```bash
FORCE_LEGACY_PROCESSOR=true
USE_LEGACY_FALLBACK=true
```
- **Processador principal**: Legacy (OpenFace/MediaPipe)
- **Fallback**: DeepFace otimizado
- **Características**: Compatibilidade total com v1.0
- **Uso**: Debugging, comparação de resultados

#### 3. **Modo DeepFace Puro**
```bash
FORCE_LEGACY_PROCESSOR=false
USE_LEGACY_FALLBACK=false
```
- **Processador principal**: DeepFace apenas
- **Fallback**: Nenhum
- **Características**: Máxima precisão (pode falhar mais)
- **Uso**: Análise especializada, dados controlados

#### 4. **Modo Legacy Puro**
```bash
FORCE_LEGACY_PROCESSOR=true
USE_LEGACY_FALLBACK=false
```
- **Processador principal**: Legacy apenas
- **Fallback**: Nenhum
- **Características**: Máxima velocidade (menor precisão)
- **Uso**: Processamento em lote, recursos limitados

### Detectores Disponíveis

| Detector | Precisão | Velocidade | Recursos | Casos de Uso |
|----------|----------|------------|----------|-------------|
| **RetinaFace** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Alto | Análise crítica, fotos HD |
| **MTCNN** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Médio | Boa qualidade geral |
| **OpenCV** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Baixo | Processamento rápido |
| **MediaPipe** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Baixo | Tempo real, fallback |

### Processamento de Emoções

O serviço v2.0 detecta as seguintes emoções:

#### Emoções Básicas (EmotiEffLib)
- **Joy** (Alegria): Alta ativação, valência positiva
- **Sadness** (Tristeza): Baixa ativação, valência negativa
- **Anger** (Raiva): Alta ativação, valência negativa
- **Fear** (Medo): Alta ativação, valência negativa
- **Surprise** (Surpresa): Alta ativação, valência neutra
- **Disgust** (Nojo): Baixa ativação, valência negativa
- **Contempt** (Desprezo): Baixa ativação, valência negativa
- **Neutral** (Neutro): Ativação e valência equilibradas

#### Dimensões Adicionais
- **Valence**: Dimensão prazer/desprazer (-1 a +1)
- **Arousal**: Dimensão ativação/calma (-1 a +1)

## 🔌 API Endpoints

### Health Check
```http
GET /health
```

**Resposta v2.0:**
```json
{
  "status": "healthy",
  "service": "emotion-service",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "2.0.0",
  "processor_type": "EmotiEffLib EfficientFormer-Lite S0",
  "processor_available": true,
  "device": "cpu",
  "cuda_available": false
}
```

### Análise de Expressão Facial
```http
POST /analyze-facial-expression
Content-Type: multipart/form-data
```

**Request:**
```
file: [imagem.jpg]
```

**Resposta v2.0:**
```json
{
  "emotions": {
    "joy": 0.78,
    "sadness": 0.05,
    "anger": 0.03,
    "fear": 0.02,
    "surprise": 0.07,
    "disgust": 0.02,
    "neutral": 0.03
  },
  "dominant_emotion": "joy",
  "confidence": 0.78,
  "status": "success",
  "message": "Análise facial realizada com sucesso",
  "service": "emotion-service",
  "filename": "imagem.jpg",
  "face_detected": true,
  "processing_time_ms": 145,
  "model_info": {
    "processor": "EmotiEffLib EfficientFormer-Lite S0",
    "device": "cpu",
    "model_path": null
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Análise em Tempo Real (Base64)
```http
POST /analyze-realtime
Content-Type: application/json
```

**Request:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
}
```

**Resposta v2.0:**
```json
{
  "emotions": {
    "joy": 0.65,
    "surprise": 0.20,
    "neutral": 0.15
  },
  "dominant_emotion": "joy",
  "confidence": 0.65,
  "status": "success",
  "face_detected": true,
  "processing_time_ms": 89,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Configuração v2.0
```http
GET /config
```

**Resposta:**
```json
{
  "processor_type": "EmotiEffLib EfficientFormer-Lite S0",
  "use_legacy_landmarks": false,
  "emotion_model_path": null,
  "confidence_threshold": 0.7,
  "service_port": "8003",
  "debug": false,
  "device": "cpu",
  "cuda_available": false,
  "shared_data_dir": "/shared_data"
}
```

## ⚙️ Configuração

### Dependências v2.0

```txt
# Core FastAPI
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.4.2

# Image Processing
opencv-python==4.8.1.78
pillow==10.0.1
numpy==1.24.3

# EmotiEffLib Dependencies
emotiefflib>=0.4.2
onnxruntime>=1.18.0
face-alignment>=1.5.1
torch>=2.0.0

# Legacy MediaPipe (fallback)
mediapipe==0.10.7

# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
httpx>=0.24.0

# Quantization
onnx>=1.14.0
onnxconverter-common>=1.13.0
```

### Variáveis de Ambiente v3.0

```bash
# Service Configuration
EMOTION_SERVICE_PORT=8003
DEBUG=false
LOG_LEVEL=INFO

# DeepFace Configuration
DEEPFACE_DETECTOR_BACKEND=mediapipe  # mediapipe, opencv, retinaface, etc.
EMOTION_CONFIDENCE_THRESHOLD=0.7

# Processing
MAX_IMAGE_SIZE=1024
PROCESSING_TIMEOUT=30
```

## 📊 Benchmark de Performance

### DeepFace Performance

| Detector Backend | Precisão | CPU (i7) | GPU (RTX) | Memória |
|------------------|----------|----------|-----------|---------|
| MediaPipe | Excelente | 250ms | 120ms | 256MB |
| OpenCV | Boa | 180ms | 90ms | 128MB |
| RetinaFace | Superior | 350ms | 150ms | 512MB |

### Performance Targets

- **Latência P95**: ≤ 300ms (CPU i7)
- **Throughput**: ≥ 8 req/s (CPU), ≥ 25 req/s (GPU)
- **Acurácia**: ≥ 90% (DeepFace standard models)
- **Memória**: ≤ 256MB (configuração padrão)

## 🚀 Execução

### Docker (Recomendado) [[memory:3753451]]
```bash
# Usar docker-compose para iniciar o serviço
docker-compose up emotion-service

# Com detector personalizado
DEEPFACE_DETECTOR_BACKEND=retinaface docker-compose up emotion-service
```

### Desenvolvimento Local
```bash
# 1. Navegar para o diretório
cd services/emotion-service

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar o serviço (modo padrão)
uvicorn src.main:app --host 0.0.0.0 --port 8003 --reload

# 4. Executar com detector personalizado
DEEPFACE_DETECTOR_BACKEND=opencv uvicorn src.main:app --host 0.0.0.0 --port 8003
```

## 🔧 Ferramentas e Desenvolvimento

### Estrutura do Projeto v3.0

```
services/emotion-service/
├── src/
│   ├── main.py                                  # Aplicação FastAPI principal
│   ├── processors/
│   │   ├── deepface_processor.py               # Processador DeepFace (Principal)
│   │   ├── facial_emotion_processor.py         # Wrapper de compatibilidade (legacy)
│   │   ├── emoti_eff_processor.py              # Processador EmotiEffLib (legacy)
│   │   └── facial_emotion_processor_legacy.py  # Processador MediaPipe (legacy)
│   └── api/
├── tools/
│   └── export_quantized.py                     # Script de quantização ONNX (legacy)
├── tests/
│   ├── assets/                                 # Imagens de teste
│   └── test_emotion_service.py                 # Testes de integração
├── requirements.txt                            # Dependências Python
├── Dockerfile                                  # Container de produção
└── README.md
```

### Quantização de Modelos

```bash
# Exportar todos os formatos (FP32, FP16, INT8)
python tools/export_quantized.py --model-name efficientformer_lite_s0 --formats all --validate

# Exportar apenas INT8
python tools/export_quantized.py --formats int8 --output-dir models

# Com validação detalhada
python tools/export_quantized.py --validate --calibration-dir tests/assets
```

### Testando o Serviço v2.0

```bash
# Health check
curl http://localhost:8003/health

# Verificar configuração
curl http://localhost:8003/config

# Testar análise de imagem
curl -X POST http://localhost:8003/analyze-facial-expression \
  -F "file=@test_image.jpg"

# Teste de performance
python evaluate.py --assets-dir tests/assets --verbose

# Executar testes de integração
pytest tests/test_emotion_service.py -v

# Teste de performance específico
pytest tests/test_emotion_service.py::TestPerformance::test_latency_requirement -v
```

### Avaliação de Acurácia

```bash
# Avaliação básica (cria imagens sintéticas se necessário)
python evaluate.py

# Avaliação com imagens personalizadas
python evaluate.py --assets-dir /path/to/test/images

# Salvar resultados detalhados
python evaluate.py --output evaluation_results.json --verbose

# Criar apenas imagens sintéticas para teste
python evaluate.py --create-synthetic --assets-dir tests/assets
```

## 🔒 Segurança e Privacidade

### Proteções Implementadas v2.0

- ✅ **Validação de arquivos**: Apenas imagens são aceitas
- ✅ **Processamento em memória**: Sem arquivos temporários desnecessários
- ✅ **Limpeza automática**: Remoção de dados temporários
- ✅ **Limitação de tamanho**: Proteção contra uploads grandes
- ✅ **Não persistência**: Imagens não são armazenadas
- ✅ **Logs seguros**: Sem dados sensíveis nos logs
- ✅ **Processamento local**: Modelos executam localmente (sem APIs externas)
- ✅ **Modelos quantizados**: Redução de pegada computacional

### Considerações de Privacidade

- Processamento completamente local (sem APIs externas)
- Imagens processadas apenas em memória
- Nenhum dado facial é persistido
- Análise acontece em tempo real sem armazenamento
- Modelos pré-treinados não coletam dados

## 🐛 Troubleshooting

### Problemas Comuns v2.0

1. **EmotiEffLib não disponível**
   ```bash
   # Instalar EmotiEffLib
   pip install emotiefflib>=0.4.2
   
   # Verificar instalação
   python -c "from emotiefflib import EmotionPredictor; print('EmotiEffLib OK')"
   
   # Fallback para modo legacy
   USE_LEGACY_LANDMARKS=true uvicorn src.main:app
   ```

2. **Performance baixa**
   ```bash
   # Usar modelo quantizado INT8
   python tools/export_quantized.py --formats int8
   export EMOTION_MODEL_PATH=models/efficientformer_lite_s0_int8.onnx
   
   # Verificar uso de GPU
   curl http://localhost:8003/config | jq '.cuda_available'
   ```

3. **Face não detectada**
   ```bash
   # Verificar qualidade da imagem
   # - Boa iluminação
   # - Face claramente visível  
   # - Resolução ≥ 224x224
   
   # Testar com imagem sintética
   python evaluate.py --create-synthetic
   ```

4. **Modelos não carregam**
   ```bash
   # Verificar dependências ONNX
   pip install onnxruntime>=1.18.0
   
   # Verificar caminho do modelo
   ls -la $EMOTION_MODEL_PATH
   
   # Usar modelo padrão
   unset EMOTION_MODEL_PATH
   ```

## 📊 Monitoramento v3.0

### Métricas Importantes

- **Taxa de detecção de faces**: Percentual de sucesso (DeepFace)
- **Tempo de processamento**: Latência por análise (target: <300ms)
- **Distribuição de emoções**: 7 emoções padrão detectadas
- **Taxa de erro**: Falhas no processamento
- **Uso de recursos**: CPU/GPU e memória
- **Backend detector**: MediaPipe, OpenCV ou RetinaFace

### Logs de Debug v3.0

O serviço produz logs estruturados para monitoramento:

```
[INFO] Inicializando DeepFaceProcessor com detector: mediapipe
[INFO] ✅ Modelos DeepFace inicializados com sucesso  
[INFO] Processando imagem: test.jpg
[DEBUG] Resultado DeepFace: {'happy': 0.85, 'surprise': 0.03, 'neutral': 0.02}
[INFO] Análise concluída: happy (0.85) em 250ms
```

### Dashboard de Métricas

```bash
# Verificar status geral
curl http://localhost:8003/health | jq

# Métricas de configuração
curl http://localhost:8003/config | jq

# Estatísticas de uso
curl http://localhost:8003/stats | jq
```

## 💡 Integração com Gateway

O Emotion Service v2.0 é chamado pelo Gateway Service para:

- Análise de estado emocional durante conversas terapêuticas
- Captura de emoções em tempo real via webcam  
- Contextualização de respostas baseadas no estado emocional
- Timeline emocional das sessões
- Insights de valência e arousal para análise de humor

```python
# Exemplo de integração no Gateway
emotion_response = await emotion_service.analyze_realtime({
    "image": webcam_base64_frame
})

# Salvar contexto emocional detalhado
await user_emotion_service.save_emotion_async({
    "username": username,
    "session_id": session_id,
    "dominant_emotion": emotion_response["dominant_emotion"],
    "confidence": emotion_response["confidence"],
    "all_emotions": emotion_response["emotions"],
    "valence": emotion_response.get("valence", 0.0),
    "arousal": emotion_response.get("arousal", 0.0),
    "processing_time_ms": emotion_response.get("processing_time_ms", 0),
    "model_info": emotion_response.get("model_info", {})
})
```

## 🔄 Migração da v1.0

### Compatibilidade de API

A v2.0 mantém **100% de compatibilidade** com a API v1.0:

- Todos os endpoints existentes funcionam sem mudanças
- Estrutura de resposta JSON idêntica
- Campos adicionais são opcionais
- Fallback para processador legacy disponível

### Guia de Migração

1. **Atualizar dependências**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Testar compatibilidade**:
   ```bash
   # Modo legacy (comportamento v1.0)
   USE_LEGACY_LANDMARKS=true uvicorn src.main:app
   ```

3. **Ativar v2.0 gradualmente**:
   ```bash
   # Padrão v2.0 (EmotiEffLib)
   uvicorn src.main:app
   ```

4. **Monitorar performance**:
   ```bash
   python evaluate.py
   ```

---

**Emotion Service v3.1** - Análise Emocional Otimizada com DeepFace Múltiplos Detectores 🧠✨

### 🆕 Novidades v3.1
- ✅ **Múltiplos detectores** com fallback automático 
- ✅ **Pré-processamento inteligente** CLAHE + redução de ruído
- ✅ **Calibração de emoções** baseada em datasets reais
- ✅ **Controle flexível** entre processadores
- ✅ **Threshold adaptativo** de confiança
- ✅ **Compatibilidade total** com v3.0 

# Emotion Service - GPU Support

## 🚀 Configuração GPU/CPU

O emotion service usa a **imagem oficial `tensorflow/tensorflow:2.15.0-gpu`** que já inclui CUDA, cuDNN e todas as otimizações necessárias para GPU NVIDIA, com fallback automático para CPU quando a GPU não estiver disponível.

### ⚙️ Requisitos para GPU

1. **Hardware**: GPU NVIDIA compatível com CUDA 11.8+ (GTX 1060+, RTX série)
2. **Docker Desktop**: Com suporte ao runtime NVIDIA habilitado
3. **Drivers NVIDIA**: Versão 470+ ou mais recente
4. **Máquina LOQ-e**: Suporte nativo à GPU dedicada

### 🐳 Executando com GPU

#### 1. Docker Desktop - GPU Dedicada  
**IMPORTANTE**: No Docker Desktop, selecione a opção "rodar na GPU dedicada" quando abrir a aplicação.

#### 2. Comando para Executar
```bash
# Build e start do emotion service com GPU
docker compose -f docker-compose.dev.yml up emotion-service --build

# Para rebuild completo (se necessário)
docker compose -f docker-compose.dev.yml build emotion-service --no-cache
docker compose -f docker-compose.dev.yml up emotion-service
```

#### 3. Verificação de GPU
Após iniciar o serviço, você pode verificar se a GPU está sendo usada:

```bash
# Check health endpoint
curl http://localhost:8003/health

# Resposta esperada com GPU:
{
  "device": {
    "type": "GPU",
    "cuda_available": true,
    "gpu_available": true,
    "gpu_count": 1
  },
  "processor_details": {
    "device_type": "GPU",
    "cuda_available": true,
    "gpu_available": true,
    "gpu_count": 1,
    "gpu_devices": [
      {
        "device_id": 0,
        "name": "/physical_device:GPU:0",
        "device_type": "GPU"
      }
    ]
  }
}
```

### 🔧 Fallback Automático CPU

Se a GPU não estiver disponível, o serviço automaticamente utilizará CPU:

```json
{
  "device": {
    "type": "CPU",
    "cuda_available": false,
    "gpu_available": false,
    "gpu_count": 0
  }
}
```

### 📊 Performance

**GPU vs CPU (com imagem TensorFlow otimizada):**
- **GPU**: ~3-7x mais rápido para inferência
- **CPU**: Funcional, mas significativamente mais lento
- **Memória**: GPU usa VRAM dedicada (configuração dinâmica)
- **Otimizações**: XLA, CUDA kernels otimizados, cuDNN

### 🛠️ Troubleshooting

#### GPU não detectada
```bash
# 1. Verificar drivers NVIDIA no host
nvidia-smi

# 2. Verificar runtime Docker
docker info | grep nvidia

# 3. Testar GPU container simples
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi

# 4. Verificar logs do emotion service
docker compose -f docker-compose.dev.yml logs emotion-service
```

#### Erro de memória GPU
```bash
# Os seguintes parâmetros estão configurados automaticamente:
# - TF_FORCE_GPU_ALLOW_GROWTH=true
# - TF_GPU_MEMORY_ALLOW_GROWTH=true
# - Alocação dinâmica de memória GPU
```

#### Fallback para CPU
```bash
# Se houver problemas com GPU, o serviço automaticamente usa CPU
# Check os logs para identificar a causa:
docker compose -f docker-compose.dev.yml logs emotion-service | grep -i gpu
```

### 🎯 Configurações Avançadas

**Imagem Base**: `tensorflow/tensorflow:2.15.0-gpu`
- **Inclui**: CUDA 11.8, cuDNN 8.6, TensorFlow 2.15 otimizado
- **Tamanho**: ~4GB (com todas otimizações GPU)

**Variáveis de ambiente otimizadas**:
```yaml
environment:
  # GPU/CUDA Core
  - NVIDIA_VISIBLE_DEVICES=all
  - NVIDIA_DRIVER_CAPABILITIES=compute,utility
  
  # TensorFlow GPU Optimizations
  - TF_FORCE_GPU_ALLOW_GROWTH=true
  - TF_GPU_MEMORY_ALLOW_GROWTH=true
  - TF_XLA_FLAGS=--tf_xla_enable_xla_devices
  
  # CUDA Performance
  - CUDA_CACHE_DISABLE=0
  - CUDA_CACHE_MAXSIZE=2147483648
```

### 📈 Benchmarks

Testes com imagem 640x480:
- **GPU (RTX 3060)**: ~50-80ms por inferência
- **GPU (GTX 1060)**: ~100-150ms por inferência  
- **CPU (8 cores)**: ~400-800ms por inferência
