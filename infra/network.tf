resource "google_compute_subnetwork" "default" {
  name                     = "default"
  region                   = local.region
  network                  = "default"
  ip_cidr_range            = "10.128.0.0/20"
  private_ip_google_access = true
}