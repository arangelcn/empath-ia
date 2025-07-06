# Empath.IA - Psicólogo Virtual com IA

Uma plataforma completa de terapia virtual baseada na abordagem humanística de Carl Rogers, integrando análise emocional em tempo real, síntese de voz avançada e interface conversacional intuitiva.

## 🎯 Visão Geral

Empath.IA é uma solução inovadora que combina inteligência artificial, processamento de linguagem natural e análise emocional para criar uma experiência terapêutica virtual personalizada. O sistema oferece:

- **Terapia Baseada em Carl Rogers**: IA treinada na abordagem centrada na pessoa
- **Análise Emocional em Tempo Real**: Detecção de emoções através de texto e expressões faciais
- **Síntese de Voz Neural**: Vozes naturais em português brasileiro via Google Cloud
- **Histórico Persistente**: Conversas mantidas entre sessões para continuidade terapêutica
- **Interface Responsiva**: Experiência otimizada para desktop, tablet e mobile
- **Personalização Completa**: Seleção de vozes e preferências individuais

## ✨ Funcionalidades Principais

### ✅ Implementado
- ✅ **Chat Terapêutico**: Conversas naturais com IA especializada em psicologia
- ✅ **Síntese de Voz Avançada**: Google Cloud Text-to-Speech com vozes neurais
- ✅ **Análise Emocional**: Detecção de emoções via texto e expressões faciais
- ✅ **Persistência de Dados**: Histórico completo de conversas no MongoDB
- ✅ **Seleção de Vozes**: Múltiplas opções de vozes em português brasileiro
- ✅ **Onboarding Personalizado**: Coleta de preferências e configuração inicial
- ✅ **Controles de Áudio**: Reprodução automática e manual de respostas
- ✅ **Interface Responsiva**: Design moderno com Tailwind CSS
- ✅ **Arquitetura de Microserviços**: Serviços especializados e escaláveis
- ✅ **Containerização**: Deploy completo com Docker e Docker Compose

### 🔄 Em Desenvolvimento
- 🔄 Avatar 3D animado com sincronização labial
- 🔄 Análise de sentimentos avançada
- 🔄 Relatórios de progresso terapêutico
- 🔄 Integração com calendário para sessões
- 🔄 Dashboard administrativo completo

## 🏗️ Arquitetura do Sistema

### Microserviços

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI        │    │  Admin Panel    │    │  Mobile App     │
│  (React/Vite)   │    │   (React)       │    │   (Future)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴───────────┐
                    │   Gateway Service       │
                    │   (FastAPI/Python)      │
                    │   - Orquestração        │
                    │   - Autenticação        │
                    │   - Rate Limiting       │
                    └─────────────┬───────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────┴────────┐    ┌──────────┴──────────┐    ┌─────────┴────────┐
│  AI Service    │    │  Emotion Service    │    │  Voice Service   │
│  (FastAPI)     │    │  (FastAPI)          │    │  (FastAPI)       │
│  - OpenAI GPT  │    │  - Análise Facial   │    │  - Google Cloud  │
│  - Carl Rogers │    │  - Análise Textual  │    │  - TTS Neural    │
│  - Contexto    │    │  - OpenFace         │    │  - Múltiplas     │
│  - Memória     │    │  - Transformers     │    │    Vozes PT-BR   │
└────────────────┘    └─────────────────────┘    └──────────────────┘
                                  │
                    ┌─────────────┴───────────┐
                    │   Avatar Service        │
                    │   (FastAPI/Python)      │
                    │   - Animação 3D         │
                    │   - Sincronização       │
                    │   - Expressões          │
                    └─────────────────────────┘
```

### Banco de Dados
```
┌─────────────────────────────────────────────────────────────┐
│                        MongoDB                              │
├─────────────────────────────────────────────────────────────┤
│  Collections:                                               │
│  • conversations (sessões, preferências, histórico)        │
│  • messages (mensagens, timestamps, emoções)               │
│  • users (perfis, configurações, progresso)                │
│  • emotions (análises, métricas, tendências)               │
│  • audio_cache (arquivos de áudio, otimização)             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Tecnologias Utilizadas

