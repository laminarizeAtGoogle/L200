output "instance_name" {
  description = "The name of the deployed Argolis Compute Engine instance"
  value       = google_compute_instance.argolis_instance.name
}

output "instance_zone" {
  description = "The zone of the deployed instance"
  value       = google_compute_instance.argolis_instance.zone
}

output "internal_ip" {
  description = "The internal IP address of the instance"
  value       = google_compute_instance.argolis_instance.network_interface[0].network_ip
}

output "external_ip" {
  description = "The public IP address of the instance"
  value       = try(google_compute_instance.argolis_instance.network_interface[0].access_config[0].nat_ip, null)
}

output "ssh_command" {
  description = "Quick gcloud command to SSH into the instance"
  value       = "gcloud compute ssh ${google_compute_instance.argolis_instance.name} --zone=${google_compute_instance.argolis_instance.zone} --project=${var.project_id}"
}
