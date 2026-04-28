# ── Service Account ────────────────────────────────────────────────────────

resource "google_service_account" "cloudrun" {
  account_id   = "quarterwatch-cloudrun"
  display_name = "QuarterWatch Cloud Run Service Account"
}

resource "google_project_iam_member" "cloudrun_sql" {
  project = local.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_project_iam_member" "cloudrun_storage" {
  project = local.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_project_iam_member" "cloudrun_secrets" {
  project = local.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_project_iam_member" "cloudrun_tasks" {
  project = local.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_project_iam_member" "cloudrun_vertexai" {
  project = local.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

# ── API Service ────────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "api" {
  name     = "quarterwatch-api"
  location = local.region

  template {
    service_account = google_service_account.cloudrun.email

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = "gcr.io/cloudrun/hello:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = local.project_id
      }

      env {
        name  = "GCP_LOCATION"
        value = local.region
      }

      env {
        name  = "CLOUD_TASKS_QUEUE"
        value = "quarterwatch-jobs"
      }

      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.transcripts.name
      }

      env {
        name  = "WORKER_URL"
        value = "https://quarterwatch-worker-${data.google_project.project.number}-uc.a.run.app"
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "GOOGLE_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.google_client_id.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "GOOGLE_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.google_client_secret.secret_id
            version = "latest"
          }
        }
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.quarterwatch.connection_name]
      }
    }
  }

  depends_on = [
    google_project_service.cloudrun,
    google_sql_database_instance.quarterwatch,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "api_public" {
  project  = local.project_id
  location = local.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Worker Service ─────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "worker" {
  name     = "quarterwatch-worker"
  location = local.region

  template {
    service_account = google_service_account.cloudrun.email

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = "gcr.io/cloudrun/hello:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
        cpu_idle = true
      }

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = local.project_id
      }

      env {
        name  = "GCP_LOCATION"
        value = local.region
      }

      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.transcripts.name
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "FMP_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.fmp_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "ALPHA_VANTAGE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.alpha_vantage_api_key.secret_id
            version = "latest"
          }
        }
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.quarterwatch.connection_name]
      }
    }
  }

  depends_on = [
    google_project_service.cloudrun,
    google_sql_database_instance.quarterwatch,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "worker_tasks_only" {
  project  = local.project_id
  location = local.region
  name     = google_cloud_run_v2_service.worker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.cloudrun.email}"
}

# ── Data source ────────────────────────────────────────────────────────────

data "google_project" "project" {
  project_id = local.project_id
}

output "api_url" {
  description = "Cloud Run URL for the FastAPI backend"
  value       = google_cloud_run_v2_service.api.uri
}

output "worker_url" {
  description = "Cloud Run URL for the worker"
  value       = google_cloud_run_v2_service.worker.uri
}