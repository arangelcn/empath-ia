# Habilitar APIs necessárias
resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "storage.googleapis.com",
    "dns.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

# Módulo: Networking (VPC, Subnet, Cloud NAT)
module "networking" {
  source = "./modules/networking"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  depends_on = [google_project_service.apis]
}

# Módulo: GKE Autopilot
module "gke" {
  source = "./modules/gke"

  project_id   = var.project_id
  region       = var.region
  cluster_name = var.gke_cluster_name
  network      = module.networking.network_name
  subnetwork   = module.networking.subnetwork_name
  environment  = var.environment

  depends_on = [module.networking]
}

# Módulo: Artifact Registry
module "registry" {
  source = "./modules/registry"

  project_id  = var.project_id
  region      = var.region
  repo_name   = var.artifact_registry_repo
  environment = var.environment

  depends_on = [google_project_service.apis]
}

# Módulo: Secret Manager
module "secrets" {
  source = "./modules/secrets"

  project_id          = var.project_id
  environment         = var.environment
  openai_api_key      = var.openai_api_key
  did_api_username    = var.did_api_username
  did_api_password    = var.did_api_password
  mongo_root_password = coalesce(var.mongo_root_password, random_password.mongo.result)
  redis_password      = coalesce(var.redis_password, random_password.redis.result)
  jwt_secret_key      = coalesce(var.jwt_secret_key, random_password.jwt.result)

  depends_on = [google_project_service.apis]
}

# Gerar passwords aleatórias quando não fornecidas
resource "random_password" "mongo" {
  length  = 32
  special = false
}

resource "random_password" "redis" {
  length  = 32
  special = false
}

resource "random_password" "jwt" {
  length  = 64
  special = false
}

# Service Account para a aplicação no GKE (Workload Identity)
resource "google_service_account" "app" {
  account_id   = "empatia-app"
  display_name = "empatIA Application Service Account"
  project      = var.project_id
}

# Permissão para aceder ao Secret Manager
resource "google_project_iam_member" "app_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# Binding Workload Identity: K8s SA → GCP SA
resource "google_service_account_iam_member" "workload_identity_app" {
  service_account_id = google_service_account.app.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[empatia/empatia-app]"

  depends_on = [module.gke]
}

# Service Account para o GitHub Actions (CI/CD)
resource "google_service_account" "github_actions" {
  count        = var.github_repo != "" ? 1 : 0
  account_id   = "github-actions-cicd"
  display_name = "GitHub Actions CI/CD"
  project      = var.project_id
}

resource "google_project_iam_member" "github_actions_roles" {
  for_each = var.github_repo != "" ? toset([
    "roles/container.developer",
    "roles/artifactregistry.writer",
    "roles/iam.serviceAccountTokenCreator",
  ]) : toset([])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.github_actions[0].email}"
}

# Workload Identity Pool para GitHub Actions (sem chaves JSON)
resource "google_iam_workload_identity_pool" "github" {
  count                     = var.github_repo != "" ? 1 : 0
  provider                  = google-beta
  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions Pool"
  project                   = var.project_id
}

resource "google_iam_workload_identity_pool_provider" "github" {
  count                              = var.github_repo != "" ? 1 : 0
  provider                           = google-beta
  workload_identity_pool_id          = google_iam_workload_identity_pool.github[0].workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Provider"
  project                            = var.project_id

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "attribute.repository == \"${var.github_repo}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "github_wif" {
  count              = var.github_repo != "" ? 1 : 0
  service_account_id = google_service_account.github_actions[0].name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github[0].name}/attribute.repository/${var.github_repo}"
}

# Bucket GCS para artefactos de TTS e uploads
resource "google_storage_bucket" "app_data" {
  name                        = "${var.project_id}-empatia-data"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = false

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  versioning {
    enabled = false
  }
}

resource "google_storage_bucket_iam_member" "app_storage" {
  bucket = google_storage_bucket.app_data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.app.email}"
}
