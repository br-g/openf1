#===========#
# VARIABLES #
#===========#

variable "gcp_project_id" {
  type = string
  description = "Google Cloud project ID"
}

variable "gcp_region" {
  type = string
  description = "Google Cloud region"
}

variable "credentials_path" {
  description = "Path to the GCP service account key JSON file"
  type = string
}

variable "mongo_connection_string" {
  description = "The MongoDB connection string"
  type = string
  sensitive = true
}

variable "timeout" {
  type = string
  description = "Execution timeout"
  default = "60s" // 1 minute
}

variable "logging_bucket_name" {
  type = string
  description = "Name of the bucket for storing logs"
}


#===========#
# PROVIDERS #
#===========#

terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
    docker = {
      source = "kreuzwerker/docker"
    }
  }
  backend "gcs" {
    bucket = "openf1-tf-backend"
    prefix = "terraform/state/query_api"
    credentials = "./google_credentials.json"
  }
}

provider "google" {
  credentials = file("${var.credentials_path}")
  project = var.gcp_project_id
  region = var.gcp_region
}

data "google_client_config" "default" {}

provider "docker" {
  registry_auth {
    address = "gcr.io"
    username = "oauth2accesstoken"
    password = data.google_client_config.default.access_token
  }
}


#==============#
# DOCKER IMAGE #
#==============#
data "docker_registry_image" "myapp" {
  name = "gcr.io/${var.gcp_project_id}/query-api:latest"
}


#===========#
# CLOUD RUN #
#===========#

resource "google_cloud_run_v2_service" "default" {
  name = "query-api"
  location = var.gcp_region

  template {
    service_account = google_service_account.sa.email
    containers {
      image = "${data.docker_registry_image.myapp.name}@${data.docker_registry_image.myapp.sha256_digest}"

      resources {
        limits = {
          cpu = "2000m"
          memory = "4Gi"
        }
        cpu_idle = true  # garbage-collect CPU once a request finishes
      }

      env {
        name = "MONGO_CONNECTION_STRING"
        value = var.mongo_connection_string
      }
    }
    max_instance_request_concurrency = 5
    timeout = var.timeout
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
  }
}


#===============#
# CLOUD LOGGING #
#===============#

resource "google_logging_project_sink" "cloud_run_sink" {
  name = "cloud-run-logs-to-gcs"
  destination = "storage.googleapis.com/${var.logging_bucket_name}"

  filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"query-api\""

  # Use unique_writer_identity to decouple the IAM permission from the sink
  unique_writer_identity = true
}


#===========#
# IAM       #
#===========#

data "google_iam_policy" "no_auth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "no_auth" {
  location = google_cloud_run_v2_service.default.location
  project = google_cloud_run_v2_service.default.project
  service = google_cloud_run_v2_service.default.name
  policy_data = data.google_iam_policy.no_auth.policy_data
}

resource "google_service_account" "sa" {
  account_id = "sa-query-api"
  display_name = "sa-query-api"
  project = var.gcp_project_id
}

resource "google_project_iam_member" "bigquery_data_viewer" {
  project = var.gcp_project_id
  role = "roles/bigquery.dataViewer"
  member = "serviceAccount:${google_service_account.sa.email}"
}

resource "google_project_iam_member" "bigquery_job_user" {
  project = var.gcp_project_id
  role = "roles/bigquery.jobUser"
  member = "serviceAccount:${google_service_account.sa.email}"
}

# Grant permission for logging to write to GCS bucket
resource "google_storage_bucket_iam_member" "bucket_iam_logging" {
  bucket = var.logging_bucket_name
  role = "roles/storage.objectCreator"
  member = google_logging_project_sink.cloud_run_sink.writer_identity
}
