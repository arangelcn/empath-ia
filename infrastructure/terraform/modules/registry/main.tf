# Artifact Registry — repositório Docker para todas as imagens do projecto
# Mais barato e moderno que o Container Registry legado
resource "google_artifact_registry_repository" "images" {
  repository_id = var.repo_name
  format        = "DOCKER"
  location      = var.region
  project       = var.project_id
  description   = "Imagens Docker do empatIA - ${var.environment}"

  # Limpar imagens antigas automaticamente (reduz custos de armazenamento)
  cleanup_policies {
    id     = "keep-last-5-tagged"
    action = "KEEP"
    most_recent_versions {
      keep_count = 5
    }
  }

  cleanup_policies {
    id     = "delete-untagged"
    action = "DELETE"
    condition {
      tag_state = "UNTAGGED"
      older_than = "168h" # 7 dias
    }
  }
}
