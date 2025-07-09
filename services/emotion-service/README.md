# Emotion Service - Empath.IA

Serviço de análise emocional facial para o Empath.IA, utilizando OpenFace e MediaPipe para detecção e análise de emoções em tempo real.

## 🎯 Visão Geral

O **Emotion Service** é responsável por:

- Análise de expressões faciais em imagens
- Detecção de emoções em tempo real via webcam
- Processamento de Action Units (AUs) com OpenFace
- Interpretação emocional baseada em análise facial
- Análise de vídeos com timeline emocional
- Integração com sistema de captura de emoções do Gateway

## 🚀 Funcionalidades

### ✅ Implementadas

- [x] **Análise de Expressão Facial**: Detecção de emoções em imagens
- [x] **Processamento em Tempo Real**: Análise via Base64 para webcam
- [x] **Action Units Detection**: Análise de unidades de ação facial
- [x] **Interpretação Emocional**: Mapeamento de AUs para emoções
- [x] **Fallback System**: Dados simulados quando OpenFace não está disponível
- [x] **Health Check**: Endpoint de status do serviço
- [x] **CORS**: Suporte a requisições cross-origin
- [x] **Logging Estruturado**: Sistema de logs detalhado

### 🔄 Em Desenvolvimento

- [ ] **Análise de Vídeo**: Processamento frame-by-frame completo
- [ ] **Calibração Personalizada**: Ajuste de sensibilidade por usuário
- [ ] **Detecção de Múltiplas Faces**: Análise de várias pessoas
- [ ] **Histórico de Emoções**: Armazenamento temporal
- [ ] **Análise Contextual**: Consideração de contexto situacional

### 📋 Planejadas

- [ ] **Machine Learning Customizado**: Modelos personalizados por usuário
- [ ] **Integração com Wearables**: Dados biométricos complementares
- [ ] **Análise de Micro-expressões**: Detecção de emoções sutis
- [ ] **API de Streaming**: Análise contínua de vídeo
- [ ] **Métricas de Confiabilidade**: Avaliação de precisão

## 🏗️ Arquitetura

```
Emotion Service
├── FastAPI (Framework Web)
├── OpenFace (Facial Analysis)
├── MediaPipe (Face Detection)
├── PIL (Image Processing)
├── Action Units Processor
├── Emotion Interpreter
└── Real-time Analysis Engine
```

### Componentes Principais

- **FastAPI**: Framework web para APIs REST
- **OpenFace**: Processamento de Action Units faciais
- **MediaPipe**: Detecção de faces e landmarks
- **Emotion Processor**: Interpretação de emoções
- **Real-time Engine**: Análise em tempo real

## 🔌 API Endpoints

### Health Check
```http
GET /health
```

