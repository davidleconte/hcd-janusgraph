# Azure Kubernetes Service (AKS) Implementation
# Part of multi-cloud cluster module

# Azure Resource Group
resource "azurerm_resource_group" "main" {
  count    = var.cloud_provider == "azure" ? 1 : 0
  name     = "${var.cluster_name}-rg"
  location = var.azure_region
  tags     = local.common_tags
}

# Azure Kubernetes Service Cluster
resource "azurerm_kubernetes_cluster" "main" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = var.cluster_name
  location            = azurerm_resource_group.main[0].location
  resource_group_name = azurerm_resource_group.main[0].name
  dns_prefix          = var.cluster_name
  kubernetes_version  = var.kubernetes_version

  # Default node pool (system nodes)
  default_node_pool {
    name                = "system"
    node_count          = var.node_count
    vm_size             = var.azure_vm_size
    vnet_subnet_id      = var.azure_subnet_id
    enable_auto_scaling = true
    min_count           = var.node_count_min
    max_count           = var.node_count_max
    os_disk_size_gb     = var.disk_size
    os_disk_type        = "Managed"
    type                = "VirtualMachineScaleSets"

    node_labels = {
      "role"        = "system"
      "environment" = var.environment
      "project"     = "janusgraph-banking"
    }

    tags = local.common_tags
  }

  # Identity
  identity {
    type = "SystemAssigned"
  }

  # Network Profile
  network_profile {
    network_plugin    = "azure"
    network_policy    = "calico"
    load_balancer_sku = "standard"
    outbound_type     = "loadBalancer"
    dns_service_ip    = var.azure_dns_service_ip
    service_cidr      = var.azure_service_cidr
  }

  # Azure AD Integration
  azure_active_directory_role_based_access_control {
    managed                = true
    azure_rbac_enabled     = true
    admin_group_object_ids = var.azure_admin_group_ids
  }

  # Monitoring
  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main[0].id
  }

  # Azure Policy
  azure_policy_enabled = true

  # HTTP Application Routing (disabled for production)
  http_application_routing_enabled = false

  # Key Vault Secrets Provider
  key_vault_secrets_provider {
    secret_rotation_enabled  = true
    secret_rotation_interval = "2m"
  }

  # Maintenance Window
  maintenance_window {
    allowed {
      day   = "Sunday"
      hours = [2, 3, 4]
    }
  }

  # Auto-upgrade
  automatic_channel_upgrade = var.environment == "prod" ? "stable" : "patch"

  tags = local.common_tags

  lifecycle {
    ignore_changes = [
      default_node_pool[0].node_count
    ]
  }
}

# Additional Node Pool for HCD workloads
resource "azurerm_kubernetes_cluster_node_pool" "hcd" {
  count                 = var.cloud_provider == "azure" ? 1 : 0
  name                  = "hcd"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main[0].id
  vm_size               = var.azure_hcd_vm_size
  node_count            = 3
  enable_auto_scaling   = true
  min_count             = 3
  max_count             = 6
  os_disk_size_gb       = 500
  os_disk_type          = "Managed"
  vnet_subnet_id        = var.azure_subnet_id

  node_labels = {
    "role"        = "hcd"
    "environment" = var.environment
    "project"     = "janusgraph-banking"
  }

  node_taints = [
    "workload=hcd:NoSchedule"
  ]

  tags = local.common_tags

  lifecycle {
    ignore_changes = [
      node_count
    ]
  }
}

# Log Analytics Workspace for monitoring
resource "azurerm_log_analytics_workspace" "main" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${var.cluster_name}-logs"
  location            = azurerm_resource_group.main[0].location
  resource_group_name = azurerm_resource_group.main[0].name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days

  tags = local.common_tags
}

# Log Analytics Solution for Container Insights
resource "azurerm_log_analytics_solution" "container_insights" {
  count                 = var.cloud_provider == "azure" ? 1 : 0
  solution_name         = "ContainerInsights"
  location              = azurerm_resource_group.main[0].location
  resource_group_name   = azurerm_resource_group.main[0].name
  workspace_resource_id = azurerm_log_analytics_workspace.main[0].id
  workspace_name        = azurerm_log_analytics_workspace.main[0].name

  plan {
    publisher = "Microsoft"
    product   = "OMSGallery/ContainerInsights"
  }

  tags = local.common_tags
}

# Role Assignment for AKS to access ACR
resource "azurerm_role_assignment" "acr_pull" {
  count                = var.cloud_provider == "azure" && var.azure_acr_id != "" ? 1 : 0
  principal_id         = azurerm_kubernetes_cluster.main[0].kubelet_identity[0].object_id
  role_definition_name = "AcrPull"
  scope                = var.azure_acr_id
}

# Diagnostic Settings for AKS
resource "azurerm_monitor_diagnostic_setting" "aks" {
  count                      = var.cloud_provider == "azure" ? 1 : 0
  name                       = "${var.cluster_name}-diagnostics"
  target_resource_id         = azurerm_kubernetes_cluster.main[0].id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main[0].id

  enabled_log {
    category = "kube-apiserver"
  }

  enabled_log {
    category = "kube-audit"
  }

  enabled_log {
    category = "kube-controller-manager"
  }

  enabled_log {
    category = "kube-scheduler"
  }

  enabled_log {
    category = "cluster-autoscaler"
  }

  metric {
    category = "AllMetrics"
    enabled  = true
  }
}