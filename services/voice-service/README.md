# Voice Service - Google Cloud Text-to-Speech

Serviço de síntese de voz (Text-to-Speech) usando Google Cloud Text-to-Speech API com vozes neurais em português brasileiro.

## 🎯 Características

- **Provedor**: Google Cloud Text-to-Speech API
- **Idioma**: Português Brasileiro
- **Qualidade**: Vozes neurais de alta fidelidade
- **Formato**: MP3 (alta qualidade)
- **API**: RESTful com FastAPI
- **Vozes**: Múltiplas opções neurais e WaveNet

## 🎙️ Vozes Disponíveis

### Vozes Neurais (Recomendadas)
- **pt-BR-Neural2-A**: Voz feminina neural (padrão)
- **pt-BR-Neural2-B**: Voz masculina neural
- **pt-BR-Neural2-C**: Voz feminina neural alternativa

### Vozes WaveNet
- **pt-BR-Wavenet-A**: Voz feminina WaveNet
- **pt-BR-Wavenet-B**: Voz masculina WaveNet

### Vozes Standard
- **pt-BR-Standard-A**: Voz feminina padrão
- **pt-BR-Standard-B**: Voz masculina padrão

## ✨ Funcionalidades

### ✅ Implementado
- ✅ Síntese de texto em português brasileiro
- ✅ API REST completa com FastAPI
- ✅ Múltiplas vozes neurais e WaveNet
- ✅ Seleção dinâmica de voz por requisição
- ✅ Gerenciamento automático de arquivos de áudio
- ✅ URLs públicas para arquivos gerados
- ✅ Health checks e monitoramento
- ✅ Logs detalhados
- ✅ Suporte completo a Docker
- ✅ Integração com Gateway Service
- ✅ Limpeza automática de arquivos antigos

### 🔄 Planejado
- 🔄 Controle de velocidade de fala
- 🔄 Controle de tom e pitch
- 🔄 Efeitos de áudio (reverb, eco)
- 🔄 Suporte a SSML avançado

## 📋 Pré-requisitos

- Docker e Docker Compose
- Google Cloud Project com Text-to-Speech API habilitada
- Service Account JSON com permissões adequadas
- Python 3.9+ (para desenvolvimento local)

## 🛠️ Instalação e Configuração

### 1. Configuração Google Cloud

1. **Criar projeto no Google Cloud Console**
   ```bash
   # Acesse: https://console.cloud.google.com/
   ```

2. **Habilitar Text-to-Speech API**
   ```bash
   # No console: APIs & Services > Library > Cloud Text-to-Speech API > Enable
   ```

3. **Criar Service Account**
   ```bash
   # IAM & Admin > Service Accounts > Create Service Account
   # Adicionar role: Cloud Text-to-Speech User
   ```

4. **Baixar credenciais JSON**
   ```bash
   # Service Account > Keys > Add Key > Create new key > JSON
   # Salvar como: services/voice-service/credentials/empathia-462921-deff8cdf0d47.json
   ```

### 2. Docker (Recomendado)

```bash
# Construir e iniciar o serviço
docker-compose up -d voice-service

# Verificar logs
docker logs empatia-voice-service-dev -f

# Verificar saúde
curl http://localhost:8004/health
```

### 3. Desenvolvimento Local

```bash
cd services/voice-service

# Instalar dependências
pip install -r requirements.txt

# Configurar credenciais
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Executar o serviço
python -m uvicorn src.main:app --host 0.0.0.0 --port 8004 --reload
```

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Credenciais Google Cloud (obrigatório)
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/empathia-462921-deff8cdf0d47.json

# Diretório de saída dos arquivos de áudio
TTS_OUTPUT_DIR=/app/output

# URL base para servir arquivos de áudio
VOICE_SERVICE_BASE_URL=http://localhost:8004

# Configurações da API
HOST=0.0.0.0
PORT=8004
WORKERS=1

# Configurações de desenvolvimento
DEBUG=true
LOG_LEVEL=DEBUG
PYTHONPATH=/app
```

### Estrutura de Arquivos

```
services/voice-service/
├── src/
│   ├── main.py                 # FastAPI app principal
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/      # Endpoints da API
│   ├── models/                 # Modelos Pydantic
│   └── services/
│       └── gcp_tts_service.py  # Serviço Google Cloud TTS
├── credentials/
│   └── empathia-*.json         # Credenciais Google Cloud
├── output/                     # Arquivos de áudio gerados
├── requirements.txt            # Dependências Python
└── Dockerfile                  # Container Docker
```

## 📚 API Endpoints

### Health Check
```http
GET /health
```

**Resposta:**
```json
{
  "status": "healthy",
  "service": "voice-service",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "google_cloud": {
    "credentials_loaded": true,
    "project_id": "empathia-462921"
  }
}
```

### Síntese de Voz
```http
POST /api/v1/synthesize
Content-Type: application/json

