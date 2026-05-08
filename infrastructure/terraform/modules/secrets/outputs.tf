output "secret_ids" {
  description = "IDs dos secrets criados no Secret Manager"
  value       = { for k, v in google_secret_manager_secret.app_secrets : k => v.secret_id }
}
