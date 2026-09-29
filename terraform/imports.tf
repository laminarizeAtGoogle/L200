# ==============================================================================
# Terraform 1.5+ Declarative Resource Import Blocks
# Adopts existing Argolis cloud assets created during initial provisioning runs
# into the remote GCS state, preventing 409 Conflict errors.
# ==============================================================================

import {
  to = google_service_account.software_factory_runtime
  id = "projects/${var.project_id}/serviceAccounts/a2a-software-factory-sa@${var.project_id}.iam.gserviceaccount.com"
}

import {
  to = google_secret_manager_secret.factory_github_oauth_token
  id = "projects/${var.project_id}/secrets/software-factory-github-token"
}

import {
  to = google_secret_manager_secret.factory_webhook_signing_secret
  id = "projects/${var.project_id}/secrets/software-factory-webhook-secret"
}

import {
  to = google_storage_bucket.factory_memory_artifacts
  id = "${var.project_id}-a2a-factory-memory"
}

import {
  to = google_storage_bucket_iam_member.factory_memory_bucket_writer
  id = "b/${var.project_id}-a2a-factory-memory roles/storage.objectAdmin serviceAccount:a2a-software-factory-sa@${var.project_id}.iam.gserviceaccount.com"
}

import {
  to = google_compute_network.factory_vpc
  id = "projects/${var.project_id}/global/networks/a2a-factory-vpc"
}

import {
  to = google_compute_subnetwork.factory_subnet
  id = "projects/${var.project_id}/regions/${var.region}/subnetworks/a2a-factory-subnet-${var.region}"
}

import {
  to = google_compute_firewall.allow_iap_ssh
  id = "projects/${var.project_id}/global/firewalls/a2a-factory-allow-iap-ssh"
}

import {
  to = google_cloud_run_v2_service.a2a_software_factory
  id = "projects/${var.project_id}/locations/${var.region}/services/${var.factory_service_name}"
}
