terraform {
  required_version = ">= 1.7"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
    project_id = var.project_id
    region = var.region
    app_name = "quarterwatch"
    
    common_labels = {
        app = "quarterwatch"
        environment = var.environment
        managed_by = "terraform"
    }
}