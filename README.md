# 🧠 empatIA - Psicólogo Virtual com Avatar

Um assistente de psicologia virtual empático baseado em Carl Rogers, construído com arquitetura de microsserviços, avatar animado usando IA e análise de expressões faciais.

## ✨ Funcionalidades Principais

- 💬 **Chat Inteligente**: Conversas empáticas baseadas em Carl Rogers com persistência MongoDB
- 🎭 **Avatar Animado**: Vídeos gerados com D-ID AI integrados ao chat
- 😊 **Análise Facial**: Detecção de expressões e emoções com OpenFace 2.0
- 🔄 **Hot Reload**: Desenvolvimento com atualização automática via Docker Compose Watch
- 🏗️ **Microsserviços**: Arquitetura modular e escalável
- 📊 **Monitoramento**: Ferramentas integradas para logs e saúde dos serviços
- 🐳 **Docker**: Ambiente completamente containerizado

## 🏗️ Arquitetura de Microsserviços

O projeto está organizado em microsserviços independentes:

- **Gateway Service** (`:8000`) - API principal e orquestração
- **AI Service** (`:8001`) - Integração OpenAI e lógica do psicólogo virtual
- **Avatar Service** (`:8002`) - Geração de vídeos com D-ID AI
- **Emotion Service** (`:8003`) - Análise facial com OpenFace
- **Web UI** (`:3000`) - Interface React com Vite
- **MongoDB** (`:27017`) - Persistência de conversas e sessões
- **Redis** (`:6379`) - Cache e sessões
- **PostgreSQL** (`:5432`) - Banco opcional para dados estruturados

## 🚀 Início Rápido

### 1. Pré-requisitos
- Docker e Docker Compose
- Git

### 2. Clone e configuração inicial
```bash
git clone <seu-repo>
cd empath-ia
make setup  # Cria estrutura de diretórios e .env
```

### 3. Configure as variáveis de ambiente
Edite o arquivo `.env` criado:

```env
# APIs Obrigatórias
OPENAI_API_KEY=sua_chave_openai_aqui
DID_API_USERNAME=seu_username_did
DID_API_PASSWORD=sua_senha_did

# MongoDB (padrões funcionam para desenvolvimento)
MONGODB_URL=mongodb://admin:admin123@mongodb:27017/empatia_db?authSource=admin
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=admin123

# URLs dos serviços (configuração automática)
AI_SERVICE_URL=http://ai-service:8001
AVATAR_SERVICE_URL=http://avatar-service:8002
EMOTION_SERVICE_URL=http://emotion-service:8003
```

**Como obter as chaves:**
- **OpenAI**: https://platform.openai.com/api-keys
- **D-ID**: https://www.d-id.com/ → Account Settings → API Key

### 4. Execute o projeto
```bash
# Desenvolvimento com hot reload
make dev

# Em background
make dev-detached

# Apenas serviços backend
make dev-services
```

### 5. Acesse a aplicação
- **Web UI**: http://localhost:3000
- **API Gateway**: http://localhost:8000/docs
- **MongoDB Express**: http://localhost:8081 (admin/admin123)

## 🛠️ Comandos de Desenvolvimento

O projeto inclui um Makefile completo para automação:

### Comandos Principais
```bash
make help          # Lista todos os comandos disponíveis
make setup         # Configuração inicial
make dev           # Inicia desenvolvimento
make stop          # Para todos os serviços
make restart       # Reinicia ambiente
make build         # Constrói imagens Docker
```

### Logs e Monitoramento
```bash
make logs          # Logs de todos os serviços
make logs-ai       # Logs apenas do AI Service
make logs-gateway  # Logs apenas do Gateway
make health        # Verifica saúde dos serviços
make monitor       # Mostra URLs de monitoramento
```

### MongoDB
```bash
make mongo-shell   # Acessa shell do MongoDB
make mongo-logs    # Visualiza logs do MongoDB
make mongo-backup  # Cria backup
make mongo-restore BACKUP=arquivo.tar.gz  # Restaura backup
make mongo-reset   # Reseta banco (cuidado!)
```

### Testes da API
```bash
make chat-test                    # Testa API de chat
make chat-history SESSION=id     # Histórico de sessão
make chat-conversations          # Lista conversas
```

## 📁 Estrutura do Projeto

