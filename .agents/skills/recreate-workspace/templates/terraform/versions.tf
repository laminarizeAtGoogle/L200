terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
  }

  # Uncomment to use Google Cloud Storage as a remote backend
  # backend "gcs" {
  #   bucket = "YOUR_ARGOLIS_TFSTATE_BUCKET_NAME"
  #   prefix = "terraform/state"
  # }
}
