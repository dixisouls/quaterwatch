resource "google_service_account" "scheduler" {
    account_id = "quarterwatch-scheduler"
    display_name = "QuarterWatch Cloud Scheduler Service Account"
}

resource "google_cloud_run_v2_service_iam_member" "scheduler_invoker" {
    project = local.project_id
    location = local.region
    name = google_cloud_run_v2_service.api.name
    role = "roles/run.invoker"
    member = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_cloud_scheduler_job" "price_fetch" {
    name = "quarterwatch-price-fetch"
    description = "Nightly job to fetch post-call stock price movement"
    schedule = "0 2 * * *"
    time_zone = "America/New_York"
    attempt_deadline = "320s"

    retry_config {
        retry_count = 3
        min_backoff_duration = "5s"
        max_backoff_duration = "60s"
        max_doublings = 3
    }

    http_target {
      http_method = "POST"
      uri = "${google_cloud_run_v2_service.api.uri}/api/internal/price-fetch"

      oidc_token {
        service_account_email = google_service_account.scheduler.email
        audience = google_cloud_run_v2_service.api.uri
      }
    }
    depends_on = [ google_project_service.cloudscheduler, google_cloud_run_v2_service.api ]
}

output "scheduler_job_name" {
    description = "Name of the nightly price fetch scheduler job"
    value = google_cloud_scheduler_job.price_fetch.name
}