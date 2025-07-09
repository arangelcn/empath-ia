# Avatar Service - Empath.IA

Serviço de geração de avatares falantes para o Empath.IA, com integração planejada para DID-AI para criação de avatares terapêuticos realistas.

## 🎯 Visão Geral

O **Avatar Service** é responsável por:

- Geração de avatares falantes realistas
- Integração com DID-AI para síntese de vídeo
- Personalização de avatares terapêuticos
- Sincronização de áudio com movimentos labiais
- Gestão de avatares disponíveis no sistema
- Integração com sistema de síntese de voz

## 🚀 Status de Desenvolvimento

### ✅ Implementado (Básico)

- [x] **Estrutura FastAPI**: API REST básica
- [x] **Health Check**: Endpoint de status do serviço
- [x] **Configuração**: Sistema de configuração básico
- [x] **Lista de Avatares**: Endpoint para listar avatares disponíveis
- [x] **CORS**: Suporte a requisições cross-origin
- [x] **Logging**: Sistema de logs básico

### 🔄 Em Desenvolvimento

- [ ] **Integração DID-AI**: Conexão com API da D-ID
- [ ] **Geração de Vídeo**: Criação de avatares falantes
- [ ] **Personalização**: Customização de avatares
- [ ] **Sincronização**: Sync áudio-visual
- [ ] **Cache**: Sistema de cache para vídeos

### 📋 Planejado

- [ ] **Múltiplos Avatares**: Biblioteca de avatares terapêuticos
- [ ] **Expressões Faciais**: Avatares com emoções
- [ ] **Gestos**: Movimentos corporais naturais
- [ ] **Qualidade Adaptativa**: Ajuste automático de qualidade
- [ ] **Streaming**: Geração de vídeo em tempo real

## 🏗️ Arquitetura

```
Avatar Service
├── FastAPI (Framework Web)
├── DID-AI Integration (Planejado)
├── Video Generation Engine (Planejado)
├── Avatar Management System
├── Audio Sync Engine (Planejado)
└── Cache System (Planejado)
```

### Componentes Principais

- **FastAPI**: Framework web para APIs REST
- **DID-AI Client**: Integração com D-ID API (planejado)
- **Avatar Manager**: Gerenciamento de avatares disponíveis
- **Video Generator**: Geração de vídeos falantes (planejado)
- **Sync Engine**: Sincronização audio-visual (planejado)

## 🔌 API Endpoints

### Health Check
```http
GET /health
```

**Resposta:**
```json
{
  "status": "healthy",
  "service": "avatar-service",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0"
}
```

### Geração de Avatar (Em Desenvolvimento)
```http
POST /generate-avatar
Content-Type: application/json
```

**Request:**
```json
{
  "avatar_id": "default-therapist",
  "text": "Olá! Como posso ajudá-lo hoje?",
  "voice_settings": {
    "voice_id": "pt-BR-Neural2-A",
    "speed": 1.0,
    "emotion": "calm"
  },
  "video_settings": {
    "quality": "high",
    "format": "mp4",
    "resolution": "720p"
  }
}
```

**Resposta:**
```json
{
  "video_url": "https://placeholder.video/avatar-demo.mp4",
  "status": "development",
  "message": "Avatar service em desenvolvimento - DID-AI será integrado em breve",
  "service": "avatar-service",
  "processing_time": 0.1,
  "duration": 5.2,
  "format": "mp4",
  "resolution": "720p"
}
```

### Listar Avatares
```http
GET /avatars
```

**Resposta:**
```json
{
  "avatars": [
    {
      "id": "default-therapist",
      "name": "Terapeuta Padrão",
      "type": "professional",
      "status": "available",
      "description": "Avatar terapêutico padrão com aparência profissional",
      "thumbnail": "https://placeholder.image/therapist.jpg",
      "supported_languages": ["pt-BR"],
      "emotions": ["neutral", "calm", "empathetic", "concerned"]
    },
    {
      "id": "friendly-counselor",
      "name": "Conselheiro Amigável",
      "type": "casual",
      "status": "planned",
      "description": "Avatar com abordagem mais casual e amigável",
      "thumbnail": "https://placeholder.image/counselor.jpg",
      "supported_languages": ["pt-BR"],
      "emotions": ["happy", "supportive", "understanding"]
    }
  ],
  "total": 2,
  "service": "avatar-service"
}
```

### Configuração
```http
GET /config
```

**Resposta:**
```json
{
  "did_configured": false,
  "did_url": "https://api.d-id.com",
  "service_port": "8002",
  "debug": true,
  "features": {
    "video_generation": false,
    "audio_sync": false,
    "multiple_avatars": false,
    "emotion_support": false
  },
  "supported_formats": ["mp4", "webm"],
  "supported_resolutions": ["480p", "720p", "1080p"],
  "max_text_length": 1000
}
```

