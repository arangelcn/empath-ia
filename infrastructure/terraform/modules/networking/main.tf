# VPC dedicada (evita uso da default VPC — boa prática de segurança)
resource "google_compute_network" "vpc" {
  name                    = "empatia-vpc-${var.environment}"
  auto_create_subnetworks = false
  project                 = var.project_id
}

# Subnet principal com secondary ranges para GKE Pods e Services
resource "google_compute_subnetwork" "main" {
  name          = "empatia-subnet-${var.environment}"
  ip_cidr_range = "10.0.0.0/20"
  region        = var.region
  network       = google_compute_network.vpc.id
  project       = var.project_id

  # Ranges secundários obrigatórios para GKE Autopilot
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.16.0.0/14"
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.20.0.0/20"
  }

  private_ip_google_access = true
}

# Cloud Router — necessário para o Cloud NAT
resource "google_compute_router" "main" {
  name    = "empatia-router-${var.environment}"
  region  = var.region
  network = google_compute_network.vpc.id
  project = var.project_id
}

# Cloud NAT — permite que pods sem IP público acessem a internet (PyPI, OpenAI, D-ID, etc.)
# Compartilhado entre todos os pods: custo único ~$0.045/hora ≈ $32/mês
resource "google_compute_router_nat" "main" {
  name                               = "empatia-nat-${var.environment}"
  router                             = google_compute_router.main.name
  region                             = var.region
  project                            = var.project_id
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = false
    filter = "ERRORS_ONLY"
  }
}

# Firewall: permitir health checks do GCP Load Balancer
resource "google_compute_firewall" "allow_health_checks" {
  name    = "empatia-allow-health-checks-${var.environment}"
  network = google_compute_network.vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
  }

  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
  target_tags   = ["gke-node"]
}

# Firewall: bloquear todo o tráfego de entrada por defeito (GKE Autopilot já gere isto)
resource "google_compute_firewall" "deny_all_ingress" {
  name      = "empatia-deny-all-ingress-${var.environment}"
  network   = google_compute_network.vpc.name
  project   = var.project_id
  priority  = 65534
  direction = "INGRESS"

  deny {
    protocol = "all"
  }

  source_ranges = ["0.0.0.0/0"]
}
