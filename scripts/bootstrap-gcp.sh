#!/usr/bin/env bash
# =============================================================================
# bootstrap-gcp.sh — Executar UMA VEZ, da sua máquina local.
#
# O que faz:
#   1. Verifica pré-requisitos (gcloud, terraform, jq)
#   2. Cria o bucket GCS para o state Terraform (se não existir)
#   3. Roda terraform init + plan + apply
#   4. Imprime os valores que devem ser adicionados como secrets no GitHub
#
# Pré-requisitos locais:
#   - gcloud CLI autenticado: gcloud auth application-default login
#   - terraform >= 1.6
#   - jq
#
# Uso:
#   chmod +x scripts/bootstrap-gcp.sh
#   ./scripts/bootstrap-gcp.sh
# =============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Cores
# ---------------------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERRO]${NC} $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Verificar pré-requisitos
# ---------------------------------------------------------------------------
check_prereqs() {
  info "Verificando pré-requisitos..."
  for cmd in gcloud terraform jq; do
    command -v "$cmd" &>/dev/null || error "'$cmd' não encontrado. Instale antes de continuar."
  done

  TERRAFORM_VERSION=$(terraform version -json | jq -r '.terraform_version')
  info "terraform $TERRAFORM_VERSION"

  GCLOUD_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
  [ -z "$GCLOUD_ACCOUNT" ] && error "gcloud não autenticado. Execute: gcloud auth application-default login"
  info "gcloud autenticado como: ${GCLOUD_ACCOUNT}"
  success "Pré-requisitos OK"
}

# ---------------------------------------------------------------------------
# Coletar configurações
# ---------------------------------------------------------------------------
collect_config() {
  echo ""
  echo -e "${CYAN}============================================================${NC}"
  echo -e "${CYAN}  Bootstrap empatIA — GCP Infrastructure${NC}"
  echo -e "${CYAN}============================================================${NC}"
  echo ""

  # Project ID
  DEFAULT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
  read -rp "$(echo -e "${BLUE}GCP Project ID${NC} [${DEFAULT_PROJECT}]: ")" INPUT_PROJECT
  PROJECT_ID="${INPUT_PROJECT:-$DEFAULT_PROJECT}"
  [ -z "$PROJECT_ID" ] && error "Project ID obrigatório."

  # Region
  read -rp "$(echo -e "${BLUE}Região GCP${NC} [us-central1]: ")" INPUT_REGION
  REGION="${INPUT_REGION:-us-central1}"

  # GitHub repo
  read -rp "$(echo -e "${BLUE}GitHub repo${NC} (owner/repo, ex: arangelcn/empath-ia): ")" GITHUB_REPO
  [ -z "$GITHUB_REPO" ] && error "GitHub repo obrigatório."

  # Secrets da aplicação
  echo ""
  info "Secrets da aplicação (serão armazenados no GCP Secret Manager):"

  read -rsp "$(echo -e "${BLUE}OPENAI_API_KEY${NC}: ")" OPENAI_API_KEY; echo ""
  [ -z "$OPENAI_API_KEY" ] && error "OPENAI_API_KEY obrigatório."

  read -rsp "$(echo -e "${BLUE}DID_API_USERNAME${NC}: ")" DID_API_USERNAME; echo ""
  read -rsp "$(echo -e "${BLUE}DID_API_PASSWORD${NC}: ")" DID_API_PASSWORD; echo ""

  # Derivados
  STATE_BUCKET="${PROJECT_ID}-terraform-state"

  echo ""
  info "Configuração coletada:"
  echo "  Project ID   : ${PROJECT_ID}"
  echo "  Região       : ${REGION}"
  echo "  GitHub repo  : ${GITHUB_REPO}"
  echo "  State bucket : gs://${STATE_BUCKET}"
  echo ""
  read -rp "$(echo -e "${YELLOW}Confirmar e continuar? [s/N]: ")" CONFIRM
  [[ "${CONFIRM,,}" =~ ^(s|sim|y|yes)$ ]] || { info "Cancelado."; exit 0; }
}