### Frontend
- **React 18** com Hooks e TypeScript
- **Vite** para build e desenvolvimento rápido
- **Tailwind CSS** para design system moderno
- **Lucide React** para ícones consistentes
- **Axios** para comunicação HTTP

### Backend
- **FastAPI** para APIs REST de alta performance
- **Python 3.11+** com async/await
- **OpenAI GPT-4** para inteligência artificial
- **Google Cloud Text-to-Speech** para síntese de voz
- **OpenFace** para análise de expressões faciais
- **Transformers** para processamento de linguagem natural

### Infraestrutura
- **MongoDB** para persistência de dados
- **Docker & Docker Compose** para containerização
- **Nginx** para proxy reverso e load balancing
- **Prometheus & Grafana** para monitoramento
- **Jaeger** para tracing distribuído

## 📦 Estrutura do Projeto

```
empath-ia/
├── apps/                          # Aplicações frontend
│   ├── web-ui/                   # Interface principal (React)
│   └── admin-panel/              # Painel administrativo
├── services/                      # Microserviços backend
│   ├── gateway-service/          # API Gateway e orquestração
│   ├── ai-service/               # Inteligência artificial
│   ├── emotion-service/          # Análise emocional
│   ├── voice-service/            # Síntese de voz
│   └── avatar-service/           # Avatar 3D (em desenvolvimento)
├── infrastructure/               # Configurações de infraestrutura
│   ├── docker/                   # Dockerfiles e configurações
│   ├── kubernetes/               # Manifests K8s
│   └── monitoring/               # Prometheus, Grafana, Jaeger
├── data/                         # Dados e modelos
│   ├── models/                   # Modelos de IA
│   ├── uploads/                  # Arquivos enviados
│   └── logs/                     # Logs do sistema
├── docs/                         # Documentação
│   ├── api/                      # Documentação das APIs
│   ├── architecture/             # Diagramas e arquitetura
│   └── deployment/               # Guias de deploy
└── scripts/                      # Scripts de automação
```

## 🛠️ Instalação e Configuração

### Pré-requisitos
- **Docker** 20.10+ e **Docker Compose** 2.0+
- **Node.js** 18+ (para desenvolvimento frontend)
- **Python** 3.11+ (para desenvolvimento backend)
- **Git** para controle de versão

### Configuração Rápida

1. **Clone o repositório**
   ```bash
   git clone https://github.com/seu-usuario/empath-ia.git
   cd empath-ia
   ```

2. **Configure as variáveis de ambiente**
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

3. **Inicie todos os serviços**
   ```bash
   docker compose up -d
   ```

4. **Acesse a aplicação**
   - Interface principal: http://localhost:3000
   - Painel admin: http://localhost:3001
   - API Gateway: http://localhost:8000
   - Documentação API: http://localhost:8000/docs

### Configuração de Desenvolvimento

Para desenvolvimento com hot reload:

```bash
# Inicie apenas os serviços de infraestrutura
docker compose up -d mongodb

# Execute os serviços em modo desenvolvimento
make dev-all

# Ou execute serviços individuais
make dev-frontend    # Web UI
make dev-gateway     # Gateway Service
make dev-ai          # AI Service
make dev-emotion     # Emotion Service
make dev-voice       # Voice Service
```

## 🔧 Configuração de Serviços

### Google Cloud Text-to-Speech

1. **Crie um projeto no Google Cloud Console**
2. **Ative a API Text-to-Speech**
3. **Crie uma Service Account e baixe o JSON**
4. **Configure as credenciais**:
   ```bash
   # Coloque o arquivo JSON em services/voice-service/credentials/
   cp sua-service-account.json services/voice-service/credentials/google-cloud-key.json
   ```

### OpenAI API

Configure sua chave da OpenAI no arquivo `.env`:
```bash
OPENAI_API_KEY=sk-sua-chave-aqui
```

### MongoDB

