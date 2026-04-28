resource "google_project_service" "cloudrun" {
    service = "run.googleapis.com"
    disable_on_destroy = false
}

resource "google_project_service" "cloudsql" {
    service = "sqladmin.googleapis.com"
    disable_on_destroy = false
}

resource "google_project_service" "cloudtasks" {
    service = "cloudtasks.googleapis.com"
    disable_on_destroy = false
}

resource "google_project_service" "cloudstorage" {
    service = "storage.googleapis.com"
    disable_on_destroy = false
}

resource "google_project_service" "secretmanager" {
    service = "secretmanager.googleapis.com"
    disable_on_destroy = false
}

resource "google_project_service" "artifactregistry" {
    service = "artifactregistry.googleapis.com"
    disable_on_destroy = false
}

resource "google_project_service" "cloudscheduler" {
    service = "cloudscheduler.googleapis.com"
    disable_on_destroy = false
}

resource "google_project_service" "naturallanguage" {
    service = "language.googleapis.com"
    disable_on_destroy = false
}

resource "google_project_service" "vertexai" {
    service = "aiplatform.googleapis.com"
    disable_on_destroy = false
}