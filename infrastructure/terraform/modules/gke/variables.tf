variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "cluster_name" {
  type    = string
  default = "empatia-cluster"
}

variable "network" {
  type = string
}

variable "subnetwork" {
  type = string
}

variable "environment" {
  type    = string
  default = "prod"
}
