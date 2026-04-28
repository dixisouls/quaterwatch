resource "google_artifact_registry_repository" "quarterwatch" {
    repository_id = "quarterwatch"
    format = "DOCKER"
    location = local.region
    description = "Docker images for QuarterWatch API and worker"
    labels = local.common_labels

    depends_on = [google_project_service.artifactregistry]
}

output "registry_url" {
    description = "Base URL for pushing Docker images"
    value = "${local.region}-docker.pkg.dev/${local.project_id}/quarterwatch"
}