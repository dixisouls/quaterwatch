resource "google_secret_manager_secret" "db_password" {
    secret_id = "quarterwatch-db-password"
    labels = local.common_labels
    replication {
        auto {}
    }
    depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "db_password" {
    secret = google_secret_manager_secret.db_password.id
    secret_data = var.db_password
}

resource "google_secret_manager_secret" "secret_key" {
    secret_id = "quarterwatch-secret-key"
    labels = local.common_labels
    replication {
        auto {}
    }
    depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "secret_key" {
    secret = google_secret_manager_secret.secret_key.id
    secret_data = var.secret_key
}

resource "google_secret_manager_secret" "fmp_api_key" {
    secret_id = "quarterwatch-fmp-api-key"
    labels = local.common_labels
    replication {
        auto {}
    }
    depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "fmp_api_key" {
    secret = google_secret_manager_secret.fmp_api_key.id
    secret_data = var.fmp_api_key
}

resource "google_secret_manager_secret" "alpha_vantage_api_key" {
    secret_id = "quarterwatch-alpha-vantage-api-key"
    labels = local.common_labels
    replication {
        auto {}
    }
    depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "alpha_vantage_api_key" {
    secret = google_secret_manager_secret.alpha_vantage_api_key.id
    secret_data = var.alpha_vantage_api_key
}

resource "google_secret_manager_secret" "google_client_id" {
    secret_id = "quarterwatch-google-client-id"
    labels = local.common_labels
    replication {
        auto {}
    }
    depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "google_client_id" {
    secret = google_secret_manager_secret.google_client_id.id
    secret_data = var.google_client_id
}

resource "google_secret_manager_secret" "google_client_secret" {
    secret_id = "quarterwatch-google-client-secret"
    labels = local.common_labels
    replication {
        auto {}
    }
    depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "google_client_secret" {
    secret = google_secret_manager_secret.google_client_secret.id
    secret_data = var.google_client_secret
}