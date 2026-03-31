output "gke_cluster_name" {
  description = "Nome do cluster GKE"
  value       = module.gke.cluster_name
}

output "gke_cluster_endpoint" {
  description = "Endpoint do cluster GKE"
  value       = module.gke.cluster_endpoint
  sensitive   = true
}

output "artifact_registry_url" {
  description = "URL do Artifact Registry"
  value       = module.registry.registry_url
}

output "artifact_registry_hostname" {
  description = "Hostname do Artifact Registry (para docker login)"
  value       = module.registry.registry_hostname
}

output "app_service_account_email" {
  description = "Email da Service Account da aplicação"
  value       = google_service_account.app.email
}

output "github_actions_service_account_email" {
  description = "Email da Service Account do GitHub Actions"
  value       = var.github_repo != "" ? google_service_account.github_actions[0].email : ""
}

output "workload_identity_provider" {
  description = "Provider de Workload Identity para o GitHub Actions (usar em GCP_WORKLOAD_IDENTITY_PROVIDER)"
  value       = var.github_repo != "" ? google_iam_workload_identity_pool_provider.github[0].name : ""
}

output "app_data_bucket" {
  description = "Bucket GCS para dados da aplicação"
  value       = google_storage_bucket.app_data.name
}

output "gke_connect_command" {
  description = "Comando para conectar ao cluster GKE"
  value       = "gcloud container clusters get-credentials ${module.gke.cluster_name} --region ${var.region} --project ${var.project_id}"
}
