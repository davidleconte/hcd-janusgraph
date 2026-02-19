# GCP Development Environment
# JanusGraph Banking Platform on Google GKE

terraform {
  required_version = ">= 1.5.0"

  backend "gcs" {
    bucket = "janusgraph-terraform-state"
    prefix = "gcp-dev"
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
  cluster_ca_certificate = base64decode(module.cluster.gcp_cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = "https://${module.cluster.cluster_endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(module.cluster.gcp_cluster_ca_certificate)
  }
}

# Data Sources
data "google_client_config" "default" {}

# Local Variables
locals {
  environment  = "dev"
  cluster_name = "janusgraph-banking-gcp-dev"
  region       = "us-central1"
  zones        = ["us-central1-a", "us-central1-b", "us-central1-c"]

  common_tags = {
    environment = "dev"
    project     = "janusgraph-banking"
    managed_by  = "terraform"
    cloud       = "gcp"
  }
}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  cluster_name       = local.cluster_name
  environment        = local.environment
  cloud_provider     = "gcp"
  vpc_cidr           = "10.2.0.0/16"
  availability_zones = local.zones

  # GCP-specific
  gcp_project_id = var.gcp_project_id
  gcp_region     = local.region

  tags = local.common_tags
}

# Cluster Module
module "cluster" {
  source = "../../modules/openshift-cluster"

  cluster_name       = local.cluster_name
  environment        = local.environment
  cloud_provider     = "gcp"
  kubernetes_version = "1.28"

  # Node configuration
  node_count     = 3
  node_count_min = 3
  node_count_max = 6

  # GCP-specific
  gcp_project_id     = var.gcp_project_id
  gcp_region         = local.region
  gcp_zones          = local.zones
  gcp_network        = module.networking.vpc_id
  gcp_subnetwork     = module.networking.private_subnet_ids[0]
  gcp_pod_cidr       = "10.4.0.0/14"
  gcp_service_cidr   = "10.8.0.0/20"
  gcp_master_cidr    = "172.16.0.0/28"
  gcp_machine_type   = "n2-standard-4"
  gcp_hcd_machine_type = "n2-highmem-8"

  # Master authorized networks (allow from anywhere for dev)
  gcp_master_authorized_networks = [
    {
      cidr_block   = "0.0.0.0/0"
      display_name = "All"
    }
  ]

  # Logging
  log_retention_days = 7

  tags = local.common_tags

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

  # Backup configuration
  backup_retention_days   = 7
  snapshot_retention_days = 3

  tags = local.common_tags

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

  tags = local.common_tags

  depends_on = [module.cluster]
}