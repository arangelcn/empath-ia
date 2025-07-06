# EmpathIA AI Service

Serviço de Inteligência Artificial para conversas terapêuticas do EmpathIA, integrando OpenAI GPT para respostas personalizadas e contextualizadas.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Funcionalidades](#funcionalidades)
- [Configuração](#configuração)
- [API Endpoints](#api-endpoints)
- [Integração OpenAI](#integração-openai)
- [Desenvolvimento](#desenvolvimento)
- [Deploy](#deploy)
- [Monitoramento](#monitoramento)

## 🎯 Visão Geral

O AI Service é o componente central de inteligência artificial do EmpathIA, responsável por:

- Processar mensagens dos usuários
- Gerar respostas terapêuticas contextualizadas
- Integrar com OpenAI GPT para conversas avançadas
- Manter contexto de conversas
- Analisar sentimentos e emoções

## 🏗️ Arquitetura

```
AI Service
├── FastAPI (Framework Web)
├── OpenAI Integration
├── Therapeutic Response Engine
├── Emotion Analysis
└── Conversation Context Management
```

### Componentes Principais

- **FastAPI**: Framework web para APIs REST
- **OpenAI Client**: Integração com GPT-4/GPT-3.5
- **Response Engine**: Lógica para respostas terapêuticas
- **Context Manager**: Gerenciamento de contexto de conversas
- **Emotion Analyzer**: Análise de sentimentos

## 🚀 Funcionalidades

### ✅ Implementadas

- [x] **Respostas Terapêuticas Básicas**: Padrões de reconhecimento para saudações, tristeza, ansiedade, raiva
- [x] **Health Check**: Endpoint de status do serviço
- [x] **Configuração Flexível**: Variáveis de ambiente para personalização
- [x] **CORS**: Suporte a requisições cross-origin
- [x] **Logging**: Sistema de logs estruturado
- [x] **Integração OpenAI**: Conexão com GPT-4/GPT-3.5
- [x] **Sistema de Fallback**: Respostas básicas quando OpenAI não está disponível
- [x] **Contexto de Conversa**: Histórico otimizado com compressão inteligente
- [x] **Otimização de Tokens**: Limitação e compressão de contexto
- [x] **Prompt Terapêutico**: Sistema de prompts para psicólogo Rogers

### 🔄 Em Desenvolvimento

- [ ] **Análise de Emoções**: Detecção automática de sentimentos
- [ ] **Respostas Personalizadas**: Baseadas no perfil do usuário
- [ ] **Cache Inteligente**: Respostas em cache para performance
- [ ] **Métricas Avançadas**: Monitoramento de uso de tokens
- [ ] **Testes Automatizados**: Suíte completa de testes

### 📋 Planejadas

- [ ] **Fine-tuning**: Modelos customizados para terapia
- [ ] **Multilíngue**: Suporte a múltiplos idiomas
- [ ] **Análise Avançada**: Sentiment analysis com ML
- [ ] **Cache Inteligente**: Respostas em cache para performance
- [ ] **A/B Testing**: Testes de diferentes abordagens

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4o  # ou gpt-3.5-turbo
MAX_TOKENS=1000
TEMPERATURE=0.7

# Service Configuration
AI_SERVICE_PORT=8001
DEBUG=false
LOG_LEVEL=INFO

# Context Optimization
MAX_HISTORY_MESSAGES=6      # Máximo mensagens no histórico
MAX_CONTEXT_TOKENS=2000     # Máximo tokens de contexto
ENABLE_CONTEXT_COMPRESSION=true  # Comprimir conversas longas
```

### Instalação Local

```bash
# 1. Clone o repositório
git clone <repository-url>
cd services/ai-service

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# 4. Execute o serviço
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

### Docker

```bash
# Build da imagem
docker build -t empath-ia-ai-service .

# Execução
docker run -p 8001:8001 \
  -e OPENAI_API_KEY=your_key \
  -e MODEL_NAME=gpt-4o \
  empath-ia-ai-service
```

## 🔌 API Endpoints

### Health Check
```http
GET /health
```

**Resposta:**
```json
{
  "status": "healthy",
  "service": "ai-service",
  "timestamp": "2025-07-05T17:45:18.694927",
  "version": "1.0.0"
}
```

### Chat
```http
POST /chat
```

**Request:**
```json
{
  "message": "Olá, como você está?",
  "session_id": "user-session-123"
}
```

**Resposta:**
```json
{
  "response": "Olá! Sou o Dr. Rogers, seu psicólogo virtual...",
  "service": "ai-service",
  "status": "active",
  "session_id": "user-session-123",
  "timestamp": "2025-07-05T17:45:18.694927",
  "provider": "openai",
  "model": "gpt-3.5-turbo"
}
```

### Configuração
```http
GET /config
```

**Resposta:**
```json
{
  "openai_configured": true,
  "model": "gpt-3.5-turbo",
  "service_port": "8001",
  "debug": false,
  "provider": "openai",
  "context_optimization": {
    "max_history_messages": 6,
    "max_context_tokens": 2000,
    "enable_compression": true
  }
}
```

## 🤖 Integração OpenAI

### Configuração

1. **Obtenha uma API Key**:
   - Acesse [OpenAI Platform](https://platform.openai.com/)
   - Crie uma conta e gere uma API Key

2. **Configure a variável de ambiente**:
   ```bash
   export OPENAI_API_KEY=sk-your-api-key-here
   ```

3. **Escolha o modelo**:
   ```bash
   export MODEL_NAME=gpt-4o  # ou gpt-3.5-turbo
   ```

### Funcionalidades

#### ✅ **Prompt Terapêutico**
- Sistema de prompts especializado para psicólogo Rogers
- Tom empático e profissional
- Respostas em português brasileiro
- Foco em bem-estar mental

#### ✅ **Otimização de Contexto**
- **Limitação de mensagens**: Máximo 6 mensagens no histórico
- **Compressão inteligente**: Para conversas longas
- **Estimativa de tokens**: Monitoramento de uso
- **Economia de custos**: ~50% redução em tokens

#### ✅ **Sistema de Fallback**
- Respostas básicas quando OpenAI indisponível
- Padrões de reconhecimento para situações comuns
- Transição transparente entre OpenAI e fallback

### Exemplo de Uso

```python
from src.services.openai_service import OpenAIService

# Inicializar serviço
service = OpenAIService()

# Gerar resposta com contexto
response = await service.generate_therapeutic_response(
    user_message="Estou muito ansioso",
    session_id="user-123",
    conversation_history=[
        {"type": "user", "content": "Olá"},
        {"type": "assistant", "content": "Olá! Como posso te ajudar?"}
    ]
)
```
```

### Otimização de Tokens

#### 📊 **Estratégias Implementadas**

1. **Limitação de Mensagens**: Máximo 6 mensagens no histórico
2. **Compressão de Contexto**: Para conversas longas
3. **Estimativa de Tokens**: Monitoramento em tempo real
4. **Configuração Flexível**: Via variáveis de ambiente

#### 💰 **Economia de Custos**

- **Antes**: ~400-600 tokens por contexto
- **Depois**: ~200-300 tokens por contexto
- **Economia**: ~50% redução em tokens

#### ⚙️ **Configurações**

```bash
# Limitar histórico
MAX_HISTORY_MESSAGES=6

# Máximo tokens de contexto
MAX_CONTEXT_TOKENS=2000

# Habilitar compressão
ENABLE_CONTEXT_COMPRESSION=true
```

## 🛠️ Desenvolvimento

### Estrutura do Projeto

```
services/ai-service/
├── src/
│   ├── main.py              # Aplicação FastAPI
│   │   ├── services/
│   │   │   ├── openai_service.py    # Integração OpenAI
│   │   │   ├── therapeutic_engine.py # Lógica terapêutica
│   │   │   └── emotion_analyzer.py   # Análise de emoções
│   │   ├── models/
│   │   │   ├── chat.py              # Modelos de dados
│   │   │   └── responses.py          # Estruturas de resposta
│   │   └── utils/
│   │       ├── prompts.py            # Templates de prompts
│   │       └── validators.py         # Validação de dados
│   ├── tests/
│   │   ├── test_openai.py
│   │   ├── test_therapeutic.py
│   │   └── test_integration.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
```

### Executando Testes

```bash
# Instalar dependências de teste
pip install pytest pytest-asyncio

# Executar testes
pytest tests/

# Com coverage
pytest --cov=src tests/

# Testar integração OpenAI
python test_openai.py
```

### Testes de Integração

```bash
# Testar configuração OpenAI
curl http://localhost:8001/config

# Testar chat com contexto
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Estou ansioso",
    "session_id": "test-123",
    "conversation_history": [
      {"type": "user", "content": "Olá"},
      {"type": "assistant", "content": "Olá! Como posso ajudar?"}
    ]
  }'

# Testar fallback (sem API key)
export OPENAI_API_KEY=""
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Teste fallback"}'
```

### Logs

```bash
# Ver logs em tempo real
docker logs -f empath-ia-ai-service-1

# Filtrar por nível
docker logs empath-ia-ai-service-1 | grep "ERROR"
```

## 🚀 Deploy

### Docker Compose

```yaml
# docker-compose.yml
ai-service:
  build: ./services/ai-service
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - MODEL_NAME=${MODEL_NAME:-gpt-4o}
    - AI_SERVICE_PORT=8001
  ports:
    - "8001:8001"
  networks:
    - empathia-network
```

### Kubernetes

```yaml
# k8s/ai-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-service
  template:
    metadata:
      labels:
        app: ai-service
    spec:
      containers:
      - name: ai-service
        image: empath-ia-ai-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
```

## 📊 Monitoramento

### Métricas Importantes

- **Latência de Resposta**: Tempo médio de resposta da OpenAI
- **Taxa de Erro**: Erro rate das chamadas para OpenAI
- **Uso de Tokens**: Consumo de tokens por sessão
- **Qualidade de Resposta**: Feedback dos usuários
- **Economia de Tokens**: Redução de custos com otimização
- **Contexto Eficiência**: Taxa de compressão de contexto

### Health Checks

```bash
# Verificar status
curl http://localhost:8001/health

# Verificar configuração
curl http://localhost:8001/config
```

### Alertas

- API Key expirada ou inválida
- Latência alta (>5s)
- Taxa de erro >5%
- Quota OpenAI esgotada
- Uso excessivo de tokens (>2000 por sessão)
- Falha no sistema de fallback

## 🔒 Segurança

### Boas Práticas

- ✅ **API Keys**: Nunca commitar chaves no código
- ✅ **Rate Limiting**: Implementar limites de requisição
- ✅ **Validação**: Validar todas as entradas
- ✅ **Logs**: Não logar dados sensíveis
- ✅ **HTTPS**: Usar sempre em produção

## 🐛 Troubleshooting

### Problemas Comuns

#### **OpenAI não configurado**
```bash
# Verificar variável de ambiente
echo $OPENAI_API_KEY

# Verificar logs
docker logs empath-ia-ai-service-1 | grep "OpenAI"
```

#### **Erro de rate limit**
```bash
# Aguardar alguns minutos
# Verificar uso da API no dashboard OpenAI
```

#### **Contexto muito longo**
```bash
# Ajustar configurações
export MAX_HISTORY_MESSAGES=4
export ENABLE_CONTEXT_COMPRESSION=true
```

#### **Fallback não funcionando**
```bash
# Verificar logs de erro
docker logs empath-ia-ai-service-1 | grep "fallback"
```

### Configurações de Segurança

```python
# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, message: dict):
    # Implementation
```

## 🤝 Contribuição

### Como Contribuir

1. **Fork** o repositório
2. **Crie** uma branch para sua feature
3. **Implemente** suas mudanças
4. **Adicione** testes
5. **Documente** suas alterações
6. **Abra** um Pull Request

### Padrões de Código

- **Python**: PEP 8
- **Type Hints**: Sempre usar
- **Docstrings**: Documentar funções
- **Tests**: Cobertura mínima de 80%

## 📞 Suporte

### Contatos

- **Issues**: [GitHub Issues](https://github.com/empath-ia/ai-service/issues)
- **Documentação**: [Wiki](https://github.com/empath-ia/ai-service/wiki)
- **Email**: ai-service@empath-ia.com

### Troubleshooting

#### Problemas Comuns

1. **API Key inválida**:
   ```bash
   curl -X POST http://localhost:8001/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "test"}'
   ```

2. **Timeout na OpenAI**:
   - Verificar conectividade
   - Aumentar timeout
   - Implementar retry logic

3. **Erro de modelo**:
   - Verificar se o modelo existe
   - Confirmar permissões da API Key

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

**Desenvolvido com ❤️ pela equipe EmpathIA** 