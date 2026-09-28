variable "project_id" {
  description = "The target Argolis GCP project ID"
  type        = string
}

variable "region" {
  description = "Default GCP region for regional resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Default GCP zone for zonal compute resources"
  type        = string
  default     = "us-central1-a"
}

variable "factory_service_name" {
  description = "Name of the A2A Software Factory Cloud Run service"
  type        = string
  default     = "a2a-software-factory"
}

variable "factory_container_image" {
  description = "Container image URI for the A2A Software Factory service"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "planning_model" {
  description = "Gemini model used for architectural planning and code synthesis"
  type        = string
  default     = "gemini-2.5-pro"
}

variable "fast_model" {
  description = "Gemini model used for fast read-only gcloud probes and log analysis"
  type        = string
  default     = "gemini-2.5-flash"
}
