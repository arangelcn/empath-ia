variable "project_id" {
  description = "ID do projeto GCP"
  type        = string
}

variable "region" {
  description = "Região GCP para todos os recursos"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Zona GCP para recursos zonais"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Nome do ambiente (prod, staging)"
  type        = string
  default     = "prod"
}

variable "gke_cluster_name" {
  description = "Nome do cluster GKE Autopilot"
  type        = string
  default     = "empatia-cluster"
}

variable "artifact_registry_repo" {
  description = "Nome do repositório no Artifact Registry"
  type        = string
  default     = "empatia-images"
}

variable "state_bucket" {
  description = "Nome do bucket GCS para armazenar o state do Terraform"
  type        = string
}

# Secrets da aplicação (passados para o Secret Manager)
variable "openai_api_key" {
  description = "Chave da API OpenAI"
  type        = string
  sensitive   = true
}

variable "did_api_username" {
  description = "Username da API D-ID (avatar)"
  type        = string
  sensitive   = true
}

variable "did_api_password" {
  description = "Password da API D-ID (avatar)"
  type        = string
  sensitive   = true
}

variable "mongo_root_password" {
  description = "Password do utilizador root do MongoDB"
  type        = string
  sensitive   = true
  default     = null
}

variable "redis_password" {
  description = "Password do Redis"
  type        = string
  sensitive   = true
  default     = null
}

variable "jwt_secret_key" {
  description = "Chave secreta para JWT"
  type        = string
  sensitive   = true
  default     = null
}

# Workload Identity para GitHub Actions
variable "github_repo" {
  description = "Repositório GitHub no formato owner/repo"
  type        = string
  default     = ""
}
