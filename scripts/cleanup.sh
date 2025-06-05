#!/bin/bash
set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Limpeza final após migração para microserviços...${NC}"

# Arquivos e diretórios a serem removidos
DEPRECATED_FILES=(
    ".env.example.bak"
    ".env.example.original"
    "shared_data"
    "migration-backup"
    "install_openface.sh"
    "dev.sh"
    "backend"
    "frontend"
    "openface"
    "OpenFace"
)

# Função para remover arquivos/diretórios
cleanup_files() {
    echo -e "${YELLOW}🗑️  Removendo arquivos desnecessários...${NC}"
    
    for item in "${DEPRECATED_FILES[@]}"; do
        if [[ -e "$item" ]]; then
            rm -rf "$item"
            echo -e "  ${GREEN}✅ Removido: $item${NC}"
        else
            echo -e "  ${YELLOW}⚠️  Não encontrado: $item${NC}"
        fi
    done
}

# Função para limpar cache Docker
cleanup_docker() {
    echo -e "${YELLOW}🐳 Limpando cache Docker...${NC}"
    
    # Remover containers antigos
    docker container prune -f 2>/dev/null || true
    
    # Remover imagens antigas
    docker image prune -f 2>/dev/null || true
    
    # Remover volumes órfãos
    docker volume prune -f 2>/dev/null || true
    
    echo -e "  ${GREEN}✅ Cache Docker limpo${NC}"
}

# Função para limpar cache Python
cleanup_python() {
    echo -e "${YELLOW}🐍 Limpando cache Python...${NC}"
    
    # Encontrar e remover __pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # Encontrar e remover .pyc
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Encontrar e remover .pyo
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    
    echo -e "  ${GREEN}✅ Cache Python limpo${NC}"
}

# Função para validar estrutura final
validate_structure() {
    echo -e "${YELLOW}🔍 Validando estrutura final...${NC}"
    
    local required_dirs=(
        "services/ai-service"
        "services/avatar-service"
        "services/emotion-service"
        "services/gateway-service"
        "apps/web-ui"
        "data/shared"
        "infrastructure/docker"
    )
    
    local errors=0
    
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            echo -e "  ${GREEN}✅ $dir${NC}"
        else
            echo -e "  ${RED}❌ $dir - FALTANDO${NC}"
            ((errors++))
        fi
    done
    
    if [[ $errors -eq 0 ]]; then
        echo -e "${GREEN}✅ Estrutura validada com sucesso!${NC}"
    else
        echo -e "${RED}❌ Encontrados $errors erros na estrutura${NC}"
    fi
}

# Função principal
main() {
    # Execução automática em ambiente Docker
    if [[ "${DOCKER_ENV:-}" == "true" ]]; then
        echo -e "${BLUE}🧹 Executando limpeza automática em ambiente Docker...${NC}"
    else
        echo -e "${BLUE}Deseja executar a limpeza completa? (y/N)${NC}"
        read -r response
        
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Limpeza cancelada.${NC}"
            exit 0
        fi
    fi
    
    cleanup_files
    cleanup_docker
    cleanup_python
    validate_structure
    
    echo -e "\n${GREEN}🎉 Limpeza concluída!${NC}"
    echo -e "${BLUE}Próximo passo: ${GREEN}make dev${NC} para testar a nova arquitetura${NC}"
}

# Executar limpeza
main "$@" 