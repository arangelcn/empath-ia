# empatIA - Makefile para automação de desenvolvimento

.PHONY: help dev build deploy-dev deploy-prod test clean setup logs docs migrate cleanup mongo

# Cores para output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

# Configurações
PROJECT_NAME=empatia
DOCKER_COMPOSE_DEV=docker-compose.dev.yml
DOCKER_COMPOSE_PROD=config/docker-compose.prod.yml

help: ## Mostra esta ajuda
	@echo "${BLUE}=== empatIA - Comandos Disponíveis ===${NC}"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "${GREEN}%-20s${NC} %s\n", $$1, $$2}'

# ===== COMANDOS DE MIGRAÇÃO =====
migrate-project: ## Executa migração completa para microserviços
	@echo "${YELLOW}🚀 Executando migração para microserviços...${NC}"
	@chmod +x scripts/migrate.sh
	@./scripts/migrate.sh

cleanup: ## Executa limpeza final após migração
	@echo "${YELLOW}🧹 Executando limpeza final...${NC}"
	@chmod +x scripts/cleanup.sh
	@./scripts/cleanup.sh

validate: ## Valida estrutura após migração
	@echo "${YELLOW}🔍 Validando estrutura...${NC}"
	@chmod +x scripts/validate_migration.sh
	@./scripts/validate_migration.sh

# ===== CONFIGURAÇÃO E DESENVOLVIMENTO =====
setup: ## Configuração inicial do projeto
	@echo "${YELLOW}🔧 Configurando projeto...${NC}"
	@cp .env.example .env 2>/dev/null || echo "Arquivo .env já existe"
	@mkdir -p data/{shared,models,uploads,logs}
	@mkdir -p docs/{api,architecture,deployment,user-guide}
	@mkdir -p scripts
	@touch data/{shared,models,uploads,logs}/.gitkeep
	@echo "${GREEN}✅ Configuração inicial concluída!${NC}"
	@echo "${BLUE}📝 Edite o arquivo .env com suas configurações${NC}"
	@echo "${YELLOW}⚠️  IMPORTANTE: Configure as seguintes variáveis no .env:${NC}"
	@echo "${BLUE}   - OPENAI_API_KEY (obrigatório)${NC}"
	@echo "${BLUE}   - CREDENTIALS_JSON (para Google Cloud TTS)${NC}"
	@echo "${BLUE}   - DID_API_USERNAME/DID_API_PASSWORD (opcional, para avatar)${NC}"

dev: ## Inicia ambiente de desenvolvimento com hot reload
	@echo "${YELLOW}🚀 Iniciando ambiente de desenvolvimento com live reload...${NC}"
	@test -f .env || (echo "${RED}❌ Arquivo .env não encontrado. Execute 'make setup' primeiro.${NC}" && exit 1)
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

dev-detached: ## Inicia ambiente de desenvolvimento em background
	@echo "${YELLOW}🚀 Iniciando ambiente de desenvolvimento (background) com live reload...${NC}"
	@test -f .env || (echo "${RED}❌ Arquivo .env não encontrado. Execute 'make setup' primeiro.${NC}" && exit 1)
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

dev-services: ## Inicia apenas os serviços backend (sem web-ui)
	@echo "${YELLOW}🚀 Iniciando apenas serviços backend...${NC}"
	@test -f .env || (echo "${RED}❌ Arquivo .env não encontrado. Execute 'make setup' primeiro.${NC}" && exit 1)
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) up --build gateway ai-service avatar-service emotion-service mongodb redis

# ===== COMANDOS MONGODB =====
mongo-logs: ## Visualiza logs do MongoDB
	@echo "${BLUE}📋 Logs do MongoDB:${NC}"
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f mongodb

mongo-shell: ## Acessa shell do MongoDB
	@echo "${BLUE}🐚 Acessando shell do MongoDB...${NC}"
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml exec mongodb mongosh -u admin -p admin123 --authenticationDatabase admin empatia_db

mongo-express: ## Abre MongoDB Express no navegador
	@echo "${BLUE}🌐 Abrindo MongoDB Express...${NC}"
	@echo "MongoDB Express: http://localhost:8081"
	@echo "Usuário: admin | Senha: admin123"