**Resposta:**
```json
{
  "status": "healthy",
  "service": "emotion-service",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "mediapipe_available": true
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

**Resposta:**
```json
{
  "emotions": {
    "joy": 0.65,
    "sadness": 0.10,
    "anger": 0.05,
    "fear": 0.05,
    "surprise": 0.10,
    "disgust": 0.05
  },
  "dominant_emotion": "joy",
  "confidence": 0.85,
  "status": "success",
  "message": "Análise facial realizada com sucesso",
  "service": "emotion-service",
  "filename": "imagem.jpg",
  "face_detected": true,
  "action_units": {
    "AU01": 0.2,
    "AU02": 0.8,
    "AU06": 0.9,
    "AU12": 0.7
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Análise em Tempo Real
```http
POST /analyze-realtime
Content-Type: application/json
```

**Request:**
```json
{
  "image": "base64_encoded_image_data",
  "username": "joao_silva",
  "session_id": "session-2"
}
```

**Resposta:**
```json
{
  "emotions": {
    "joy": 0.75,
    "anxiety": 0.25
  },
  "dominant_emotion": "joy",
  "confidence": 0.80,
  "face_detected": true,
  "timestamp": "2024-01-01T12:00:00Z",
  "processing_time": 0.15
}
```

### Análise de Vídeo (Em Desenvolvimento)
```http
POST /analyze-video
Content-Type: multipart/form-data
```

**Request:**
```
file: [video.mp4]
```

**Resposta:**
```json
{
  "timeline": [
    {
      "timestamp": 0.0,
      "emotions": {"joy": 0.8, "sadness": 0.2},
      "dominant_emotion": "joy"
    },
    {
      "timestamp": 1.0,
      "emotions": {"joy": 0.6, "sadness": 0.4},
      "dominant_emotion": "joy"
    }
  ],
  "summary": {
    "avg_emotions": {"joy": 0.7, "sadness": 0.3},
    "dominant_emotion": "joy",
    "duration": 2.0
  },
  "status": "development",
  "service": "emotion-service"
}
```

### Configuração
```http
GET /config
```

**Resposta:**
```json
{
  "openface_available": true,
  "mediapipe_available": true,
  "service_port": "8003",
  "debug": false,
  "models": {
    "emotion_model": "action_units_v1",
    "face_detector": "mediapipe"
  }
}
```

### Estatísticas
```http
GET /stats
```

**Resposta:**
```json
{
  "analyses_performed": 1250,
  "faces_detected": 1100,
  "detection_rate": 0.88,
  "avg_processing_time": 0.12,
  "most_common_emotion": "joy",
  "service_uptime": "2h 30m"
}
```

## 🧠 Análise de Emoções

### Emoções Suportadas

- **Joy** (Alegria): Expressões positivas, sorrisos
- **Sadness** (Tristeza): Expressões melancólicas, desânimo
- **Anger** (Raiva): Expressões de irritação, frustração
- **Fear** (Medo): Expressões de ansiedade, nervosismo
- **Surprise** (Surpresa): Expressões de espanto, admiração
- **Disgust** (Nojo): Expressões de repulsa, desagrado
- **Neutral** (Neutro): Estado emocional equilibrado

### Action Units (AUs) Principais

- **AU01**: Inner Brow Raiser (sobrancelha interna levantada)
- **AU02**: Outer Brow Raiser (sobrancelha externa levantada)
- **AU04**: Brow Lowerer (sobrancelha abaixada)
- **AU06**: Cheek Raiser (bochechas levantadas)
- **AU12**: Lip Corner Puller (cantos da boca puxados)
- **AU15**: Lip Corner Depressor (cantos da boca abaixados)
- **AU20**: Lip Stretcher (lábios esticados)
- **AU25**: Lips Part (lábios separados)

### Interpretação Emocional

```python
# Exemplo de mapeamento AU -> Emoção
{
  "joy": ["AU06", "AU12"],          # Bochechas + sorriso
  "sadness": ["AU01", "AU04", "AU15"], # Sobrancelhas + boca triste
  "anger": ["AU04", "AU07", "AU23"],   # Sobrancelhas + olhos + lábios
  "fear": ["AU01", "AU02", "AU05"],    # Sobrancelhas + olhos abertos
  "surprise": ["AU01", "AU02", "AU25"], # Sobrancelhas + boca aberta
  "disgust": ["AU09", "AU15", "AU16"]   # Nariz + boca repulsa
}
```

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# Service Configuration
EMOTION_SERVICE_PORT=8003
DEBUG=false
LOG_LEVEL=INFO

# OpenFace Configuration
OPENFACE_AVAILABLE=true
OPENFACE_MODEL_PATH=/app/models/openface
USE_FALLBACK_ON_ERROR=true

# MediaPipe Configuration
MEDIAPIPE_MODEL_COMPLEXITY=1
MEDIAPIPE_MIN_DETECTION_CONFIDENCE=0.5
MEDIAPIPE_MIN_TRACKING_CONFIDENCE=0.5

# Processing
MAX_IMAGE_SIZE=1024
SUPPORTED_FORMATS=jpg,jpeg,png,webp
PROCESSING_TIMEOUT=30
```

### Instalação Local

```bash
# 1. Clone o repositório
cd services/emotion-service

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente
export EMOTION_SERVICE_PORT=8003
export DEBUG=true

# 4. Execute o serviço
python -m uvicorn src.main:app --host 0.0.0.0 --port 8003 --reload
```

### Docker

```bash
# Build da imagem
docker build -t empath-ia-emotion-service .

# Execução
docker run -p 8003:8003 \
  -e DEBUG=true \
  -e OPENFACE_AVAILABLE=true \
  empath-ia-emotion-service
```

## 🔧 Desenvolvimento

### Estrutura do Projeto

```
services/emotion-service/
├── src/
│   ├── main.py                         # Aplicação FastAPI
│   ├── processors/
│   │   ├── facial_emotion_processor.py # Processador principal
│   │   └── openface_processor.py       # Integração OpenFace
│   ├── models/
│   │   ├── emotion_models.py           # Modelos de emoção
│   │   └── action_units.py             # Definições de AUs
│   └── utils/
│       ├── image_processing.py         # Processamento de imagem
│       └── emotion_mapping.py          # Mapeamento AU -> Emoção
├── tests/
│   ├── test_emotion_analysis.py
│   ├── test_realtime_processing.py
│   └── test_openface_integration.py
├── models/                             # Modelos OpenFace
├── requirements.txt
├── Dockerfile
└── README.md
```

### Testando Funcionalidades

```bash
# Testar análise de imagem
curl -X POST http://localhost:8003/analyze-facial-expression \
  -F "file=@test_image.jpg"

# Testar análise em tempo real
curl -X POST http://localhost:8003/analyze-realtime \
  -H "Content-Type: application/json" \
  -d '{
    "image": "base64_encoded_image",
    "username": "test_user",
    "session_id": "test_session"
  }'

# Verificar saúde do serviço
curl http://localhost:8003/health

# Verificar configuração
curl http://localhost:8003/config
```

## 🚀 Deploy

### Docker Compose

```yaml
# docker-compose.yml
emotion-service:
  build: ./services/emotion-service
  environment:
    - EMOTION_SERVICE_PORT=8003
    - DEBUG=false
    - OPENFACE_AVAILABLE=true
  ports:
    - "8003:8003"
  volumes:
    - ./models:/app/models
  networks:
    - empathia-network
```

## 📊 Monitoramento

### Métricas Importantes

- **Detecção de Faces**: Taxa de sucesso na detecção
- **Tempo de Processamento**: Latência média por análise
- **Precisão Emocional**: Confiabilidade das análises
- **Uso de Recursos**: CPU e memória durante processamento
- **Erro Rate**: Taxa de falhas no processamento

### Alertas Importantes

- Falha na detecção de faces (>20%)
- Tempo de processamento elevado (>5s)
- Erro na análise emocional
- Indisponibilidade do OpenFace
- Uso excessivo de memória

## 🔒 Segurança

### Proteções Implementadas

- ✅ Validação de tipo de arquivo
- ✅ Limpeza de arquivos temporários
- ✅ Limitação de tamanho de imagem
- ✅ Sanitização de dados de entrada
- ✅ Não armazenamento de imagens processadas
- ✅ Logs sem dados sensíveis

### Considerações de Privacidade

- Imagens são processadas em memória
- Arquivos temporários são removidos imediatamente
- Dados faciais não são armazenados permanentemente
- Análise acontece localmente (sem envio para terceiros)

## 🐛 Troubleshooting

### Problemas Comuns

1. **OpenFace não disponível**
   ```bash
   # Verificar logs
   docker logs empath-ia-emotion-service-1 | grep "OpenFace"
   
   # Usar modo fallback
   curl http://localhost:8003/analyze-facial-expression \
     -F "file=@test.jpg" # Retornará dados simulados
   ```

2. **Face não detectada**
   ```bash
   # Verificar qualidade da imagem
   # Imagem deve ter boa iluminação e face visível
   
   # Verificar configuração MediaPipe
   curl http://localhost:8003/config
   ```

3. **Timeout no processamento**
   ```bash
   # Reduzir tamanho da imagem
   # Verificar configuração de timeout
   export PROCESSING_TIMEOUT=60
   ```

## 💡 Integração com Gateway

O Emotion Service é integrado ao Gateway Service para:

- Captura de emoções em tempo real durante conversas
- Análise de estado emocional do usuário
- Contextualização de respostas terapêuticas
- Armazenamento de timeline emocional

```python
# Exemplo de integração
response = await emotion_service.analyze_realtime({
    "image": webcam_base64,
    "username": "joao_silva",
    "session_id": "session-2"
})

# Salvar emoção no contexto da sessão
await user_emotion_service.save_emotion_async({
    "username": "joao_silva",
    "session_id": "session-2",
    "dominant_emotion": response["dominant_emotion"],
    "confidence": response["confidence"]
})
```

---

**Emotion Service v1.0** - Análise Emocional Facial Inteligente 😊💙 