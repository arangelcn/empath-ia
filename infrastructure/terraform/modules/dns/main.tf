# Zona DNS pública no Cloud DNS para o domínio empat-ia.io
resource "google_dns_managed_zone" "main" {
  name        = "${var.environment}-empathia-zone"
  dns_name    = "${var.domain_name}."
  description = "Zona DNS pública para ${var.domain_name}"
  project     = var.project_id

  dnssec_config {
    state = "on"
  }
}

# Registo A para app.empat-ia.io → Load Balancer do GKE Ingress
resource "google_dns_record_set" "app" {
  name         = "app.${var.domain_name}."
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.main.name
  project      = var.project_id
  rrdatas      = [var.ingress_ip]
}

# Registo A para admin.empat-ia.io → mesmo Load Balancer
resource "google_dns_record_set" "admin" {
  name         = "admin.${var.domain_name}."
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.main.name
  project      = var.project_id
  rrdatas      = [var.ingress_ip]
}

# Registo A para api.empat-ia.io → mesmo Load Balancer
resource "google_dns_record_set" "api" {
  name         = "api.${var.domain_name}."
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.main.name
  project      = var.project_id
  rrdatas      = [var.ingress_ip]
}