{
  "text": "Olá! Como posso ajudá-lo hoje?",
  "voice": "pt-BR-Neural2-A"
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Áudio gerado com sucesso usando pt-BR-Neural2-A",
  "audio_url": "http://localhost:8004/audio/output_1234567890_abc123.mp3",
  "duration": 2.5,
  "voice_used": "pt-BR-Neural2-A",
  "text_length": 28,
  "file_size": 45678
}
```

### Obter Arquivo de Áudio
```http
GET /audio/{filename}
```

### Listar Vozes Disponíveis
```http
GET /api/v1/voices
```

**Resposta:**
```json
{
  "success": true,
  "voices": [
    {
      "name": "pt-BR-Neural2-A",
      "gender": "FEMALE",
      "type": "Neural2",
      "description": "Voz feminina neural de alta qualidade"
    },
    {
      "name": "pt-BR-Neural2-B",
      "gender": "MALE",
      "type": "Neural2",
      "description": "Voz masculina neural de alta qualidade"
    }
  ]
}
```

### Informações do Serviço
```http
GET /api/v1/info
```

### Limpeza de Arquivos
```http
DELETE /api/v1/cleanup?max_age_hours=24
```

## 🔗 Integração com Gateway

O Voice Service é integrado ao Gateway Service para uso transparente:

```http
# Via Gateway (recomendado)
POST /api/voice/speak
Content-Type: application/json

{
  "text": "Texto para síntese",
  "voice": "pt-BR-Neural2-B"
}
```

## 🎵 Qualidade de Áudio

### Configurações de Áudio
- **Formato**: MP3
- **Taxa de Amostragem**: 24kHz
- **Bitrate**: 64kbps (otimizado para web)
- **Canais**: Mono

### Performance
- **Latência**: ~1-3 segundos para textos curtos
- **Qualidade**: Vozes neurais com naturalidade superior
- **Tamanho**: ~1MB por minuto de áudio

## 🔍 Monitoramento e Logs

### Logs Estruturados
```bash
# Visualizar logs em tempo real
docker logs empatia-voice-service-dev -f

# Filtrar por nível
docker logs empatia-voice-service-dev 2>&1 | grep "ERROR"
```

### Métricas Disponíveis
- Tempo de resposta da síntese
- Taxa de sucesso/erro
- Uso de diferentes vozes
- Tamanho dos arquivos gerados

## 🚨 Troubleshooting

### Problemas Comuns

1. **Credenciais não encontradas**
   ```bash
   # Verificar se o arquivo existe
   ls -la services/voice-service/credentials/
   
   # Verificar variável de ambiente
   docker exec empatia-voice-service-dev env | grep GOOGLE
   ```

2. **API não habilitada**
   ```bash
   # Verificar logs para erros de API
   docker logs empatia-voice-service-dev | grep "API"
   ```

3. **Arquivos não sendo servidos**
   ```bash
   # Verificar diretório de output
   docker exec empatia-voice-service-dev ls -la /app/output/
   ```

### Testes Manuais

```bash
# Testar síntese diretamente
curl -X POST http://localhost:8004/api/v1/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Teste de síntese de voz",
    "voice": "pt-BR-Neural2-A"
  }'

# Testar arquivo de áudio
curl -I http://localhost:8004/audio/nome_do_arquivo.mp3
```

## 🔧 Desenvolvimento

### Estrutura do Projeto
```
services/voice-service/
├── src/
│   ├── api/
│   │   └── voice_api.py          # Endpoints da API
│   ├── models/
│   │   └── voice_models.py       # Modelos Pydantic
│   ├── services/
│   │   └── f5_tts_service.py     # Serviço principal F5-TTS
│   └── main.py                   # Aplicação FastAPI
├── tests/
│   └── test_voice_service.py     # Testes unitários
├── Dockerfile                    # Container Docker
├── requirements.txt              # Dependências Python
└── README.md                     # Esta documentação
```

### Executar Testes
```bash
# Testes unitários
python -m pytest tests/ -v

# Teste de integração
python -m pytest tests/test_integration.py -v
```

### Contribuir
1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🤝 Suporte

Para suporte e dúvidas:
- Abra uma issue no GitHub
- Consulte os logs do serviço
- Verifique a documentação da API

---

**Desenvolvido com ❤️ para síntese de voz em português brasileiro** 