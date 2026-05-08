output "name_servers" {
  description = "Name servers do Cloud DNS — copiar para o registrador do domínio"
  value       = google_dns_managed_zone.main.name_servers
}

output "zone_name" {
  description = "Nome da zona Cloud DNS"
  value       = google_dns_managed_zone.main.name
}
