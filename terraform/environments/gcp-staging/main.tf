# GCP Staging Environment
# JanusGraph Banking Platform on Google Kubernetes Engine (GKE)

terraform {
  required_version = ">= 1.5.0"

  backend "gcs" {
    bucket = "janusgraph-terraform-state"
    prefix = "gcp-staging"
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
  environment  = "staging"
  cluster_name = "janusgraph-banking-gcp-staging"
  region       = "us-east1"
  zones        = ["us-east1-b", "us-east1-c", "us-east1-d"]

  common_labels = {
    environment = "staging"
    project     = "janusgraph-banking"
    managed_by  = "terraform"
    cloud       = "gcp"
    cost_center = "engineering"
    owner       = "platform-team"
  }
}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  cluster_name       = local.cluster_name
  environment        = local.environment
  cloud_provider     = "gcp"
  vpc_cidr           = "10.30.0.0/16"
  availability_zones = local.zones

  # GCP-specific
  gcp_project_id = var.gcp_project_id
  gcp_region     = local.region

  # Secondary IP ranges for GKE
  gcp_pods_cidr     = "10.32.0.0/14"
  gcp_services_cidr = "10.36.0.0/20"

  # Enable flow logs for staging
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

  # Node configuration - Staging sized
  node_count     = 5
  node_count_min = 5
  node_count_max = 10

  # GCP-specific - Larger machines for staging
  gcp_project_id     = var.gcp_project_id
  gcp_region         = local.region
  gcp_zones          = local.zones
  gcp_machine_type   = "n2-standard-8"   # 8 vCPU, 32 GB RAM
  gcp_hcd_machine_type = "n2-highmem-16" # 16 vCPU, 128 GB RAM
  gcp_network        = module.networking.vpc_id
  gcp_subnetwork     = module.networking.private_subnet_ids[0]

  # Logging - Extended retention for staging
  log_retention_days = 30

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

  # Storage configuration - SSD for staging
  gcp_hcd_disk_type        = "pd-ssd"
  gcp_janusgraph_disk_type = "pd-ssd"
  gcp_opensearch_disk_type = "pd-balanced"
  gcp_pulsar_disk_type     = "pd-balanced"

  # Backup configuration - Extended retention
  backup_retention_days   = 14
  snapshot_retention_days = 7
  backup_transition_days  = 3

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

# Cloud Logging Sink for GKE
resource "google_logging_project_sink" "gke_logs" {
  name        = "${local.cluster_name}-gke-logs"
  destination = "storage.googleapis.com/${google_storage_bucket.logs.name}"
  filter      = "resource.type=k8s_cluster AND resource.labels.cluster_name=${local.cluster_name}"

  unique_writer_identity = true
}

# Storage Bucket for Logs
resource "google_storage_bucket" "logs" {
  name          = "${local.cluster_name}-logs"
  location      = local.region
  force_destroy = false

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  labels = local.common_labels
}

# IAM binding for log sink
resource "google_storage_bucket_iam_member" "log_writer" {
  bucket = google_storage_bucket.logs.name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.gke_logs.writer_identity
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

output "kubeconfig_command" {
  description = "Command to get kubeconfig"
  value       = "gcloud container clusters get-credentials ${local.cluster_name} --region ${local.region} --project ${var.gcp_project_id}"
}