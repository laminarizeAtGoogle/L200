variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "Default GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Default GCP zone for compute resources"
  type        = string
  default     = "us-central1-a"
}