mongo-backup: ## Cria backup do MongoDB
	@echo "${YELLOW}💾 Criando backup do MongoDB...${NC}"
	@mkdir -p ./data/backups
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml exec mongodb mongodump --uri="mongodb://admin:admin123@localhost:27017/empatia_db?authSource=admin" --out=/tmp/backup
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml exec mongodb tar -czf /tmp/mongodb-backup-$(shell date +%Y%m%d_%H%M%S).tar.gz -C /tmp/backup .
	@docker cp $$(docker compose -f docker-compose.yml -f docker-compose.dev.yml ps -q mongodb):/tmp/mongodb-backup-*.tar.gz ./data/backups/
	@echo "${GREEN}✅ Backup criado em ./data/backups/${NC}"

mongo-restore: ## Restaura backup do MongoDB (uso: make mongo-restore BACKUP=arquivo.tar.gz)
	@echo "${YELLOW}📥 Restaurando backup do MongoDB...${NC}"
	@test -n "$(BACKUP)" || (echo "${RED}❌ Especifique o arquivo: make mongo-restore BACKUP=arquivo.tar.gz${NC}" && exit 1)
	@docker cp ./data/backups/$(BACKUP) $$(docker compose -f docker-compose.yml -f docker-compose.dev.yml ps -q mongodb):/tmp/
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml exec mongodb tar -xzf /tmp/$(BACKUP) -C /tmp/
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml exec mongodb mongorestore --uri="mongodb://admin:admin123@localhost:27017/empatia_db?authSource=admin" --drop /tmp/empatia_db
	@echo "${GREEN}✅ Backup restaurado com sucesso!${NC}"

mongo-reset: ## Reseta completamente o banco MongoDB
	@echo "${RED}⚠️  ATENÇÃO: Isto vai apagar TODOS os dados do MongoDB!${NC}"
	@read -p "Tem certeza? Digite 'yes' para confirmar: " confirm && [ "$$confirm" = "yes" ] || (echo "Operação cancelada" && exit 1)
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml stop mongodb
	@docker volume rm empath-ia_mongodb_data_dev 2>/dev/null || true
	@docker volume rm empath-ia_mongodb_data 2>/dev/null || true
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d mongodb
	@echo "${GREEN}✅ MongoDB resetado com sucesso!${NC}"

# ===== BUILD E DEPLOY =====
build: ## Constrói todas as imagens Docker
	@echo "${YELLOW}🔨 Construindo imagens Docker...${NC}"
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) build

build-service: ## Constrói imagem de um serviço específico (ex: make build-service SERVICE=ai-service)
	@echo "${YELLOW}🔨 Construindo serviço $(SERVICE)...${NC}"
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) build $(SERVICE)

build-prod: ## Constrói imagens para produção
	@echo "${YELLOW}🔨 Construindo imagens para produção...${NC}"
	@docker compose -f $(DOCKER_COMPOSE_PROD) build

deploy-dev: build ## Deploy em ambiente de desenvolvimento
	@echo "${YELLOW}🚀 Fazendo deploy em desenvolvimento...${NC}"
	@test -f .env || (echo "${RED}❌ Arquivo .env não encontrado. Execute 'make setup' primeiro.${NC}" && exit 1)
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) up -d

deploy-prod: build-prod ## Deploy em ambiente de produção
	@echo "${YELLOW}🚀 Fazendo deploy em produção...${NC}"
	@test -f .env || (echo "${RED}❌ Arquivo .env não encontrado. Execute 'make setup' primeiro.${NC}" && exit 1)
	@docker compose -f $(DOCKER_COMPOSE_PROD) up -d

# ===== CONTROLE DE SERVIÇOS =====
stop: ## Para todos os serviços
	@echo "${YELLOW}⏹️ Parando serviços...${NC}"
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml down

stop-prod: ## Para serviços de produção
	@echo "${YELLOW}⏹️ Parando serviços de produção...${NC}"
	@docker compose -f $(DOCKER_COMPOSE_PROD) down

restart: stop dev ## Reinicia ambiente de desenvolvimento
	@echo "${GREEN}🔄 Ambiente reiniciado!${NC}"

restart-service: ## Reinicia um serviço específico (ex: make restart-service SERVICE=ai-service)
	@echo "${YELLOW}🔄 Reiniciando serviço $(SERVICE)...${NC}"
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml restart $(SERVICE)

# ===== LOGS E MONITORAMENTO =====
logs: ## Visualiza logs de todos os serviços
	@echo "${BLUE}📋 Logs dos serviços:${NC}"
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

logs-ai: ## Logs apenas do serviço de IA
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f ai-service

