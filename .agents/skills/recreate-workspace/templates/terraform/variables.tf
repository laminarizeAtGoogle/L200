variable "project_id" {
  description = "The GCP project ID (Argolis demo project)"
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

variable "instance_name" {
  description = "Name for the Argolis Compute Engine instance"
  type        = string
  default     = "argolis-dev-vm"
}

variable "machine_type" {
  description = "Machine type for the Compute Engine instance"
  type        = string
  default     = "e2-standard-4"
}

variable "boot_disk_image" {
  description = "OS boot disk image for the instance"
  type        = string
  default     = "debian-cloud/debian-12"
}

variable "boot_disk_size_gb" {
  description = "Boot disk size in GB"
  type        = number
  default     = 50
}

variable "network" {
  description = "VPC network to attach the instance to"
  type        = string
  default     = "default"
}

variable "tags" {
  description = "Network tags to apply to the instance"
  type        = list(string)
  default     = ["argolis-dev", "http-server", "https-server"]
}
