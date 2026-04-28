resource "google_cloud_tasks_queue" "quarterwatch_jobs" {
    name = "quarterwatch-jobs"
    location = local.region

    rate_limits {
      max_concurrent_dispatches = 5
      max_dispatches_per_second = 2
    }

    retry_config {
      max_attempts = 3
      max_retry_duration = "3600s"
      min_backoff = "10s"
      max_backoff = "300s"
      max_doublings = 4
    }
    depends_on = [google_project_service.cloudtasks]
}

output "tasks_queue_name" {
    description = "Full Cloud Tasks queue name"
    value = google_cloud_tasks_queue.quarterwatch_jobs.id
}