resource "google_sql_database_instance" "quarterwatch" {
    name = "quarterwatch-db"
    database_version = "POSTGRES_16"
    region = local.region
    
    settings {
        tier = "db-f1-micro"
        availability_type = "ZONAL"
        disk_size = 10
        disk_autoresize = false

        backup_configuration {
            enabled = false
        }

        ip_configuration {
            ipv4_enabled = true
        }

        database_flags {
            name = "max_connections"
            value = "25"
        }

        insights_config {
            query_insights_enabled = false
        }
    }
    deletion_protection = false

    depends_on = [google_project_service.cloudsql]
}

resource "google_sql_database" "quarterwatch" {
    name = "quarterwatch"
    instance = google_sql_database_instance.quarterwatch.name
}

resource "google_sql_user" "postgres" {
    name = "postgres"
    instance = google_sql_database_instance.quarterwatch.name
    password = var.db_password
}

output "db_instance_connection_name" {
    description = "Cloud SQL connection name for Cloud Run"
    value = google_sql_database_instance.quarterwatch.connection_name
}

output "db_instance_ip" {
    description = "Cloud SQL public IP"
    value = google_sql_database_instance.quarterwatch.ip_address
}
