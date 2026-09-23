# Service Account for the Argolis Compute Engine instance
resource "google_service_account" "argolis_sa" {
  account_id   = "${var.instance_name}-sa"
  display_name = "Service Account for ${var.instance_name}"
}

# Compute Engine Instance
resource "google_compute_instance" "argolis_instance" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  tags = var.tags

  boot_disk {
    initialize_params {
      image = var.boot_disk_image
      size  = var.boot_disk_size_gb
    }
  }

  network_interface {
    network = var.network

    access_config {
      // Ephemeral public IP
    }
  }

  service_account {
    email  = google_service_account.argolis_sa.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    enable-oslogin = "TRUE"
  }

  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  allow_stopping_for_update = true
}