logs-avatar: ## Logs apenas do serviço de avatar
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f avatar-service

logs-emotion: ## Logs apenas do serviço de emoções
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f emotion-service

logs-gateway: ## Logs apenas do gateway
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f gateway

logs-ui: ## Logs apenas do web-ui
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f web-ui

ps: ## Lista status dos containers
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml ps

health: ## Verifica saúde de todos os serviços
	@echo "${BLUE}🏥 Verificando saúde dos serviços...${NC}"
	@curl -s http://localhost:8000/health | jq . || echo "${RED}Gateway não disponível${NC}"
	@curl -s http://localhost:8001/health | jq . || echo "${RED}AI Service não disponível${NC}"
	@curl -s http://localhost:8002/health | jq . || echo "${RED}Avatar Service não disponível${NC}"
	@curl -s http://localhost:8003/health | jq . || echo "${RED}Emotion Service não disponível${NC}"

monitor: ## Abre ferramentas de monitoramento
	@echo "${BLUE}📊 Ferramentas de monitoramento:${NC}"
	@echo " - Web UI: http://localhost:7860"
	@echo " - Admin Panel: http://localhost:3001"
	@echo " - Gateway API: http://localhost:8000/docs"
	@echo " - AI Service: http://localhost:8001/docs"
	@echo " - Avatar Service: http://localhost:8002/docs"
	@echo " - Emotion Service: http://localhost:8003/docs"
	@echo " - Voice Service: http://localhost:8004/docs"
	@echo " - MongoDB Express: http://localhost:8081"
	@echo " - Redis: localhost:6379"
	@echo " - PostgreSQL: localhost:5432"

# ===== CHAT E PERSISTÊNCIA =====
chat-test: ## Testa a API de chat
	@echo "${BLUE}🧪 Testando API de chat...${NC}"
	@curl -X POST http://localhost:8000/api/chat/send \
		-H "Content-Type: application/json" \
		-d '{"message": "Olá, como você está?", "session_id": "test_makefile"}' | jq .

chat-history: ## Visualiza histórico de uma sessão (uso: make chat-history SESSION=session_id)
	@echo "${BLUE}📜 Histórico da sessão $(SESSION)...${NC}"
	@curl -s http://localhost:8000/api/chat/history/$(SESSION) | jq .

chat-conversations: ## Lista conversas recentes
	@echo "${BLUE}💬 Conversas recentes...${NC}"
	@curl -s http://localhost:8000/api/chat/conversations | jq .

# ===== TESTES =====
test: ## Executa todos os testes
	@echo "${YELLOW}🧪 Executando testes...${NC}"
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec ai-service pytest tests/ || true
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec avatar-service pytest tests/ || true
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec emotion-service pytest tests/ || true
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec gateway pytest tests/ || true

test-service: ## Executa testes de um serviço específico (ex: make test-service SERVICE=ai-service)
	@echo "${YELLOW}🧪 Executando testes do $(SERVICE)...${NC}"
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec $(SERVICE) pytest tests/

test-integration: ## Executa testes de integração
	@echo "${YELLOW}🧪 Executando testes de integração...${NC}"
	@pytest tests/integration/

test-e2e: ## Executa testes end-to-end
	@echo "${YELLOW}🧪 Executando testes E2E...${NC}"
	@pytest tests/e2e/

# ===== QUALIDADE DE CÓDIGO =====
lint: ## Executa linting em todos os serviços
	@echo "${YELLOW}📝 Executando linting...${NC}"
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec ai-service flake8 src/ || true
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec avatar-service flake8 src/ || true
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec emotion-service flake8 src/ || true
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec gateway flake8 src/ || true

format: ## Formata código com black
	@echo "${YELLOW}🎨 Formatando código...${NC}"
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec ai-service black src/ || true
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec avatar-service black src/ || true
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec emotion-service black src/ || true
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec gateway black src/ || true

# ===== LIMPEZA =====
clean: ## Remove containers, volumes e imagens não utilizadas
	@echo "${YELLOW}🧹 Limpando containers e volumes...${NC}"
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) down -v --remove-orphans
	@docker system prune -f
	@echo "${GREEN}✅ Limpeza concluída!${NC}"

clean-all: ## Remove tudo incluindo imagens
	@echo "${RED}🧹 Limpeza completa (incluindo imagens)...${NC}"
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) down -v --remove-orphans --rmi all
	@docker system prune -af
	@echo "${GREEN}✅ Limpeza completa concluída!${NC}"

