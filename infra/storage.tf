resource "google_storage_bucket" "transcripts" {
    name = "${local.project_id}-quarterwatch-transcripts"
    location = local.region
    force_destroy = false

    uniform_bucket_level_access = true
    
    labels = local.common_labels

    lifecycle_rule {
        condition {
            age = 30
        }
        action {
            type = "Delete"
        }
    }

    depends_on = [google_project_service.cloudstorage]
}

output "transcripts_bucket" {
    description = "Name of the Cloud Storage bucket for raw transcripts"
    value = google_storage_bucket.transcripts.name
}