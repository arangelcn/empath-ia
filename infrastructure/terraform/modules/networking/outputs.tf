output "network_name" {
  value = google_compute_network.vpc.name
}

output "network_self_link" {
  value = google_compute_network.vpc.self_link
}

output "subnetwork_name" {
  value = google_compute_subnetwork.main.name
}

output "subnetwork_self_link" {
  value = google_compute_subnetwork.main.self_link
}

output "pods_range_name" {
  value = "pods"
}

output "services_range_name" {
  value = "services"
}
