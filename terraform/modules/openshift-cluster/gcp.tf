# Google Kubernetes Engine (GKE) Implementation
# Part of multi-cloud cluster module

# GKE Cluster
resource "google_container_cluster" "main" {
  count    = var.cloud_provider == "gcp" ? 1 : 0
  name     = var.cluster_name
  location = var.gcp_region
  project  = var.gcp_project_id

  # Regional cluster (multi-zone by default)
  node_locations = var.gcp_zones

  # Remove default node pool (we'll create custom ones)
  remove_default_node_pool = true
  initial_node_count       = 1

  # Network configuration
  network    = var.gcp_network
  subnetwork = var.gcp_subnetwork

  # IP allocation policy for VPC-native cluster
  ip_allocation_policy {
    cluster_ipv4_cidr_block  = var.gcp_pod_cidr
    services_ipv4_cidr_block = var.gcp_service_cidr
  }

  # Master auth configuration
  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }

  # Workload Identity for GCP service account integration
  workload_identity_config {
    workload_pool = "${var.gcp_project_id}.svc.id.goog"
  }

  # Logging and monitoring
  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"

  # Addons
  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
    network_policy_config {
      disabled = false
    }
    gcp_filestore_csi_driver_config {
      enabled = true
    }
    gce_persistent_disk_csi_driver_config {
      enabled = true
    }
  }

  # Network policy
  network_policy {
    enabled  = true
    provider = "CALICO"
  }

  # Binary authorization
  binary_authorization {
    evaluation_mode = var.environment == "prod" ? "PROJECT_SINGLETON_POLICY_ENFORCE" : "DISABLED"
  }

  # Maintenance policy
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"
    }
  }

  # Release channel for auto-upgrades
  release_channel {
    channel = var.environment == "prod" ? "STABLE" : "REGULAR"
  }

  # Private cluster configuration
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.gcp_master_cidr
  }

  # Master authorized networks
  dynamic "master_authorized_networks_config" {
    for_each = var.gcp_master_authorized_networks != [] ? [1] : []
    content {
      dynamic "cidr_blocks" {
        for_each = var.gcp_master_authorized_networks
        content {
          cidr_block   = cidr_blocks.value.cidr_block
          display_name = cidr_blocks.value.display_name
        }
      }
    }
  }

  # Resource labels
  resource_labels = merge(
    local.common_tags,
    {
      "mesh_id" = "proj-${var.gcp_project_id}"
    }
  )

  # Lifecycle
  lifecycle {
    ignore_changes = [
      node_pool,
      initial_node_count
    ]
  }
}

# General purpose node pool
resource "google_container_node_pool" "general" {
  count      = var.cloud_provider == "gcp" ? 1 : 0
  name       = "general"
  location   = var.gcp_region
  cluster    = google_container_cluster.main[0].name
  node_count = var.node_count

  # Autoscaling
  autoscaling {
    min_node_count = var.node_count_min
    max_node_count = var.node_count_max
  }

  # Node configuration
  node_config {
    machine_type = var.gcp_machine_type
    disk_size_gb = var.disk_size
    disk_type    = "pd-ssd"
    image_type   = "COS_CONTAINERD"

    # OAuth scopes
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    # Labels
    labels = {
      role        = "general"
      environment = var.environment
      project     = "janusgraph-banking"
    }

    # Metadata
    metadata = {
      disable-legacy-endpoints = "true"
    }

    # Workload metadata config
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    # Shielded instance config
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    # Tags
    tags = ["gke-node", "${var.cluster_name}-node"]
  }

  # Management
  management {
    auto_repair  = true
    auto_upgrade = true
  }

  # Upgrade settings
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
}

# HCD node pool for Cassandra workloads
resource "google_container_node_pool" "hcd" {
  count      = var.cloud_provider == "gcp" ? 1 : 0
  name       = "hcd"
  location   = var.gcp_region
  cluster    = google_container_cluster.main[0].name
  node_count = 3

  # Autoscaling
  autoscaling {
    min_node_count = 3
    max_node_count = 6
  }

  # Node configuration
  node_config {
    machine_type = var.gcp_hcd_machine_type
    disk_size_gb = 500
    disk_type    = "pd-ssd"
    image_type   = "COS_CONTAINERD"

    # OAuth scopes
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    # Labels
    labels = {
      role        = "hcd"
      environment = var.environment
      project     = "janusgraph-banking"
    }

    # Taints
    taint {
      key    = "workload"
      value  = "hcd"
      effect = "NO_SCHEDULE"
    }

    # Metadata
    metadata = {
      disable-legacy-endpoints = "true"
    }

    # Workload metadata config
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    # Shielded instance config
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    # Local SSD for better performance
    local_ssd_count = 1

    # Tags
    tags = ["gke-node", "${var.cluster_name}-hcd-node"]
  }

  # Management
  management {
    auto_repair  = true
    auto_upgrade = true
  }

  # Upgrade settings
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
}

# Service Account for GKE nodes
resource "google_service_account" "gke_nodes" {
  count        = var.cloud_provider == "gcp" ? 1 : 0
  account_id   = "${var.cluster_name}-gke-nodes"
  display_name = "Service Account for GKE nodes in ${var.cluster_name}"
  project      = var.gcp_project_id
}

# IAM bindings for node service account
resource "google_project_iam_member" "gke_nodes_log_writer" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  project = var.gcp_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gke_nodes[0].email}"
}

resource "google_project_iam_member" "gke_nodes_metric_writer" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  project = var.gcp_project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gke_nodes[0].email}"
}

resource "google_project_iam_member" "gke_nodes_monitoring_viewer" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  project = var.gcp_project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.gke_nodes[0].email}"
}

# Firewall rule for health checks
resource "google_compute_firewall" "gke_health_checks" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  name    = "${var.cluster_name}-gke-health-checks"
  network = var.gcp_network
  project = var.gcp_project_id

  allow {
    protocol = "tcp"
    ports    = ["10256"]
  }

  source_ranges = [
    "35.191.0.0/16",
    "130.211.0.0/22"
  ]

  target_tags = ["gke-node"]
}