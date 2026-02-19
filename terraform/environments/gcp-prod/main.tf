# GCP Production Environment
# JanusGraph Banking Platform on Google Kubernetes Engine (GKE)

terraform {
  required_version = ">= 1.5.0"

  backend "gcs" {
    bucket = "janusgraph-terraform-state"
    prefix = "gcp-prod"
  }
}

# Provider Configuration
provider "google" {
  project = var.gcp_project_id
  region  = local.region
}

provider "kubernetes" {
  host                   = "https://${module.cluster.cluster_endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.cluster.cluster_certificate_authority_data)
}

provider "helm" {
  kubernetes {
    host                   = "https://${module.cluster.cluster_endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(module.cluster.cluster_certificate_authority_data)
  }
}

# Data Sources
data "google_client_config" "default" {}

# Local Variables
locals {
  environment  = "production"
  cluster_name = "janusgraph-banking-gcp-prod"
  region       = "us-east1"
  zones        = ["us-east1-b", "us-east1-c", "us-east1-d"]

  common_labels = {
    environment = "production"
    project     = "janusgraph-banking"
    managed_by  = "terraform"
    cloud       = "gcp"
    cost_center = "production"
    owner       = "platform-team"
    compliance  = "pci-dss-sox-gdpr"
    criticality = "high"
  }
}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  cluster_name       = local.cluster_name
  environment        = local.environment
  cloud_provider     = "gcp"
  vpc_cidr           = "10.40.0.0/16"
  availability_zones = local.zones

  # GCP-specific
  gcp_project_id = var.gcp_project_id
  gcp_region     = local.region

  # Secondary IP ranges for GKE
  gcp_pods_cidr     = "10.44.0.0/14"
  gcp_services_cidr = "10.48.0.0/20"

  # Enable flow logs for production
  enable_flow_logs = true

  tags = local.common_labels
}

# Cluster Module
module "cluster" {
  source = "../../modules/openshift-cluster"

  cluster_name       = local.cluster_name
  environment        = local.environment
  cloud_provider     = "gcp"
  kubernetes_version = "1.28"

  # Node configuration - Production sized
  node_count     = 10
  node_count_min = 10
  node_count_max = 20

  # GCP-specific - Production machines
  gcp_project_id       = var.gcp_project_id
  gcp_region           = local.region
  gcp_zones            = local.zones
  gcp_machine_type     = "n2-standard-16"  # 16 vCPU, 64 GB RAM
  gcp_hcd_machine_type = "n2-highmem-32"   # 32 vCPU, 256 GB RAM
  gcp_network          = module.networking.vpc_id
  gcp_subnetwork       = module.networking.private_subnet_ids[0]

  # Logging - Extended retention for production
  log_retention_days = 90

  tags = local.common_labels

  depends_on = [module.networking]
}

# Storage Module
module "storage" {
  source = "../../modules/storage"

  cluster_name   = local.cluster_name
  environment    = local.environment
  cloud_provider = "gcp"

  # GCP-specific
  gcp_project_id = var.gcp_project_id
  gcp_region     = local.region

  # Storage configuration - SSD for production
  gcp_hcd_disk_type        = "pd-ssd"
  gcp_janusgraph_disk_type = "pd-ssd"
  gcp_opensearch_disk_type = "pd-ssd"
  gcp_pulsar_disk_type     = "pd-ssd"

  # Backup configuration - Extended retention for production
  backup_retention_days   = 90
  snapshot_retention_days = 30
  backup_transition_days  = 7

  tags = local.common_labels

  depends_on = [module.cluster]
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"

  cluster_name   = local.cluster_name
  environment    = local.environment
  cloud_provider = "gcp"

  # Monitoring configuration
  enable_prometheus = true
  enable_grafana    = true
  enable_loki       = true

  # GCP-specific
  gcp_project_id = var.gcp_project_id

  tags = local.common_labels

  depends_on = [module.cluster]
}

