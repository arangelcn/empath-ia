#!/bin/bash
set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Iniciando migração empatIA para arquitetura de microserviços...${NC}"

# Função para backup
backup_current() {
    echo -e "${YELLOW}📦 Criando backup...${NC}"
    BACKUP_DIR="../empath-ia-backup-$(date +%Y%m%d_%H%M%S)"
    cp -r . "$BACKUP_DIR"
    echo -e "${GREEN}✅ Backup criado em $BACKUP_DIR${NC}"
}

# Função para criar estrutura de diretórios
create_structure() {
    echo -e "${YELLOW}📁 Criando nova estrutura de diretórios...${NC}"
    
    # Serviços
    mkdir -p services/{ai-service,avatar-service,emotion-service,gateway-service}/{src,tests}
    mkdir -p services/ai-service/src/{models,services,api}
    mkdir -p services/avatar-service/src/{models,services,api}
    mkdir -p services/emotion-service/src/{processors,models,api}
    mkdir -p services/gateway-service/src/{services,orchestrators,api}
    
    # Apps
    mkdir -p apps/web-ui/{src,assets}
    mkdir -p apps/web-ui/src/{components,services,utils}
    mkdir -p apps/web-ui/src/components/{Chat,Avatar,EmotionAnalysis,Common}
    
    # Data
    mkdir -p data/{shared,models,uploads,logs}
    
    # Infrastructure
    mkdir -p infrastructure/{docker,kubernetes,monitoring}
    mkdir -p infrastructure/docker/{services,base}
    mkdir -p infrastructure/kubernetes/{manifests,helm}
    mkdir -p infrastructure/monitoring/{prometheus,grafana,jaeger}
    
    # Config
    mkdir -p config/environments
    
    # Outros
    mkdir -p scripts tests docs
    mkdir -p tests/{integration,e2e,performance}
    mkdir -p docs/{api,architecture,deployment,user-guide}
    
    echo -e "${GREEN}✅ Estrutura de diretórios criada${NC}"
}

# Função para migrar Avatar Service
migrate_avatar_service() {
    echo -e "${YELLOW}🎭 Migrando Avatar Service...${NC}"
    
    # Migrar did_client.py
    if [[ -f "backend/app/did_client.py" ]]; then
        cp backend/app/did_client.py services/avatar-service/src/services/
        echo "  ✅ did_client.py migrado"
    else
        echo -e "${RED}  ❌ backend/app/did_client.py não encontrado${NC}"
    fi
    
    # Criar __init__.py files
    touch services/avatar-service/src/{__init__.py,services/__init__.py,models/__init__.py,api/__init__.py}
    
    # Criar requirements.txt
    cat > services/avatar-service/requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
requests==2.31.0
python-dotenv==1.0.0
EOF

    echo "  ✅ Avatar Service configurado"
}

# Função para migrar Emotion Service
migrate_emotion_service() {
    echo -e "${YELLOW}😊 Migrando Emotion Service...${NC}"
    
    # Migrar openface_integration.py
    if [[ -f "backend/app/utils/openface_integration.py" ]]; then
        cp backend/app/utils/openface_integration.py services/emotion-service/src/processors/openface_processor.py
        echo "  ✅ openface_integration.py migrado para openface_processor.py"
    else
        echo -e "${RED}  ❌ backend/app/utils/openface_integration.py não encontrado${NC}"
    fi
    
    # Criar __init__.py files
    touch services/emotion-service/src/{__init__.py,processors/__init__.py,models/__init__.py,api/__init__.py}
    
    # Criar requirements.txt
    cat > services/emotion-service/requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
opencv-python==4.8.1.78
numpy==1.24.3
python-dotenv==1.0.0
pillow==10.1.0
EOF

    echo "  ✅ Emotion Service configurado"
}