O MongoDB é configurado automaticamente via Docker. Para configuração personalizada:
```bash
MONGODB_URI=mongodb://localhost:27017/empath_ia
MONGODB_DATABASE=empath_ia
```

## 📚 Documentação das APIs

### Gateway Service (Porta 8000)
- **POST** `/api/chat/send` - Enviar mensagem
- **GET** `/api/chat/history/{session_id}` - Buscar histórico
- **GET** `/api/user/status/{session_id}` - Status do usuário
- **POST** `/api/user/preferences` - Salvar preferências

### Voice Service (Porta 8004)
- **POST** `/api/voice/synthesize` - Sintetizar áudio
- **GET** `/api/voice/voices` - Listar vozes disponíveis
- **GET** `/health` - Status do serviço

### Emotion Service (Porta 8003)
- **POST** `/api/emotion/analyze-text` - Análise textual
- **POST** `/api/emotion/analyze-face` - Análise facial
- **GET** `/api/emotion/history/{session_id}` - Histórico emocional

### AI Service (Porta 8002)
- **POST** `/api/ai/chat` - Conversa com IA
- **GET** `/api/ai/context/{session_id}` - Contexto da sessão
- **POST** `/api/ai/reset-context` - Resetar contexto

## 🎨 Vozes Disponíveis

### Vozes Neurais (Recomendadas)
- **pt-BR-Neural2-A** - Voz feminina natural
- **pt-BR-Neural2-B** - Voz masculina natural
- **pt-BR-Neural2-C** - Voz feminina expressiva

### Vozes WaveNet
- **pt-BR-Wavenet-A** - Voz feminina de alta qualidade
- **pt-BR-Wavenet-B** - Voz masculina de alta qualidade
- **pt-BR-Wavenet-C** - Voz feminina alternativa

### Vozes Standard
- **pt-BR-Standard-A** - Voz feminina padrão
- **pt-BR-Standard-B** - Voz masculina padrão

## 🧪 Testes

### Executar todos os testes
```bash
make test-all
```

### Testes por serviço
```bash
make test-gateway    # Gateway Service
make test-ai         # AI Service
make test-emotion    # Emotion Service
make test-voice      # Voice Service
```

### Testes E2E
```bash
make test-e2e
```

## 📊 Monitoramento

### Métricas (Prometheus)
- http://localhost:9090

### Dashboards (Grafana)
- http://localhost:3001
- Usuário: admin / Senha: admin

### Tracing (Jaeger)
- http://localhost:16686

## 🚀 Deploy em Produção

### Docker Compose (Recomendado para desenvolvimento)
```bash
docker compose -f docker-compose.prod.yml up -d
```

### Kubernetes
```bash
# Aplicar manifests
kubectl apply -f infrastructure/kubernetes/manifests/

# Ou usar Helm
helm install empath-ia infrastructure/kubernetes/helm/
```

## 🔒 Segurança

- **Rate Limiting**: Proteção contra spam e ataques
- **CORS**: Configuração adequada para produção
- **Sanitização**: Limpeza de inputs do usuário
- **Logs**: Auditoria completa de ações
- **Secrets**: Gerenciamento seguro de credenciais

## 🤝 Contribuição

1. **Fork** o projeto
2. **Crie** uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. **Abra** um Pull Request

### Padrões de Código
- **Python**: PEP 8, Black, isort
- **JavaScript/TypeScript**: ESLint, Prettier
- **Commits**: Conventional Commits

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/empath-ia/issues)
- **Discussões**: [GitHub Discussions](https://github.com/seu-usuario/empath-ia/discussions)
- **Email**: suporte@empath-ia.com

## 🙏 Agradecimentos

- **Carl Rogers** - Inspiração para a abordagem terapêutica
- **OpenAI** - Tecnologia de IA conversacional
- **Google Cloud** - Síntese de voz de alta qualidade
- **Comunidade Open Source** - Ferramentas e bibliotecas utilizadas

---

**Empath.IA** - Transformando o cuidado mental através da tecnologia 💙
