# Voice Service - F5-TTS Português Brasileiro

Serviço de síntese de voz (Text-to-Speech) usando o modelo F5-TTS otimizado para português brasileiro.

## 🎯 Características

- **Modelo**: F5-TTS-pt-br (firstpixel/F5-TTS-pt-br)
- **Idioma**: Português Brasileiro
- **Qualidade**: Alta fidelidade com síntese neural
- **Formato**: WAV (24kHz)
- **API**: RESTful com FastAPI
- **Treinamento**: +200 horas de áudio PT-BR (Common Voice + Facebook)

## 📝 Otimizações para Português Brasileiro

### ✅ Processamento de Texto Automático
- **Conversão de Números**: Números são automaticamente convertidos para palavras (`123` → `cento e vinte e três`)
- **Normalização**: Texto convertido para minúsculas conforme recomendação do modelo
- **Pontuação Inteligente**: Adição automática de vírgulas para pausas naturais
- **Caracteres Especiais**: Preservação de acentos e caracteres específicos do português

### 🎙️ Qualidade de Áudio
- **Áudio de Referência**: Usa arquivo de referência otimizado (5-9 segundos)
- **Texto Curto**: Processamento otimizado para linhas curtas de texto
- **Pausas Naturais**: Vírgulas adicionadas automaticamente após conjunções

## 🚀 Funcionalidades

### ✅ Implementado
- ✅ Síntese de texto em português brasileiro
- ✅ API REST completa
- ✅ Limpeza e normalização de texto para PT-BR
- ✅ Gerenciamento automático de arquivos
- ✅ Health checks
- ✅ Logs detalhados
- ✅ Suporte a Docker

### 🔄 Em Desenvolvimento
- 🔄 Múltiplas vozes
- 🔄 Controle de velocidade
- 🔄 Controle de tom
- 🔄 Arquivo de referência personalizado

## 📋 Pré-requisitos

- Docker e Docker Compose
- Python 3.9+ (para desenvolvimento local)
- CUDA (opcional, para aceleração GPU)

## 🛠️ Instalação

### Docker (Recomendado)

```bash
# Construir e iniciar o serviço
docker-compose up -d voice-service

# Verificar logs
docker logs empatia-voice-service-dev -f
```

### Desenvolvimento Local

```bash
cd services/voice-service

# Instalar dependências
pip install -r requirements.txt

# Executar o serviço
python -m uvicorn src.main:app --host 0.0.0.0 --port 8004 --reload
```

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Diretório de saída dos arquivos de áudio
F5_TTS_OUTPUT_DIR=/app/tts_output

# Configurações do modelo
F5_TTS_MODEL=firstpixel/F5-TTS-pt-br
F5_TTS_DEVICE=auto  # auto, cpu, cuda

# Configurações da API
API_HOST=0.0.0.0
API_PORT=8004
```

## 📚 API Endpoints

### Health Check
```http
GET /api/v1/health
```

**Resposta:**
```json
{
  "status": "healthy",
  "service": "voice-service",
  "timestamp": "2024-01-01T12:00:00",
  "model_info": {
    "model_name": "firstpixel/F5-TTS-pt-br",
    "device": "cpu",
    "model_loaded": true,
    "sample_rate": 24000,
    "output_dir": "/app/tts_output"
  }
}
```

### Síntese de Voz
```http
POST /api/v1/synthesize
Content-Type: application/json

{
  "text": "Olá! Este é um teste de síntese de voz em português brasileiro."
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Áudio sintetizado com F5-TTS",
  "audio_path": "/app/tts_output/f5tts_20240101_120000_abc123.wav",
  "filename": "f5tts_20240101_120000_abc123.wav",
  "audio_url": "/api/v1/audio/f5tts_20240101_120000_abc123.wav",
  "duration": 3.45,
  "text_length": 65
}
```

### Obter Arquivo de Áudio
```http
GET /api/v1/audio/{filename}
```

### Informações do Modelo
```http
GET /api/v1/model-info
```

### Listar Arquivos
```http
GET /api/v1/files
```

### Limpeza de Arquivos Antigos
```http
DELETE /api/v1/cleanup?max_age_hours=24
```

## 🎙️ Exemplos de Uso

### cURL

```bash
# Sintetizar texto
curl -X POST "http://localhost:8004/api/v1/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"text": "Olá! Como você está hoje?"}'

# Baixar áudio gerado
curl -O "http://localhost:8004/api/v1/audio/f5tts_20240101_120000_abc123.wav"
```

### Python

```python
import requests

# Sintetizar texto
response = requests.post(
    "http://localhost:8004/api/v1/synthesize",
    json={"text": "Bem-vindo ao sistema de síntese de voz!"}
)

if response.status_code == 200:
    data = response.json()
    audio_url = f"http://localhost:8004{data['audio_url']}"
    print(f"Áudio disponível em: {audio_url}")
```

### JavaScript

```javascript
// Sintetizar texto
const response = await fetch('http://localhost:8004/api/v1/synthesize', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: 'Esta é uma mensagem de teste em português brasileiro.'
  })
});

const data = await response.json();
console.log('Áudio gerado:', data.audio_url);
```

## 🔍 Monitoramento

### Logs
```bash
# Ver logs em tempo real
docker logs empatia-voice-service-dev -f

# Ver logs específicos
docker logs empatia-voice-service-dev | grep "F5-TTS"
```

### Health Check
```bash
# Verificar status do serviço
curl http://localhost:8004/api/v1/health
```

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Modelo não carrega
```bash
# Verificar logs de inicialização
docker logs empatia-voice-service-dev | grep -E "(Loading|Error|Failed)"

# Verificar espaço em disco
docker exec empatia-voice-service-dev df -h
```

#### 2. Áudio silencioso
- Verificar se o modelo F5-TTS-pt-br foi carregado corretamente
- Verificar logs para erros de síntese
- Testar com texto simples: "Olá, teste."

#### 3. Erro de memória
```bash
# Verificar uso de memória
docker stats empatia-voice-service-dev

# Ajustar recursos do container se necessário
```

#### 4. Arquivos não encontrados
```bash
# Verificar diretório de saída
docker exec empatia-voice-service-dev ls -la /app/tts_output/

# Verificar permissões
docker exec empatia-voice-service-dev ls -la /app/
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