# Função para migrar AI Service (extrair de backend/app/app.py)
migrate_ai_service() {
    echo -e "${YELLOW}🤖 Configurando AI Service...${NC}"
    
    # Criar __init__.py files
    touch services/ai-service/src/{__init__.py,models/__init__.py,services/__init__.py,api/__init__.py}
    
    # Criar requirements.txt
    cat > services/ai-service/requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
openai==1.3.8
python-dotenv==1.0.0
EOF

    echo "  ✅ AI Service estrutura criada"
    echo "  ⚠️  Extração manual necessária de backend/app/app.py (linhas do chat)"
}

# Função para configurar Gateway Service
configure_gateway_service() {
    echo -e "${YELLOW}🌐 Configurando Gateway Service...${NC}"
    
    # Criar __init__.py files
    touch services/gateway-service/src/{__init__.py,services/__init__.py,orchestrators/__init__.py,api/__init__.py}
    
    # Criar requirements.txt
    cat > services/gateway-service/requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
httpx==0.25.2
python-dotenv==1.0.0
python-multipart==0.0.6
EOF

    echo "  ✅ Gateway Service configurado"
}

# Função para migrar Frontend
migrate_frontend() {
    echo -e "${YELLOW}🖥️ Migrando Frontend...${NC}"
    
    # Migrar app.py principal
    if [[ -f "frontend/app.py" ]]; then
        cp frontend/app.py apps/web-ui/src/main.py
        echo "  ✅ frontend/app.py migrado para apps/web-ui/src/main.py"
    else
        echo -e "${RED}  ❌ frontend/app.py não encontrado${NC}"
    fi
    
    # Migrar requirements.txt
    if [[ -f "frontend/requirements.txt" ]]; then
        cp frontend/requirements.txt apps/web-ui/
        echo "  ✅ requirements.txt migrado"
    fi
    
    # Migrar Dockerfile
    if [[ -f "frontend/Dockerfile" ]]; then
        cp frontend/Dockerfile apps/web-ui/
        echo "  ✅ Dockerfile migrado"
    fi
    
    # Criar __init__.py files
    touch apps/web-ui/src/{__init__.py,components/__init__.py,services/__init__.py,utils/__init__.py}
    touch apps/web-ui/src/components/{Chat/__init__.py,Avatar/__init__.py,EmotionAnalysis/__init__.py,Common/__init__.py}
    
    echo "  ✅ Frontend migrado"
    echo "  ⚠️  Refatoração em componentes necessária"
}

# Função para migrar Infraestrutura
migrate_infrastructure() {
    echo -e "${YELLOW}🐳 Migrando Infraestrutura...${NC}"
    
    # Migrar OpenFace
    if [[ -d "openface" ]]; then
        cp -r openface/ infrastructure/docker/base/openface-base/
        echo "  ✅ openface/ migrado para infrastructure/docker/base/openface-base/"
    else
        echo -e "${RED}  ❌ diretório openface/ não encontrado${NC}"
    fi
    
    # Migrar shared_data
    if [[ -d "shared_data" ]]; then
        mv shared_data/ data/shared/ 2>/dev/null || cp -r shared_data/ data/shared/
        echo "  ✅ shared_data/ migrado para data/shared/"
    else
        echo -e "${YELLOW}  ⚠️  diretório shared_data/ não encontrado${NC}"
    fi
    
    echo "  ✅ Infraestrutura migrada"
}

