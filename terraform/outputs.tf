output "software_factory_service_url" {
  description = "URI of the deployed A2A Software Factory Cloud Run v2 service"
  value       = google_cloud_run_v2_service.a2a_software_factory.uri
}

output "software_factory_runtime_sa_email" {
  description = "Email of the least-privilege A2A Software Factory runtime Service Account"
  value       = google_service_account.software_factory_runtime.email
}

output "factory_memory_bucket_name" {
  description = "GCS bucket storing persistent agent memories and evaluation artifacts"
  value       = google_storage_bucket.factory_memory_artifacts.name
}

output "factory_vpc_name" {
  description = "Name of the isolated VPC network"
  value       = google_compute_network.factory_vpc.name
}

output "secret_manager_github_token_id" {
  description = "Secret Manager resource ID for the GitHub OAuth token"
  value       = google_secret_manager_secret.factory_github_oauth_token.id
}
