# ==============================================================================
# A2A Agent Graph Software Factory - Argolis GCP Infrastructure
# ==============================================================================

locals {
  required_apis = toset([
    "aiplatform.googleapis.com",
    "cloudasset.googleapis.com",
    "cloudtrace.googleapis.com",
    "compute.googleapis.com",
    "dlp.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "iap.googleapis.com",
    "logging.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "sts.googleapis.com",
    "texttospeech.googleapis.com",
  ])
}

resource "google_project_service" "factory_apis" {
  for_each           = local.required_apis
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# ------------------------------------------------------------------------------
# 1. Dedicated Runtime Service Account & Least-Privilege IAM
# ------------------------------------------------------------------------------
resource "google_service_account" "software_factory_runtime" {
  project      = var.project_id
  account_id   = "a2a-software-factory-sa"
  display_name = "Gemini Enterprise Cloud Chat Runtime Service Account"
  description  = "Executes the GE Cloud Chat Agent, TTS voice engine, and read-only GCP inspection"
  depends_on   = [google_project_service.factory_apis]
}

resource "google_project_iam_member" "factory_runtime_roles" {
  for_each = var.manage_project_iam ? toset([
    "roles/aiplatform.user",
    "roles/cloudtrace.agent",
    "roles/compute.viewer",
    "roles/dlp.user",
    "roles/logging.logWriter",
    "roles/logging.viewer",
    "roles/run.viewer",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectViewer",
  ]) : toset([])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.software_factory_runtime.email}"
}

# ------------------------------------------------------------------------------
# 2. Google Cloud Secret Manager (Zero Hardcoded Credentials)
# ------------------------------------------------------------------------------
resource "google_secret_manager_secret" "factory_github_oauth_token" {
  project   = var.project_id
  secret_id = "software-factory-github-token"

  replication {
    auto {}
  }

  labels = {
    managed_by = "terraform"
    component  = "a2a-software-factory"
  }

  depends_on = [google_project_service.factory_apis]
}

resource "google_secret_manager_secret" "factory_webhook_signing_secret" {
  project   = var.project_id
  secret_id = "software-factory-webhook-secret"

  replication {
    auto {}
  }

  labels = {
    managed_by = "terraform"
    component  = "a2a-software-factory"
  }

  depends_on = [google_project_service.factory_apis]
}

# ------------------------------------------------------------------------------
# 3. Persistent Agent Memory & Evaluation Artifact Storage
# ------------------------------------------------------------------------------
resource "google_storage_bucket" "factory_memory_artifacts" {
  project                     = var.project_id
  name                        = "${var.project_id}-a2a-factory-memory"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }

  labels = {
    managed_by = "terraform"
    component  = "a2a-software-factory"
  }

  depends_on = [google_project_service.factory_apis]
}

resource "google_storage_bucket_iam_member" "factory_memory_bucket_writer" {
  bucket = google_storage_bucket.factory_memory_artifacts.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.software_factory_runtime.email}"
}

# ------------------------------------------------------------------------------
# 4. Isolated VPC Network, Subnet & Security Firewall Rules
# ------------------------------------------------------------------------------
resource "google_compute_network" "factory_vpc" {
  project                 = var.project_id
  name                    = "a2a-factory-vpc"
  auto_create_subnetworks = false
  description             = "Isolated VPC network for A2A Software Factory workloads"
  depends_on              = [google_project_service.factory_apis]
}

resource "google_compute_subnetwork" "factory_subnet" {
  project                  = var.project_id
  name                     = "a2a-factory-subnet-${var.region}"
  ip_cidr_range            = "10.20.0.0/24"
  region                   = var.region
  network                  = google_compute_network.factory_vpc.id
  private_ip_google_access = true
}

resource "google_compute_firewall" "allow_iap_ssh" {
  project     = var.project_id
  name        = "a2a-factory-allow-iap-ssh"
  network     = google_compute_network.factory_vpc.name
  description = "Allow SSH ingress strictly from Google Identity-Aware Proxy (IAP)"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["a2a-factory-vm"]
}

# ------------------------------------------------------------------------------
# 5. Cloud Run v2 Service: Unified FastAPI + A2A Agent Graph Endpoint
# ------------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "a2a_software_factory" {
  project  = var.project_id
  name     = var.factory_service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.software_factory_runtime.email

    containers {
      image = var.factory_container_image

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }
      env {
        name  = "FACTORY_PLANNING_MODEL"
        value = var.planning_model
      }
      env {
        name  = "FACTORY_FAST_MODEL"
        value = var.fast_model
      }
      env {
        name  = "FACTORY_CHAT_MODEL"
        value = "gemini-3.8-flash"
      }
      env {
        name  = "FACTORY_TTS_VOICE"
        value = "en-US-Journey-F"
      }
      env {
        name  = "IAP_ENFORCE"
        value = "true"
      }
      env {
        name  = "FACTORY_READONLY_SA"
        value = "cloudtop-agent-reader@${var.project_id}.iam.gserviceaccount.com"
      }
    }
  }

  depends_on = [google_project_service.factory_apis]
}
