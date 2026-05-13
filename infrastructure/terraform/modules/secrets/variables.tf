variable "project_id" {
  type = string
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "openai_api_key" {
  type      = string
  sensitive = true
}

variable "mongo_root_password" {
  type      = string
  sensitive = true
}

variable "redis_password" {
  type      = string
  sensitive = true
}

variable "jwt_secret_key" {
  type      = string
  sensitive = true
}
