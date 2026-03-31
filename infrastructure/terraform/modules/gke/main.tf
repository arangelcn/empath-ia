# GKE Autopilot — sem gestão de nós, paga apenas pelos pods em execução
# Melhor custo/benefício para workloads variáveis como este projeto
resource "google_container_cluster" "autopilot" {
  provider = google-beta

  name     = var.cluster_name
  location = var.region
  project  = var.project_id

  # Autopilot mode
  enable_autopilot = true

  # Rede privada — nós sem IP público (mais seguro e sem custo extra de IP)
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  network    = var.network
  subnetwork = var.subnetwork

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # Workload Identity — permite que pods usem Service Accounts GCP sem chaves JSON
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Desabilitar logs de sistema para reduzir custos (Cloud Logging)
  # Manter apenas logs de workload em caso de debug
  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS"]
    managed_prometheus {
      enabled = false
    }
  }

  # Manutenção em horário de baixo tráfego (reduz disrupções)
  maintenance_policy {
    recurring_window {
      start_time = "2024-01-01T03:00:00Z"
      end_time   = "2024-01-01T07:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=SA,SU"
    }
  }

  release_channel {
    channel = "REGULAR"
  }

  deletion_protection = var.environment == "prod"
}
