output "registry_url" {
  description = "URL completa do repositório (usar no docker push)"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repo_name}"
}

output "registry_hostname" {
  description = "Hostname para docker login"
  value       = "${var.region}-docker.pkg.dev"
}

output "repository_id" {
  value = google_artifact_registry_repository.images.repository_id
}
