# Azure Production Environment
# JanusGraph Banking Platform on Azure AKS

terraform {
  required_version = ">= 1.5.0"

  backend "azurerm" {
    resource_group_name  = "janusgraph-terraform-state"
    storage_account_name = "janusgraphterraform"
    container_name       = "tfstate"
    key                  = "azure-prod.terraform.tfstate"
  }
}

# Provider Configuration
provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
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
  environment  = "production"
  cluster_name = "janusgraph-banking-azure-prod"
  region       = "eastus"

  common_tags = {
    Environment = "production"
    Project     = "janusgraph-banking"
    ManagedBy   = "terraform"
    Cloud       = "azure"
    CostCenter  = "production"
    Owner       = "platform-team"
    Compliance  = "pci-dss,sox,gdpr"
    Criticality = "high"
  }
}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  cluster_name       = local.cluster_name
  environment        = local.environment
  cloud_provider     = "azure"
  vpc_cidr           = "10.20.0.0/16"
  availability_zones = ["1", "2", "3"]

  # Azure-specific
  azure_region              = local.region
  azure_resource_group_name = azurerm_resource_group.main.name

  # Enable flow logs for production
  enable_flow_logs                        = true
  azure_network_watcher_name              = "NetworkWatcher_${local.region}"
  azure_network_watcher_rg                = "NetworkWatcherRG"
  azure_flow_logs_storage_account_id      = azurerm_storage_account.flow_logs.id
  azure_log_analytics_workspace_id        = azurerm_log_analytics_workspace.main.id
  azure_log_analytics_workspace_resource_id = azurerm_log_analytics_workspace.main.id
  flow_logs_retention_days                = 90

  tags = local.common_tags
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "${local.cluster_name}-rg"
  location = local.region
  tags     = local.common_tags
}

# Log Analytics Workspace - Production retention
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${local.cluster_name}-logs"
  location            = local.region
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 90

  tags = local.common_tags
}

# Storage Account for Flow Logs - GRS for production
resource "azurerm_storage_account" "flow_logs" {
  name                     = replace("${local.cluster_name}flowlogs", "-", "")
  resource_group_name      = azurerm_resource_group.main.name
  location                 = local.region
  account_tier             = "Standard"
  account_replication_type = "GRS"
  
  tags = local.common_tags
}

# Azure Policy Assignment for Compliance
resource "azurerm_resource_group_policy_assignment" "pci_dss" {
  name                 = "pci-dss-compliance"
  resource_group_id    = azurerm_resource_group.main.id
  policy_definition_id = "/providers/Microsoft.Authorization/policySetDefinitions/496eeda9-8f2f-4d5e-8dfd-204f0a92ed41"
  
  parameters = jsonencode({
    effect = {
      value = "Audit"
    }
  })
}

resource "azurerm_resource_group_policy_assignment" "cis_benchmark" {
  name                 = "cis-benchmark"
  resource_group_id    = azurerm_resource_group.main.id
  policy_definition_id = "/providers/Microsoft.Authorization/policySetDefinitions/06f19060-9e68-4070-92ca-f15cc126059e"
  
  parameters = jsonencode({
    effect = {
      value = "Audit"
    }
  })
}

# Cluster Module
module "cluster" {
  source = "../../modules/openshift-cluster"

  cluster_name       = local.cluster_name
  environment        = local.environment
  cloud_provider     = "azure"
  kubernetes_version = "1.28"

  # Node configuration - Production sized
  node_count     = 10
  node_count_min = 10
  node_count_max = 20

  # Azure-specific - Production VMs
  azure_region          = local.region
  azure_vm_size         = "Standard_D16s_v3"  # 16 vCPU, 64 GB RAM
  azure_hcd_vm_size     = "Standard_E32s_v3"  # 32 vCPU, 256 GB RAM
  azure_subnet_id       = module.networking.private_subnet_ids[0]
  azure_dns_service_ip  = "10.0.0.10"
  azure_service_cidr    = "10.0.0.0/16"
  azure_admin_group_ids = var.azure_admin_group_ids

  # Logging - Extended retention for production
  log_retention_days = 90

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
  azure_region              = local.region
  azure_resource_group_name = azurerm_resource_group.main.name

  # Storage configuration - Premium for production
  azure_hcd_disk_type        = "Premium_LRS"
  azure_janusgraph_disk_type = "Premium_LRS"
  azure_opensearch_disk_type = "Premium_LRS"
  azure_pulsar_disk_type     = "Premium_LRS"

  # Backup configuration - Extended retention for production
  backup_retention_days   = 90
  snapshot_retention_days = 30
  backup_transition_days  = 7

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
  azure_log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  tags = local.common_tags

  depends_on = [module.cluster]
}

# Azure Monitor Alerts for Production
resource "azurerm_monitor_metric_alert" "cpu_high" {
  name                = "${local.cluster_name}-cpu-high"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [module.cluster.cluster_id]
  description         = "Alert when CPU usage is high"
  severity            = 2

  criteria {
    metric_namespace = "Microsoft.ContainerService/managedClusters"
    metric_name      = "node_cpu_usage_percentage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = azurerm_monitor_action_group.critical.id
  }

  tags = local.common_tags
}

resource "azurerm_monitor_metric_alert" "memory_high" {
  name                = "${local.cluster_name}-memory-high"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [module.cluster.cluster_id]
  description         = "Alert when memory usage is high"
  severity            = 2

  criteria {
    metric_namespace = "Microsoft.ContainerService/managedClusters"
    metric_name      = "node_memory_working_set_percentage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = azurerm_monitor_action_group.critical.id
  }

  tags = local.common_tags
}

resource "azurerm_monitor_action_group" "critical" {
  name                = "${local.cluster_name}-critical-alerts"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "critical"

  email_receiver {
    name          = "platform-team"
    email_address = var.alert_email
  }

  tags = local.common_tags
}

# Disaster Recovery - Backup Vault
resource "azurerm_data_protection_backup_vault" "main" {
  name                = "${local.cluster_name}-backup-vault"
  resource_group_name = azurerm_resource_group.main.name
  location            = local.region
  datastore_type      = "VaultStore"
  redundancy          = "GeoRedundant"

  tags = local.common_tags
}

# Outputs
output "cluster_name" {
  description = "Name of the AKS cluster"
  value       = module.cluster.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint for the AKS cluster"
  value       = module.cluster.cluster_endpoint
  sensitive   = true
}

output "resource_group_name" {
  description = "Name of the Azure resource group"
  value       = azurerm_resource_group.main.name
}

output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.main.id
}

output "backup_vault_id" {
  description = "ID of the backup vault"
  value       = azurerm_data_protection_backup_vault.main.id
}

output "kubeconfig_command" {
  description = "Command to get kubeconfig"
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${local.cluster_name}"
}