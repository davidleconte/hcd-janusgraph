# GCP Networking Implementation
# Part of multi-cloud networking module

# ============================================================================
# VPC Network
# ============================================================================

resource "google_compute_network" "main" {
  count                   = var.cloud_provider == "gcp" ? 1 : 0
  name                    = "${var.cluster_name}-vpc"
  project                 = var.gcp_project_id
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"

  description = "VPC network for ${var.cluster_name}"
}

# ============================================================================
# Public Subnets
# ============================================================================

resource "google_compute_subnetwork" "public" {
  count         = var.cloud_provider == "gcp" ? length(var.availability_zones) : 0
  name          = "${var.cluster_name}-public-${count.index}"
  project       = var.gcp_project_id
  region        = var.gcp_region
  network       = google_compute_network.main[0].id
  ip_cidr_range = cidrsubnet(var.vpc_cidr, 4, count.index)

  # Secondary IP ranges for GKE pods and services
  secondary_ip_range {
    range_name    = "pods-${count.index}"
    ip_cidr_range = cidrsubnet(var.gcp_pod_cidr, 4, count.index)
  }

  secondary_ip_range {
    range_name    = "services-${count.index}"
    ip_cidr_range = cidrsubnet(var.gcp_service_cidr, 4, count.index)
  }

  # Enable private Google access
  private_ip_google_access = true

  # Enable flow logs
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }

  description = "Public subnet ${count.index} for ${var.cluster_name}"
}

# ============================================================================
# Private Subnets
# ============================================================================

resource "google_compute_subnetwork" "private" {
  count         = var.cloud_provider == "gcp" ? length(var.availability_zones) : 0
  name          = "${var.cluster_name}-private-${count.index}"
  project       = var.gcp_project_id
  region        = var.gcp_region
  network       = google_compute_network.main[0].id
  ip_cidr_range = cidrsubnet(var.vpc_cidr, 4, count.index + length(var.availability_zones))

  # Secondary IP ranges for GKE pods and services
  secondary_ip_range {
    range_name    = "pods-private-${count.index}"
    ip_cidr_range = cidrsubnet(var.gcp_pod_cidr, 4, count.index + length(var.availability_zones))
  }

  secondary_ip_range {
    range_name    = "services-private-${count.index}"
    ip_cidr_range = cidrsubnet(var.gcp_service_cidr, 4, count.index + length(var.availability_zones))
  }

  # Enable private Google access
  private_ip_google_access = true

  # Enable flow logs
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }

  description = "Private subnet ${count.index} for ${var.cluster_name}"
}

# ============================================================================
# Cloud Router (for Cloud NAT)
# ============================================================================

resource "google_compute_router" "main" {
  count   = var.cloud_provider == "gcp" && var.enable_nat_gateway ? 1 : 0
  name    = "${var.cluster_name}-router"
  project = var.gcp_project_id
  region  = var.gcp_region
  network = google_compute_network.main[0].id

  bgp {
    asn = 64514
  }

  description = "Cloud Router for ${var.cluster_name}"
}

# ============================================================================
# Cloud NAT
# ============================================================================

resource "google_compute_router_nat" "main" {
  count  = var.cloud_provider == "gcp" && var.enable_nat_gateway ? 1 : 0
  name   = "${var.cluster_name}-nat"
  router = google_compute_router.main[0].name
  region = var.gcp_region

  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  # Logging configuration
  log_config {
    enable = var.enable_flow_logs
    filter = "ERRORS_ONLY"
  }

  # Minimum ports per VM
  min_ports_per_vm = 64

  # Enable endpoint independent mapping
  enable_endpoint_independent_mapping = true
}

# ============================================================================
# Firewall Rules
# ============================================================================

# Allow internal traffic
resource "google_compute_firewall" "allow_internal" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  name    = "${var.cluster_name}-allow-internal"
  project = var.gcp_project_id
  network = google_compute_network.main[0].name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = [var.vpc_cidr]

  description = "Allow internal traffic within VPC"
}