### Status de Avatar (Planejado)
```http
GET /avatars/{avatar_id}/status
```

**Resposta:**
```json
{
  "avatar_id": "default-therapist",
  "status": "ready",
  "last_used": "2024-01-01T12:00:00Z",
  "usage_count": 25,
  "average_generation_time": 3.5,
  "supported_features": [
    "text_to_video",
    "emotion_expression",
    "lip_sync"
  ]
}
```

## 🎭 Avatares Terapêuticos

### Tipos de Avatares

#### **Terapeuta Profissional**
- Aparência madura e confiável
- Expressões calmas e empáticas
- Vestuário profissional
- Gestos sutis e apropriados

#### **Conselheiro Amigável**
- Aparência acessível e calorosa
- Expressões mais animadas
- Estilo casual mas cuidado
- Gestos mais expressivos

#### **Especialista em Ansiedade**
- Expressões particularmente calmas
- Movimentos lentos e suaves
- Voz pausada e reasseguradora
- Gestos de apoio

### Expressões Emocionais

- **Neutral**: Estado padrão, expressão neutra
- **Empathetic**: Sobrancelhas levemente erguidas, olhar compreensivo
- **Concerned**: Expressão de preocupação apropriada
- **Supportive**: Sorriso sutil, expressão encorajadora
- **Calm**: Expressão serena e tranquilizadora

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# Service Configuration
AVATAR_SERVICE_PORT=8002
DEBUG=true
LOG_LEVEL=INFO

# DID-AI Configuration (Planejado)
DID_API_KEY=your_did_api_key_here
DID_API_URL=https://api.d-id.com
DID_DEFAULT_PRESENTER=default-therapist

# Video Settings
DEFAULT_VIDEO_QUALITY=720p
DEFAULT_VIDEO_FORMAT=mp4
MAX_VIDEO_DURATION=60
VIDEO_CACHE_TTL=3600

# Audio Settings
DEFAULT_VOICE=pt-BR-Neural2-A
AUDIO_SYNC_ENABLED=true
AUDIO_SAMPLE_RATE=44100

# Performance
MAX_CONCURRENT_GENERATIONS=3
GENERATION_TIMEOUT=30
CACHE_ENABLED=true
```

### Instalação Local

```bash
# 1. Clone o repositório
cd services/avatar-service

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente
export AVATAR_SERVICE_PORT=8002
export DEBUG=true
# export DID_API_KEY=your_key_here  # Quando disponível

# 4. Execute o serviço
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload
```

### Docker

```bash
# Build da imagem
docker build -t empath-ia-avatar-service .

# Execução
docker run -p 8002:8002 \
  -e DEBUG=true \
  -e DID_API_KEY=your_key \
  empath-ia-avatar-service
```

## 🔧 Desenvolvimento

### Estrutura do Projeto

```
services/avatar-service/
├── src/
│   ├── main.py                    # Aplicação FastAPI
│   ├── services/
│   │   ├── did_client.py          # Cliente D-ID (planejado)
│   │   ├── avatar_manager.py      # Gerenciamento de avatares (planejado)
│   │   └── video_generator.py     # Geração de vídeo (planejado)
│   ├── models/
│   │   ├── avatar.py              # Modelos de avatar (planejado)
│   │   ├── video_request.py       # Modelos de requisição (planejado)
│   │   └── generation_response.py # Modelos de resposta (planejado)
│   └── utils/
│       ├── video_processing.py    # Processamento de vídeo (planejado)
│       └── audio_sync.py          # Sincronização de áudio (planejado)
├── tests/
│   ├── test_avatar_generation.py  # Testes de geração (planejado)
│   ├── test_did_integration.py    # Testes D-ID (planejado)
│   └── test_avatar_manager.py     # Testes de gerenciamento (planejado)
├── assets/
│   ├── avatars/                   # Imagens de avatares
│   └── thumbnails/                # Miniaturas
├── requirements.txt
├── Dockerfile
└── README.md
```

### Testando Funcionalidades

```bash
# Verificar saúde do serviço
curl http://localhost:8002/health

# Listar avatares disponíveis
curl http://localhost:8002/avatars

# Verificar configuração
curl http://localhost:8002/config

# Testar geração de avatar (modo desenvolvimento)
curl -X POST http://localhost:8002/generate-avatar \
  -H "Content-Type: application/json" \
  -d '{
    "avatar_id": "default-therapist",
    "text": "Olá! Como posso ajudá-lo hoje?",
    "voice_settings": {
      "voice_id": "pt-BR-Neural2-A",
      "emotion": "calm"
    }
  }'