```
empath-ia/
├── apps/
│   └── web-ui/                  # Frontend React + Vite
│       ├── src/
│       │   ├── components/      # Componentes React
│       │   └── services/        # Integração com APIs
│       └── Dockerfile
├── services/                    # Microsserviços
│   ├── gateway-service/         # API Gateway (:8000)
│   ├── ai-service/             # OpenAI Integration (:8001)
│   ├── avatar-service/         # D-ID AI Videos (:8002)
│   └── emotion-service/        # OpenFace Analysis (:8003)
├── infrastructure/
│   ├── docker/                 # Dockerfiles personalizados
│   ├── kubernetes/             # Deploy K8s (preparado)
│   └── monitoring/             # Grafana, Prometheus, Jaeger
├── data/
│   ├── shared/                 # Volume compartilhado
│   ├── uploads/                # Uploads de arquivos
│   ├── models/                 # Modelos ML
│   └── logs/                   # Logs persistentes
├── scripts/                    # Scripts de automação
│   ├── init-db.js             # Inicialização MongoDB
│   ├── cleanup.sh             # Limpeza do projeto
│   └── migrate.sh             # Migração de dados
├── config/                     # Configurações
├── docs/                       # Documentação
├── tests/                      # Testes E2E e integração
├── docker-compose.yml          # Produção
├── docker-compose.dev.yml      # Desenvolvimento
└── Makefile                    # Automação
```

## 🎯 APIs e Endpoints

### Gateway Service (:8000)
```http
# Chat principal
POST /api/chat/send
GET /api/chat/history/{session_id}
GET /api/chat/conversations

# Orquestração de serviços
POST /api/analyze/emotion      # Análise facial
POST /api/avatar/generate      # Geração de avatar
GET /health                    # Status do sistema
```

### Exemplo de uso da API
```bash
# Enviar mensagem
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Estou me sentindo ansioso hoje...",
    "session_id": "session_123"
  }'

# Ver histórico
curl http://localhost:8000/api/chat/history/session_123
```

## 🔬 Análise de Expressões Faciais

### Configuração OpenFace
```bash
# Construir container OpenFace (primeira vez)
docker compose build openface

# Executar análise facial
docker compose run --rm openface

# Via API
curl -X POST http://localhost:8000/api/analyze/emotion \
  -F "file=@foto.jpg"
```

### Resposta da análise facial
```json
{
  "success": true,
  "facial_analysis": {
    "face_detected": true,
    "confidence": 0.95
  },
  "action_units": {
    "AU01": {"intensity": 0.2, "present": false},
    "AU12": {"intensity": 1.8, "present": true}
  },
  "emotional_interpretation": {
    "joy": 0.85,
    "sadness": 0.0,
    "anger": 0.0,
    "surprise": 0.1,
    "fear": 0.0,
    "disgust": 0.0
  },
  "dominant_emotion": "joy"
}
```

## 🚀 Deploy e Produção

### Desenvolvimento
```bash
make dev           # Hot reload ativo
make dev-detached  # Background
```

### Produção
```bash
make build-prod    # Build para produção
make deploy-prod   # Deploy produção
```

### Kubernetes (preparado)
```bash
# Manifests disponíveis em infrastructure/kubernetes/
kubectl apply -f infrastructure/kubernetes/manifests/
```

## 📊 Monitoramento e Observabilidade

### Ferramentas Integradas
- **Logs**: Docker Compose logs com rotação
- **Métricas**: Preparado para Prometheus
- **Tracing**: Jaeger configurado
- **Dashboards**: Grafana templates

### Acesso às ferramentas
```bash
make monitor  # Lista todas as URLs
```

## 🔧 Desenvolvimento Avançado

### Hot Reload
O projeto usa Docker Compose Watch para hot reload automático:
- Alterações em código Python são sincronizadas automaticamente
- FastAPI recarrega automaticamente com mudanças
- React/Vite detecta mudanças via Vite HMR

### Testes
```bash
make test              # Todos os testes
pytest services/*/tests/  # Testes específicos
```

### Logs estruturados
```bash
make logs              # Todos os serviços
make logs-gateway      # Gateway específico
docker compose logs -f mongodb  # Logs MongoDB
```

## ⚠️ Troubleshooting

### Avatar não aparece
1. **Verifique credenciais D-ID no `.env`**
2. **Logs**: `make logs-avatar`
3. **Teste isolado**: `curl http://localhost:8002/health`

### MongoDB não conecta
1. **Verifique se está rodando**: `make mongo-logs`
2. **Acesse shell**: `make mongo-shell`
3. **Reset se necessário**: `make mongo-reset`

### OpenFace não funciona
1. **Build primeiro**: `docker compose build openface`
2. **Teste isolado**: `make logs-emotion`
3. **Verifique imagem**: Use fotos claras e bem iluminadas

### Limpeza completa
```bash
make stop
docker system prune -f
make dev
```

### Rede Docker com conflitos
```bash
docker network prune -f
docker volume prune -f
make dev
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'Adiciona nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob licença MIT. Veja `LICENSE` para mais detalhes.

## 🆘 Suporte

- **Issues**: Use GitHub Issues para bugs e sugestões
- **Documentação**: Verifique a pasta `docs/`
- **Chat**: Teste o próprio sistema! 😊

---

**Desenvolvido com ❤️ usando arquitetura de microsserviços, Docker e as melhores práticas de desenvolvimento moderno.**
