# Azure Development Environment
# JanusGraph Banking Platform on Azure AKS

terraform {
  required_version = ">= 1.5.0"

  backend "azurerm" {
    resource_group_name  = "janusgraph-terraform-state"
    storage_account_name = "janusgraphterraform"
    container_name       = "tfstate"
    key                  = "azure-dev.terraform.tfstate"
  }
}

# Provider Configuration
provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

provider "kubernetes" {
  host                   = module.cluster.cluster_endpoint
  cluster_ca_certificate = base64decode(module.cluster.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "kubelogin"
    args = [
      "get-token",
      "--environment",
      "AzurePublicCloud",
      "--server-id",
      "6dae42f8-4368-4678-94ff-3960e28e3630", # Azure Kubernetes Service AAD Server
      "--client-id",
      var.azure_client_id,
      "--tenant-id",
      var.azure_tenant_id
    ]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.cluster.cluster_endpoint
    cluster_ca_certificate = base64decode(module.cluster.cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "kubelogin"
      args = [
        "get-token",
        "--environment",
        "AzurePublicCloud",
        "--server-id",
        "6dae42f8-4368-4678-94ff-3960e28e3630",
        "--client-id",
        var.azure_client_id,
        "--tenant-id",
        var.azure_tenant_id
      ]
    }
  }
}

# Local Variables
locals {
  environment  = "dev"
  cluster_name = "janusgraph-banking-azure-dev"
  region       = "eastus"

  common_tags = {
    Environment = "dev"
    Project     = "janusgraph-banking"
    ManagedBy   = "terraform"
    Cloud       = "azure"
  }
}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  cluster_name     = local.cluster_name
  environment      = local.environment
  cloud_provider   = "azure"
  vpc_cidr         = "10.1.0.0/16"
  availability_zones = ["1", "2", "3"]

  # Azure-specific
  azure_region = local.region

  tags = local.common_tags
}

# Cluster Module
module "cluster" {
  source = "../../modules/openshift-cluster"

  cluster_name       = local.cluster_name
  environment        = local.environment
  cloud_provider     = "azure"
  kubernetes_version = "1.28"

  # Node configuration
  node_count     = 3
  node_count_min = 3
  node_count_max = 6

  # Azure-specific
  azure_region        = local.region
  azure_vm_size       = "Standard_D4s_v3"
  azure_hcd_vm_size   = "Standard_E8s_v3"
  azure_subnet_id     = module.networking.private_subnet_ids[0]
  azure_dns_service_ip = "10.0.0.10"
  azure_service_cidr   = "10.0.0.0/16"
  azure_admin_group_ids = var.azure_admin_group_ids

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
  cloud_provider = "azure"

  # Azure-specific
  azure_region            = local.region
  azure_resource_group_name = module.cluster.azure_resource_group_name

  # Backup configuration
  backup_retention_days = 7
  snapshot_retention_days = 3

  tags = local.common_tags

  depends_on = [module.cluster]
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"

  cluster_name   = local.cluster_name
  environment    = local.environment
  cloud_provider = "azure"

  # Monitoring configuration
  enable_prometheus = true
  enable_grafana    = true
  enable_loki       = true

  # Azure-specific
  azure_log_analytics_workspace_id = module.cluster.azure_log_analytics_workspace_id

  tags = local.common_tags

  depends_on = [module.cluster]
}