```

## 🚀 Deploy

### Docker Compose

```yaml
# docker-compose.yml
avatar-service:
  build: ./services/avatar-service
  environment:
    - AVATAR_SERVICE_PORT=8002
    - DEBUG=false
    - DID_API_KEY=${DID_API_KEY}
    - DID_API_URL=https://api.d-id.com
  ports:
    - "8002:8002"
  volumes:
    - ./assets/avatars:/app/assets/avatars
  networks:
    - empathia-network
```

## 🔗 Integração Planejada

### DID-AI Integration

O serviço será integrado com a API da D-ID para:

```python
# Exemplo de integração planejada
async def generate_avatar_video(avatar_id: str, text: str, voice_settings: dict):
    """
    Gerar vídeo de avatar falante usando D-ID
    """
    did_client = DIDClient(api_key=os.getenv("DID_API_KEY"))
    
    # Configurar apresentador
    presenter = {
        "type": "talk",
        "source_url": f"https://avatars.empathia.ai/{avatar_id}.jpg",
        "voice": {
            "type": "microsoft",
            "voice_id": voice_settings.get("voice_id"),
            "style": voice_settings.get("emotion", "neutral")
        }
    }
    
    # Gerar vídeo
    result = await did_client.create_talk(
        presenter=presenter,
        script={
            "type": "text",
            "input": text,
            "subtitles": "false"
        }
    )
    
    return {
        "video_url": result.get("result_url"),
        "status": "success",
        "duration": result.get("duration"),
        "talk_id": result.get("id")
    }
```

### Voice Service Integration

```python
# Integração com Voice Service
async def generate_with_voice_service(text: str, voice_id: str):
    """
    Gerar áudio via Voice Service e vídeo via D-ID
    """
    # 1. Gerar áudio
    voice_response = await call_voice_service(text, voice_id)
    
    # 2. Usar áudio para gerar vídeo
    video_response = await did_client.create_talk_with_audio(
        presenter_url=avatar_url,
        audio_url=voice_response["audio_url"]
    )
    
    return video_response
```

## 📊 Monitoramento

### Métricas Importantes (Planejadas)

- **Geração de Vídeos**: Taxa de sucesso na geração
- **Tempo de Processamento**: Latência média por vídeo
- **Uso de Cache**: Taxa de hit/miss do cache
- **Uso de Recursos**: CPU e memória durante geração
- **Qualidade de Vídeo**: Métricas de qualidade

### Alertas Importantes

- Falha na geração de avatar
- Tempo de processamento elevado (>10s)
- Erro na integração D-ID
- Uso excessivo de recursos
- Cache com alta taxa de miss

## 🔒 Segurança

### Proteções Implementadas

- ✅ Validação de entrada
- ✅ Limitação de tamanho de texto
- ✅ Logs sem dados sensíveis
- ✅ Sanitização de parâmetros

### Proteções Planejadas

- [ ] Rate limiting para geração de vídeos
- [ ] Validação de avatares permitidos
- [ ] Watermarking de vídeos
- [ ] Criptografia de cache
- [ ] Auditoria de uso

## 🐛 Troubleshooting

### Problemas Comuns

1. **Serviço não inicializa**
   ```bash
   # Verificar logs
   docker logs empath-ia-avatar-service-1
   
   # Verificar configuração
   curl http://localhost:8002/config
   ```

2. **D-ID não configurado**
   ```bash
   # Verificar variável de ambiente
   echo $DID_API_KEY
   
   # Testar configuração
   curl http://localhost:8002/config | jq '.did_configured'
   ```

3. **Avatar não encontrado**
   ```bash
   # Listar avatares disponíveis
   curl http://localhost:8002/avatars
   
   # Verificar ID do avatar
   curl http://localhost:8002/avatars/default-therapist/status
   ```

## 🛣️ Roadmap

### Fase 1: Básico (Atual)
- [x] Estrutura FastAPI básica
- [x] Endpoints de configuração
- [x] Sistema de avatares mockado

### Fase 2: Integração D-ID
- [ ] Integração com API D-ID
- [ ] Geração básica de vídeos
- [ ] Sistema de cache

### Fase 3: Funcionalidades Avançadas
- [ ] Múltiplos avatares
- [ ] Expressões emocionais
- [ ] Sincronização avançada

### Fase 4: Otimização
- [ ] Streaming de vídeo
- [ ] Qualidade adaptativa
- [ ] Performance otimizada

## 💡 Contribuição

Para contribuir com o Avatar Service:

1. Verifique as issues abertas
2. Implemente funcionalidades planejadas
3. Adicione testes para novas funcionalidades
4. Siga as diretrizes de código do projeto

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

**Avatar Service v1.0** - Avatares Terapêuticos Inteligentes (Em Desenvolvimento) 🎭💙 