# ---------------------------------------------------------------------------
# Criar bucket de state
# ---------------------------------------------------------------------------
create_state_bucket() {
  echo ""
  info "Verificando bucket de state Terraform: gs://${STATE_BUCKET}..."

  if gsutil ls "gs://${STATE_BUCKET}" &>/dev/null; then
    success "Bucket já existe, continuando."
  else
    info "Criando bucket gs://${STATE_BUCKET}..."
    gsutil mb -p "${PROJECT_ID}" -l "${REGION}" "gs://${STATE_BUCKET}"
    gsutil versioning set on "gs://${STATE_BUCKET}"
    success "Bucket criado com versionamento habilitado."
  fi
}

# ---------------------------------------------------------------------------
# Terraform
# ---------------------------------------------------------------------------
run_terraform() {
  local TF_DIR
  TF_DIR="$(cd "$(dirname "$0")/.." && pwd)/infrastructure/terraform"

  echo ""
  info "Inicializando Terraform em ${TF_DIR}..."
  cd "$TF_DIR"

  terraform init \
    -backend-config="bucket=${STATE_BUCKET}" \
    -backend-config="prefix=terraform/state" \
    -reconfigure

  success "terraform init OK"

  echo ""
  info "Gerando terraform plan..."
  terraform plan \
    -var="project_id=${PROJECT_ID}" \
    -var="region=${REGION}" \
    -var="state_bucket=${STATE_BUCKET}" \
    -var="openai_api_key=${OPENAI_API_KEY}" \
    -var="did_api_username=${DID_API_USERNAME:-}" \
    -var="did_api_password=${DID_API_PASSWORD:-}" \
    -var="github_repo=${GITHUB_REPO}" \
    -out=tfplan

  echo ""
  read -rp "$(echo -e "${YELLOW}Aplicar o plano acima? [s/N]: ")" APPLY_CONFIRM
  [[ "${APPLY_CONFIRM,,}" =~ ^(s|sim|y|yes)$ ]] || { warn "Apply cancelado. O arquivo tfplan foi salvo."; exit 0; }

  echo ""
  info "Aplicando infra..."
  terraform apply tfplan
  success "terraform apply concluído!"
}

# ---------------------------------------------------------------------------
# Imprimir outputs / instruções
# ---------------------------------------------------------------------------
print_outputs() {
  local TF_DIR
  TF_DIR="$(cd "$(dirname "$0")/.." && pwd)/infrastructure/terraform"
  cd "$TF_DIR"

  echo ""
  echo -e "${GREEN}============================================================${NC}"
  echo -e "${GREEN}  Bootstrap concluído! Adicione estes secrets no GitHub:${NC}"
  echo -e "${GREEN}  https://github.com/${GITHUB_REPO}/settings/secrets/actions${NC}"
  echo -e "${GREEN}============================================================${NC}"
  echo ""

  WIF=$(terraform output -raw workload_identity_provider 2>/dev/null || echo "(consulte os outputs do terraform)")
  SA=$(terraform output -raw github_actions_service_account_email 2>/dev/null || echo "(consulte os outputs do terraform)")

  echo -e "  ${CYAN}GCP_PROJECT_ID${NC}                 = ${PROJECT_ID}"
  echo -e "  ${CYAN}GCP_WORKLOAD_IDENTITY_PROVIDER${NC} = ${WIF}"
  echo -e "  ${CYAN}GCP_SERVICE_ACCOUNT${NC}            = ${SA}"
  echo -e "  ${CYAN}OPENAI_API_KEY${NC}                 = (já configurado no Secret Manager)"
  echo ""
  echo -e "${YELLOW}Nota: GCP_SA_KEY NÃO é necessário no pipeline — o WIF autentica sem chaves JSON.${NC}"
  echo ""

  info "Para ver todos os outputs Terraform:"
  echo "  cd infrastructure/terraform && terraform output"
  echo ""
  info "Para conectar ao cluster GKE:"
  terraform output -raw gke_connect_command 2>/dev/null && echo "" || true
  echo ""
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  check_prereqs
  collect_config
  create_state_bucket
  run_terraform
  print_outputs
}

main "$@"
