variable "project_id" {
  description = "ID do projeto GCP"
  type        = string
}

variable "environment" {
  description = "Nome do ambiente (prod, staging)"
  type        = string
}

variable "domain_name" {
  description = "Nome do domínio raiz (ex: empathia.app)"
  type        = string
}

variable "ingress_ip" {
  description = "IP público do Load Balancer do GKE Ingress"
  type        = string
}