# Allow SSH from IAP
resource "google_compute_firewall" "allow_iap_ssh" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  name    = "${var.cluster_name}-allow-iap-ssh"
  project = var.gcp_project_id
  network = google_compute_network.main[0].name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  # IAP IP range
  source_ranges = ["35.235.240.0/20"]

  description = "Allow SSH from Identity-Aware Proxy"
}

# Allow health checks
resource "google_compute_firewall" "allow_health_checks" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  name    = "${var.cluster_name}-allow-health-checks"
  project = var.gcp_project_id
  network = google_compute_network.main[0].name

  allow {
    protocol = "tcp"
  }

  # Google Cloud health check IP ranges
  source_ranges = [
    "35.191.0.0/16",
    "130.211.0.0/22"
  ]

  description = "Allow health checks from Google Cloud"
}

# Allow HTTP/HTTPS
resource "google_compute_firewall" "allow_http_https" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  name    = "${var.cluster_name}-allow-http-https"
  project = var.gcp_project_id
  network = google_compute_network.main[0].name

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http-server", "https-server"]

  description = "Allow HTTP and HTTPS traffic"
}

# ============================================================================
# Global Load Balancer Components
# ============================================================================

# Global static IP for load balancer
resource "google_compute_global_address" "lb" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  name    = "${var.cluster_name}-lb-ip"
  project = var.gcp_project_id

  description = "Global static IP for ${var.cluster_name} load balancer"
}

# Health check for backend services
resource "google_compute_health_check" "http" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  name    = "${var.cluster_name}-http-health-check"
  project = var.gcp_project_id

  http_health_check {
    port         = 80
    request_path = "/healthz"
  }

  check_interval_sec  = 10
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3

  description = "HTTP health check for ${var.cluster_name}"
}

# ============================================================================
# Private Service Connection (for Google Services)
# ============================================================================

# Reserve IP range for private service connection
resource "google_compute_global_address" "private_service_connection" {
  count         = var.cloud_provider == "gcp" && var.enable_vpc_endpoints ? 1 : 0
  name          = "${var.cluster_name}-private-service-connection"
  project       = var.gcp_project_id
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main[0].id

  description = "IP range for private service connection"
}

# Private VPC connection
resource "google_service_networking_connection" "private_vpc_connection" {
  count                   = var.cloud_provider == "gcp" && var.enable_vpc_endpoints ? 1 : 0
  network                 = google_compute_network.main[0].id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_connection[0].name]
}

# ============================================================================
# Cloud DNS (Private Zone)
# ============================================================================

resource "google_dns_managed_zone" "private" {
  count       = var.cloud_provider == "gcp" ? 1 : 0
  name        = "${var.cluster_name}-private-zone"
  project     = var.gcp_project_id
  dns_name    = "${var.cluster_name}.internal."
  description = "Private DNS zone for ${var.cluster_name}"
  visibility  = "private"

  private_visibility_config {
    networks {
      network_url = google_compute_network.main[0].id
    }
  }
}

# ============================================================================
# VPC Flow Logs (via Logging Sink)
# ============================================================================

resource "google_logging_project_sink" "vpc_flow_logs" {
  count       = var.cloud_provider == "gcp" && var.enable_flow_logs ? 1 : 0
  name        = "${var.cluster_name}-vpc-flow-logs"
  project     = var.gcp_project_id
  destination = "storage.googleapis.com/${var.gcp_flow_logs_bucket}"

  filter = <<-EOT
    resource.type="gce_subnetwork"
    logName="projects/${var.gcp_project_id}/logs/compute.googleapis.com%2Fvpc_flows"
  EOT

  unique_writer_identity = true
}

# ============================================================================
# Network Tags (for firewall rules)
# ============================================================================

locals {
  gcp_network_tags = var.cloud_provider == "gcp" ? {
    cluster_name = var.cluster_name
    environment  = var.environment
    managed_by   = "terraform"
  } : {}
}

# ============================================================================
# Routes (Custom routes if needed)
# ============================================================================

# Default route to internet gateway (automatically created by GCP)
# Custom routes can be added here if needed

# ============================================================================
# Network Peering (for multi-region or hybrid setups)
# ============================================================================

# Network peering resources can be added here for hybrid deployments
# Example: Peering with on-premises networks via Cloud Interconnect or VPN