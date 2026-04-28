output "deployment_summary" {
    description = "Summary of all deployed resources"
    value = {
        api_url = google_cloud_run_v2_service.api.uri
        worker_url = google_cloud_run_v2_service.worker.uri
        registry_url = "${local.region}-docker.pkg.dev/${local.project_id}/quarterwatch"
        bucket_name = google_storage_bucket.transcripts.name
        db_connection = google_sql_database_instance.quarterwatch.connection_name
        tasks_queue = google_cloud_tasks_queue.quarterwatch_jobs.id
        scheduler_job = google_cloud_scheduler_job.price_fetch.name
    }
}