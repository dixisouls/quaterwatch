variable "project_id" {
    description = "GCP project ID"
    type = string
}

variable "region" {
    description = "GCP region"
    type = string
    default = "us-central1"
}

variable "environment" {
    description = "Deployment environment"
    type = string
    default = "production"
}

variable "db_password" {
    description = "Password for Cloud SQL postgres user"
    type = string
    sensitive = true
}

variable "secret_key" {
    description = "FastAPI secret key for JWT signing"
    type = string
    sensitive = true
}

variable "fmp_api_key" {
  description = "Financial Modeling Prep API key"
  type        = string
  sensitive   = true
}

variable "alpha_vantage_api_key" {
  description = "Alpha Vantage API key"
  type        = string
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth client secret"
  type        = string
  sensitive   = true
}
