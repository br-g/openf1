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
  sensitive   = true
}

variable "timeout" {
  type = string
  description = "Execution timeout"
  default = "840s" // 14 minutes
}

variable "google_credentials" {
  description = "GCP credentials (JSON)"
  type = string
  sensitive   = true
}

variable "bucket_api_raw" {
  description = "Bucket for storing raw F1 data"
  type = string
  sensitive = true
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
    bucket  = "openf1-tf-backend"
    prefix  = "terraform/state/ingestor"
    credentials = "./google_credentials.json"
  }
}

provider "google" {
  credentials = file("${var.credentials_path}")
  project     = var.gcp_project_id
  region      = var.gcp_region
}

data "google_client_config" "default" {}

provider "docker" {
  registry_auth {
    address  = "gcr.io"
    username = "oauth2accesstoken"
    password = data.google_client_config.default.access_token
  }
}


#==============#
# DOCKER IMAGE #
#==============#
data "docker_registry_image" "myapp" {
  name = "gcr.io/${var.gcp_project_id}/ingestor:latest"
}


#===========#
# CLOUD RUN #
#===========#

resource "google_cloud_run_v2_service" "default" {
  name = "ingestor"
  location = var.gcp_region

  template {
    service_account = google_service_account.sa.email
    containers {
      image = "${data.docker_registry_image.myapp.name}@${data.docker_registry_image.myapp.sha256_digest}"

      resources {
        limits = {
          cpu = "1000m"
          memory = "1Gi"
        }
        cpu_idle = true  # garbage-collect CPU once a request finishes
      }

      env {
        name  = "MONGO_CONNECTION_STRING"
        value = var.mongo_connection_string
      }
      env {
        name  = "GOOGLE_CREDENTIALS"
        value = var.google_credentials
      }
      env {
        name  = "BUCKET_API_RAW"
        value = var.bucket_api_raw
      }
    }
    max_instance_request_concurrency = 1
    timeout = var.timeout
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
  }
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
  account_id = "sa-ingestor"
  display_name = "sa-ingestor"
  project = var.gcp_project_id
}


#===========#
# SCHEDULER #
#===========#

resource "google_cloud_scheduler_job" "job" {
  name = "ingestor-scheduler"
  region = var.gcp_region
  project = var.gcp_project_id
  schedule = "*/5 * * * *"

  retry_config {
    retry_count = 0
  }

  http_target {
    http_method = "POST"
    uri = google_cloud_run_v2_service.default.uri
    body = ""
  }
}
