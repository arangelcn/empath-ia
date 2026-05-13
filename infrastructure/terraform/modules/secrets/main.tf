locals {
  secrets = {
    openai-api-key      = var.openai_api_key
    mongo-root-password = var.mongo_root_password
    redis-password      = var.redis_password
    jwt-secret-key      = var.jwt_secret_key
  }
}

resource "google_secret_manager_secret" "app_secrets" {
  for_each  = local.secrets
  secret_id = "empatia-${each.key}"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    app         = "empatia"
  }
}

resource "google_secret_manager_secret_version" "app_secrets" {
  for_each    = local.secrets
  secret      = google_secret_manager_secret.app_secrets[each.key].id
  secret_data = each.value
}
