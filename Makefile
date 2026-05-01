# empatIA - atalhos de desenvolvimento

SHELL := /bin/bash
.DEFAULT_GOAL := help

GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
RED := \033[0;31m
NC := \033[0m

COMPOSE_FILES := -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.host.yml
BRIDGE_FILES := -f docker-compose.yml -f docker-compose.dev.yml

COMPOSE := docker compose $(COMPOSE_FILES)
BRIDGE_COMPOSE := docker compose $(BRIDGE_FILES)

BACKEND_SERVICES := gateway ai-service avatar-service emotion-service voice-service
FRONTEND_SERVICES := web-ui admin-panel
CORE_SERVICES := mongodb redis $(BACKEND_SERVICES)

.PHONY: help setup env-check env-create env-validate dev up dev-d down restart ps build build-ai-local logs shell test lint format health urls clean reset mongo-shell mongo-reset bridge bridge-d services

help: ## Lista os comandos disponíveis
	@printf "$(BLUE)empatIA - comandos$(NC)\n"
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "$(GREEN)%-16s$(NC) %s\n", $$1, $$2}'

setup: ## Cria .env e pastas locais usadas pelo Docker
	@cp -n .env.example .env 2>/dev/null || true
	@mkdir -p data/{shared,models,uploads,logs,backups}
	@touch data/{shared,models,uploads,logs}/.gitkeep
	@echo "$(GREEN)Setup concluído.$(NC) Edite o .env antes de subir a stack."

env-check:
	@test -f .env || (echo "$(RED).env não encontrado. Rode: make setup$(NC)" && exit 1)

env-create: ## Cria .env a partir de .env.example
	@test -f .env.example || (echo "$(RED).env.example não encontrado$(NC)" && exit 1)
	@test ! -f .env || (echo "$(RED).env já existe$(NC)" && exit 1)
	@cp .env.example .env
	@echo "$(GREEN).env criado.$(NC)"

env-validate: env-check ## Valida o mínimo esperado no .env
	@grep -q '^OPENAI_API_KEY=' .env || (echo "$(RED)OPENAI_API_KEY ausente$(NC)" && exit 1)
	@grep -q '^CREDENTIALS_JSON=' .env || echo "$(YELLOW)CREDENTIALS_JSON ausente ou opcional no seu fluxo$(NC)"
	@echo "$(GREEN).env encontrado e validado.$(NC)"

dev: env-check ## Sobe a stack dev com host network
	@set -a; . ./.env; set +a; $(COMPOSE) up --build

up: dev ## Alias para dev

dev-d: env-check ## Sobe a stack dev em background
	@set -a; . ./.env; set +a; $(COMPOSE) up --build -d

services: env-check ## Sobe só backend, MongoDB e Redis
	@set -a; . ./.env; set +a; $(COMPOSE) up --build $(CORE_SERVICES)

bridge: env-check ## Sobe a stack usando Docker bridge
	@set -a; . ./.env; set +a; $(BRIDGE_COMPOSE) up --build

bridge-d: env-check ## Sobe a stack usando Docker bridge em background
	@set -a; . ./.env; set +a; $(BRIDGE_COMPOSE) up --build -d

down: ## Para e remove containers da stack dev
	@$(COMPOSE) down --remove-orphans

restart: down dev-d ## Reinicia a stack dev em background

ps: ## Mostra containers da stack
	@$(COMPOSE) ps

build: ## Build das imagens, ou SERVICE=nome para uma imagem
	@set -a; [ ! -f .env ] || . ./.env; set +a; $(COMPOSE) build $(SERVICE)

build-ai-local: ## Build do ai-service exigindo modelo local via HF_TOKEN
	@set -a; [ ! -f .env ] || . ./.env; set +a; \
	token="$${HF_TOKEN:-$${HUGGING_FACE_TOKEN:-$${HUGGIN_FACE_TOKEN:-}}}"; \
	test -n "$$token" || (echo "$(RED)Configure HF_TOKEN antes do build.$(NC)" && exit 1); \
	HF_TOKEN="$$token" ENABLE_LOCAL_LLM=true LOCAL_MODEL_DOWNLOAD_REQUIRED=true $(COMPOSE) build --no-cache ai-service

logs: ## Logs da stack, ou SERVICE=nome para um serviço
	@$(COMPOSE) logs -f $(SERVICE)

shell: ## Abre shell em um serviço: make shell SERVICE=ai-service
	@test -n "$(SERVICE)" || (echo "$(RED)Informe SERVICE. Ex.: make shell SERVICE=ai-service$(NC)" && exit 1)
	@$(COMPOSE) exec $(SERVICE) bash

test: ## Roda pytest nos backends, ou SERVICE=nome
	@if [ -n "$(SERVICE)" ]; then \
		$(COMPOSE) exec $(SERVICE) pytest tests/; \
	else \
		status=0; \
		for service in $(BACKEND_SERVICES); do \
			echo "$(BLUE)==> $$service$(NC)"; \
			$(COMPOSE) exec $$service pytest tests/ || status=$$?; \
		done; exit $$status; \
	fi

lint: ## Roda flake8 nos backends
	@status=0; for service in $(BACKEND_SERVICES); do \
		echo "$(BLUE)==> $$service$(NC)"; \
		$(COMPOSE) exec $$service flake8 src/ || status=$$?; \
	done; exit $$status

format: ## Roda black nos backends
	@status=0; for service in $(BACKEND_SERVICES); do \
		echo "$(BLUE)==> $$service$(NC)"; \
		$(COMPOSE) exec $$service black src/ || status=$$?; \
	done; exit $$status

health: ## Verifica endpoints /health locais
	@for port in 8000 8001 8002 8003 8004; do \
		printf ":%s " "$$port"; \
		curl -fsS "http://localhost:$$port/health" | jq . || true; \
	done

urls: ## Mostra URLs locais úteis
	@echo "Web UI:          http://localhost:7860"
	@echo "Admin Panel:    http://localhost:3001"
	@echo "Gateway API:    http://localhost:8000/docs"
	@echo "AI Service:     http://localhost:8001/docs"
	@echo "Avatar Service: http://localhost:8002/docs"
	@echo "Emotion API:    http://localhost:8003/docs"
	@echo "Voice API:      http://localhost:8004/docs"
	@echo "Mongo Express:  http://localhost:8081"

mongo-shell: ## Abre o shell do MongoDB
	@$(COMPOSE) exec mongodb mongosh -u admin -p admin123 --authenticationDatabase admin empatia_db

mongo-reset: ## Apaga volumes locais do MongoDB e recria o serviço
	@read -p "Isto apaga o MongoDB local. Digite 'yes' para continuar: " confirm; \
	test "$$confirm" = "yes"
	@$(COMPOSE) stop mongodb
	@docker volume rm empath-ia_mongodb_data_dev empath-ia_mongodb_data 2>/dev/null || true
	@$(COMPOSE) up -d mongodb

clean: ## Remove containers, volumes locais e órfãos
	@$(COMPOSE) down -v --remove-orphans

reset: clean dev-d ## Recria a stack local do zero