# Cloud Logging Sink for GKE - Production retention
resource "google_logging_project_sink" "gke_logs" {
  name        = "${local.cluster_name}-gke-logs"
  destination = "storage.googleapis.com/${google_storage_bucket.logs.name}"
  filter      = "resource.type=k8s_cluster AND resource.labels.cluster_name=${local.cluster_name}"

  unique_writer_identity = true
}

# Storage Bucket for Logs - Multi-regional for production
resource "google_storage_bucket" "logs" {
  name          = "${local.cluster_name}-logs"
  location      = "US"
  force_destroy = false

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  versioning {
    enabled = true
  }

  labels = local.common_labels
}

# IAM binding for log sink
resource "google_storage_bucket_iam_member" "log_writer" {
  bucket = google_storage_bucket.logs.name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.gke_logs.writer_identity
}

# Cloud Monitoring Alert Policies
resource "google_monitoring_alert_policy" "cpu_high" {
  display_name = "${local.cluster_name}-cpu-high"
  combiner     = "OR"

  conditions {
    display_name = "CPU usage high"

    condition_threshold {
      filter          = "resource.type=\"k8s_node\" AND resource.labels.cluster_name=\"${local.cluster_name}\" AND metric.type=\"kubernetes.io/node/cpu/allocatable_utilization\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]

  alert_strategy {
    auto_close = "1800s"
  }
}

resource "google_monitoring_alert_policy" "memory_high" {
  display_name = "${local.cluster_name}-memory-high"
  combiner     = "OR"

  conditions {
    display_name = "Memory usage high"

    condition_threshold {
      filter          = "resource.type=\"k8s_node\" AND resource.labels.cluster_name=\"${local.cluster_name}\" AND metric.type=\"kubernetes.io/node/memory/allocatable_utilization\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]

  alert_strategy {
    auto_close = "1800s"
  }
}

resource "google_monitoring_notification_channel" "email" {
  display_name = "Platform Team Email"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }
}

# Binary Authorization Policy for Production
resource "google_binary_authorization_policy" "policy" {
  admission_whitelist_patterns {
    name_pattern = "gcr.io/${var.gcp_project_id}/*"
  }

  default_admission_rule {
    evaluation_mode  = "REQUIRE_ATTESTATION"
    enforcement_mode = "ENFORCED_BLOCK_AND_AUDIT_LOG"

    require_attestations_by = [
      google_binary_authorization_attestor.attestor.name
    ]
  }

  global_policy_evaluation_mode = "ENABLE"
}

resource "google_binary_authorization_attestor" "attestor" {
  name = "${local.cluster_name}-attestor"

  attestation_authority_note {
    note_reference = google_container_analysis_note.note.name
  }
}

resource "google_container_analysis_note" "note" {
  name = "${local.cluster_name}-attestor-note"

  attestation_authority {
    hint {
      human_readable_name = "Production attestor"
    }
  }
}

# Disaster Recovery - Cross-region backup bucket
resource "google_storage_bucket" "dr_backups" {
  name          = "${local.cluster_name}-dr-backups"
  location      = "US-WEST1"
  force_destroy = false

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  versioning {
    enabled = true
  }

  labels = merge(local.common_labels, {
    purpose = "disaster-recovery"
  })
}

# Outputs
output "cluster_name" {
  description = "Name of the GKE cluster"
  value       = module.cluster.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint for the GKE cluster"
  value       = module.cluster.cluster_endpoint
  sensitive   = true
}

output "project_id" {
  description = "GCP project ID"
  value       = var.gcp_project_id
}

output "region" {
  description = "GCP region"
  value       = local.region
}

output "log_bucket" {
  description = "Cloud Storage bucket for logs"
  value       = google_storage_bucket.logs.name
}

output "dr_backup_bucket" {
  description = "Cloud Storage bucket for DR backups"
  value       = google_storage_bucket.dr_backups.name
}

output "kubeconfig_command" {
  description = "Command to get kubeconfig"
  value       = "gcloud container clusters get-credentials ${local.cluster_name} --region ${local.region} --project ${var.gcp_project_id}"
}