# ===== SHELLS E ACESSO =====
shell-ai: ## Acessa shell do serviço de IA
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec ai-service bash

shell-avatar: ## Acessa shell do serviço de avatar
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec avatar-service bash

shell-emotion: ## Acessa shell do serviço de emoções
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec emotion-service bash

shell-gateway: ## Acessa shell do gateway
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec gateway bash

shell-ui: ## Acessa shell do web-ui
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec web-ui bash

shell-mongo: ## Acessa shell do MongoDB
	@docker compose -f docker-compose.yml -f $(DOCKER_COMPOSE_DEV) exec mongodb bash

# ===== DOCUMENTAÇÃO =====
docs: ## Mostra URLs da documentação
	@echo "${YELLOW}📚 Documentação da API:${NC}"
	@echo "${BLUE}📖 Documentações disponíveis em:${NC}"
	@echo "  - Gateway API: http://localhost:8000/docs"
	@echo "  - AI Service: http://localhost:8001/docs"
	@echo "  - Avatar Service: http://localhost:8002/docs"
	@echo "  - Emotion Service: http://localhost:8003/docs"

# ===== UTILITÁRIOS =====
update-deps: ## Atualiza dependências
	@echo "${YELLOW}📦 Atualizando dependências...${NC}"
	@find services/ -name "requirements.txt" -exec pip-compile {} \;

security-scan: ## Executa scan de segurança
	@echo "${YELLOW}🔒 Executando scan de segurança...${NC}"
	@docker run --rm -v $(PWD):/app -w /app securecodewarrior/docker-image-scanner

env-create: ## Cria arquivo .env a partir do .env.example
	@echo "${YELLOW}📝 Criando arquivo .env...${NC}"
	@test -f .env.example || (echo "${RED}❌ Arquivo .env.example não encontrado${NC}" && exit 1)
	@test ! -f .env || (echo "${RED}❌ Arquivo .env já existe${NC}" && exit 1)
	@cp .env.example .env
	@echo "${GREEN}✅ Arquivo .env criado! Edite as variáveis conforme necessário.${NC}"

env-validate: ## Valida configurações do .env
	@echo "${YELLOW}🔍 Validando configurações do .env...${NC}"
	@test -f .env || (echo "${RED}❌ Arquivo .env não encontrado${NC}" && exit 1)
	@echo "${GREEN}✅ Arquivo .env encontrado${NC}"
	@echo "${BLUE}📋 Verificando variáveis obrigatórias:${NC}"
	@if grep -q "OPENAI_API_KEY=open_ia_api_key" .env; then \
		echo "${RED}⚠️  OPENAI_API_KEY não configurada${NC}"; \
	else \
		echo "${GREEN}✅ OPENAI_API_KEY configurada${NC}"; \
	fi
	@if grep -q "CREDENTIALS_JSON=path_to_credentials" .env; then \
		echo "${RED}⚠️  CREDENTIALS_JSON não configurada${NC}"; \
	else \
		echo "${GREEN}✅ CREDENTIALS_JSON configurada${NC}"; \
	fi
	@if grep -q "DID_API_USERNAME=seu_username_aqui" .env; then \
		echo "${YELLOW}⚠️  DID_API_USERNAME não configurada (opcional)${NC}"; \
	else \
		echo "${GREEN}✅ DID_API_USERNAME configurada${NC}"; \
	fi
	@echo "${BLUE}📋 Verificando arquivos de credenciais:${NC}"
	@if [ -f "services/voice-service/credentials/empathia-462921-deff8cdf0d47.json" ]; then \
		echo "${GREEN}✅ Arquivo de credenciais GCP encontrado${NC}"; \
	else \
		echo "${RED}⚠️  Arquivo de credenciais GCP não encontrado${NC}"; \
		echo "${BLUE}   Coloque o arquivo JSON em: services/voice-service/credentials/${NC}"; \
	fi
	@echo "${BLUE}📋 Verificando portas:${NC}"
	@echo " - Gateway: ${GATEWAY_PORT:-8000}"
	@echo " - Web UI: ${WEB_UI_PORT:-7860}"
	@echo " - Admin Panel: ${ADMIN_PANEL_PORT:-3001}"
	@echo "${GREEN}✅ Validação concluída${NC}"

# Default target
.DEFAULT_GOAL := help 