# Função para criar configurações
create_configs() {
    echo -e "${YELLOW}⚙️ Criando configurações...${NC}"
    
    # Criar .env.example se não existir
    if [[ ! -f ".env.example" ]]; then
        if [[ -f "env.example" ]]; then
            cp env.example .env.example
        fi
    fi
    
    # Criar .gitignore se não existir
    if [[ ! -f ".gitignore" ]]; then
        cat > .gitignore << 'EOF'
# Environment variables
.env
.env.local
.env.production

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Docker
.dockerignore

# Logs
*.log
logs/
data/logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Data
data/uploads/
data/models/
!data/shared/.gitkeep

# Backups
*backup*
migration-backup/

# OpenFace outputs
*.csv
*.txt
data/shared/*.jpg
data/shared/*.png
data/shared/*.mp4

# Temporary files
tmp/
temp/
*.tmp
EOF
    fi
    
    echo "  ✅ Configurações criadas"
}

# Função para criar arquivos de exemplo
create_sample_files() {
    echo -e "${YELLOW}📄 Criando arquivos de exemplo...${NC}"
    
    # .gitkeep para diretórios vazios
    touch data/{shared,models,uploads,logs}/.gitkeep
    touch docs/{api,architecture,deployment,user-guide}/.gitkeep
    touch tests/{integration,e2e,performance}/.gitkeep
    
    echo "  ✅ Arquivos de exemplo criados"
}

# Função para validar migração
validate_migration() {
    echo -e "${YELLOW}🔍 Validando migração...${NC}"
    
    local errors=0
    
    # Verificar estrutura crítica
    local critical_dirs=(
        "services/ai-service/src"
        "services/avatar-service/src"
        "services/emotion-service/src"
        "services/gateway-service/src"
        "apps/web-ui/src"
        "data/shared"
        "infrastructure/docker"
    )
    
    for dir in "${critical_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            echo -e "  ${GREEN}✅ $dir${NC}"
        else
            echo -e "  ${RED}❌ $dir - FALTANDO${NC}"
            ((errors++))
        fi
    done
    
    # Verificar arquivos migrados
    local migrated_files=(
        "services/avatar-service/src/services/did_client.py"
        "services/emotion-service/src/processors/openface_processor.py"
        "apps/web-ui/src/main.py"
    )
    
    for file in "${migrated_files[@]}"; do
        if [[ -f "$file" ]]; then
            echo -e "  ${GREEN}✅ $file${NC}"
        else
            echo -e "  ${YELLOW}⚠️  $file - PODE PRECISAR DE MIGRAÇÃO MANUAL${NC}"
        fi
    done
    
    if [[ $errors -eq 0 ]]; then
        echo -e "${GREEN}✅ Validação passou - estrutura básica OK${NC}"
    else
        echo -e "${RED}❌ Validação encontrou $errors erros${NC}"
    fi
}

# Função para mostrar próximos passos
show_next_steps() {
    echo -e "\n${BLUE}🎉 Migração estrutural concluída!${NC}"
    echo -e "\n${YELLOW}📋 Próximos passos:${NC}"
    echo -e "  1. ${GREEN}make setup${NC} - Configurar ambiente"
    echo -e "  2. ${GREEN}cp env.example .env${NC} - Configurar variáveis"
    echo -e "  3. Editar .env com suas chaves API"
    echo -e "  4. Implementar código dos serviços:"
    echo -e "     - ${YELLOW}AI Service:${NC} Extrair lógica OpenAI de backend/app/app.py"
    echo -e "     - ${YELLOW}Gateway:${NC} Criar orquestrador que chama os outros serviços"
    echo -e "     - ${YELLOW}Frontend:${NC} Refatorar em componentes"
    echo -e "  5. ${GREEN}make dev${NC} - Testar nova arquitetura"
    echo -e "\n${BLUE}📖 Consulte MIGRATION_GUIDE.md para detalhes específicos${NC}"
}

# Função principal
main() {
    # Verificar se estamos no diretório correto
    if [[ ! -f "README.md" ]] || [[ ! -d "backend" ]]; then
        echo -e "${RED}❌ Execute este script na raiz do projeto empatIA${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Você está prestes a migrar seu projeto para uma arquitetura de microserviços.${NC}"
    echo -e "${YELLOW}Deseja continuar? (y/N)${NC}"
    read -r response
    
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Migração cancelada.${NC}"
        exit 0
    fi
    
    backup_current
    create_structure
    migrate_avatar_service
    migrate_emotion_service
    migrate_ai_service
    configure_gateway_service
    migrate_frontend
    migrate_infrastructure
    create_configs
    create_sample_files
    validate_migration
    show_next_steps
}

# Verificar dependências
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não encontrado. Instale o Docker primeiro.${NC}"
    exit 1
fi

# Executar migração
main "$@" 