# Azure Storage Implementation
# Part of multi-cloud storage module

# ============================================================================
# Azure Managed Disk StorageClasses
# ============================================================================

# HCD (Cassandra) Storage Class - Premium SSD
resource "kubernetes_storage_class_v1" "azure_hcd" {
  count = var.cloud_provider == "azure" ? 1 : 0

  metadata {
    name = "hcd-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "disk.csi.azure.com"
  reclaim_policy         = var.hcd_reclaim_policy
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    skuName             = var.azure_hcd_disk_type  # Premium_LRS, StandardSSD_LRS
    kind                = "Managed"
    cachingMode         = "ReadWrite"
    diskEncryptionSetID = var.azure_disk_encryption_set_id
    fsType              = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.disk.csi.azure.com/zone"
      values = var.availability_zones
    }
  }
}

# JanusGraph Storage Class - Standard SSD
resource "kubernetes_storage_class_v1" "azure_janusgraph" {
  count = var.cloud_provider == "azure" ? 1 : 0

  metadata {
    name = "janusgraph-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "disk.csi.azure.com"
  reclaim_policy         = var.janusgraph_reclaim_policy
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    skuName             = var.azure_janusgraph_disk_type
    kind                = "Managed"
    cachingMode         = "ReadOnly"
    diskEncryptionSetID = var.azure_disk_encryption_set_id
    fsType              = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.disk.csi.azure.com/zone"
      values = var.availability_zones
    }
  }
}

# OpenSearch Storage Class - Standard SSD
resource "kubernetes_storage_class_v1" "azure_opensearch" {
  count = var.cloud_provider == "azure" ? 1 : 0

  metadata {
    name = "opensearch-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "disk.csi.azure.com"
  reclaim_policy         = var.opensearch_reclaim_policy
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    skuName             = var.azure_opensearch_disk_type
    kind                = "Managed"
    cachingMode         = "ReadOnly"
    diskEncryptionSetID = var.azure_disk_encryption_set_id
    fsType              = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.disk.csi.azure.com/zone"
      values = var.availability_zones
    }
  }
}

# Pulsar Storage Class - Standard SSD
resource "kubernetes_storage_class_v1" "azure_pulsar" {
  count = var.cloud_provider == "azure" ? 1 : 0

  metadata {
    name = "pulsar-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "disk.csi.azure.com"
  reclaim_policy         = var.pulsar_reclaim_policy
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    skuName             = var.azure_pulsar_disk_type
    kind                = "Managed"
    cachingMode         = "ReadWrite"
    diskEncryptionSetID = var.azure_disk_encryption_set_id
    fsType              = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.disk.csi.azure.com/zone"
      values = var.availability_zones
    }
  }
}

# Mission Control Storage Class - Standard SSD
resource "kubernetes_storage_class_v1" "azure_mission_control" {
  count = var.cloud_provider == "azure" ? 1 : 0

  metadata {
    name = "mission-control-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
  }

  storage_provisioner    = "disk.csi.azure.com"
  reclaim_policy         = "Retain"
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    skuName             = "StandardSSD_LRS"
    kind                = "Managed"
    cachingMode         = "ReadWrite"
    diskEncryptionSetID = var.azure_disk_encryption_set_id
    fsType              = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.disk.csi.azure.com/zone"
      values = var.availability_zones
    }
  }
}

# General Purpose Storage Class (Default) - Standard SSD
resource "kubernetes_storage_class_v1" "azure_general" {
  count = var.cloud_provider == "azure" ? 1 : 0

  metadata {
    name = "general-storage"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }

  storage_provisioner    = "disk.csi.azure.com"
  reclaim_policy         = "Delete"
  allow_volume_expansion = true
  volume_binding_mode    = "WaitForFirstConsumer"

  parameters = {
    skuName             = "StandardSSD_LRS"
    kind                = "Managed"
    cachingMode         = "ReadWrite"
    diskEncryptionSetID = var.azure_disk_encryption_set_id
    fsType              = "ext4"
  }

  allowed_topologies {
    match_label_expressions {
      key    = "topology.disk.csi.azure.com/zone"
      values = var.availability_zones
    }
  }
}

# ============================================================================
# Azure Blob Storage - Backups
# ============================================================================

resource "azurerm_storage_account" "backups" {
  count                    = var.cloud_provider == "azure" ? 1 : 0
  name                     = replace("${var.cluster_name}backups", "-", "")  # Storage account names can't have hyphens
  resource_group_name      = var.azure_resource_group_name
  location                 = var.azure_region
  account_tier             = "Standard"
  account_replication_type = "GRS"  # Geo-redundant storage
  account_kind             = "StorageV2"
  
  # Security
  enable_https_traffic_only       = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  
  # Encryption
  infrastructure_encryption_enabled = true

  blob_properties {
    versioning_enabled = true
    
    delete_retention_policy {
      days = 30
    }
    
    container_delete_retention_policy {
      days = 30
    }
  }

  tags = merge(
    var.tags,
    {
      Name    = "${var.cluster_name}-backups"
      Purpose = "Backup storage for JanusGraph Banking Platform"
    }
  )
}

resource "azurerm_storage_container" "backups" {
  count                 = var.cloud_provider == "azure" ? 1 : 0
  name                  = "backups"
  storage_account_name  = azurerm_storage_account.backups[0].name
  container_access_type = "private"
}

resource "azurerm_storage_management_policy" "backups" {
  count              = var.cloud_provider == "azure" ? 1 : 0
  storage_account_id = azurerm_storage_account.backups[0].id

  rule {
    name    = "transition-to-cool"
    enabled = true
    
    filters {
      blob_types = ["blockBlob"]
    }
    
    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than = var.backup_transition_days
        delete_after_days_since_modification_greater_than       = var.backup_retention_days
      }
      
      snapshot {
        delete_after_days_since_creation_greater_than = 30
      }
    }
  }
}

# ============================================================================
# Azure Blob Storage - Snapshots
# ============================================================================

resource "azurerm_storage_account" "snapshots" {
  count                    = var.cloud_provider == "azure" ? 1 : 0
  name                     = replace("${var.cluster_name}snapshots", "-", "")
  resource_group_name      = var.azure_resource_group_name
  location                 = var.azure_region
  account_tier             = "Standard"
  account_replication_type = "LRS"  # Locally redundant storage
  account_kind             = "StorageV2"
  
  # Security
  enable_https_traffic_only       = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  
  # Encryption
  infrastructure_encryption_enabled = true

  blob_properties {
    versioning_enabled = true
    
    delete_retention_policy {
      days = 7
    }
  }

  tags = merge(
    var.tags,
    {
      Name    = "${var.cluster_name}-snapshots"
      Purpose = "Disk snapshot storage"
    }
  )
}

resource "azurerm_storage_container" "snapshots" {
  count                 = var.cloud_provider == "azure" ? 1 : 0
  name                  = "snapshots"
  storage_account_name  = azurerm_storage_account.snapshots[0].name
  container_access_type = "private"
}

resource "azurerm_storage_management_policy" "snapshots" {
  count              = var.cloud_provider == "azure" ? 1 : 0
  storage_account_id = azurerm_storage_account.snapshots[0].id

  rule {
    name    = "expire-old-snapshots"
    enabled = true
    
    filters {
      blob_types = ["blockBlob"]
    }
    
    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = var.snapshot_retention_days
      }
      
      snapshot {
        delete_after_days_since_creation_greater_than = 7
      }
    }
  }
}

# ============================================================================
# Azure Backup Vault
# ============================================================================

resource "azurerm_data_protection_backup_vault" "main" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${var.cluster_name}-backup-vault"
  resource_group_name = var.azure_resource_group_name
  location            = var.azure_region
  datastore_type      = "VaultStore"
  redundancy          = "GeoRedundant"

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-backup-vault"
    }
  )
}

# ============================================================================
# Azure Backup Policy - Disks
# ============================================================================

resource "azurerm_data_protection_backup_policy_disk" "main" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${var.cluster_name}-disk-backup-policy"
  vault_id            = azurerm_data_protection_backup_vault.main[0].id

  # Daily backups
  backup_repeating_time_intervals = ["R/2024-01-01T02:00:00+00:00/P1D"]  # Daily at 2 AM UTC
  
  default_retention_duration = "P${var.backup_retention_days}D"

  retention_rule {
    name     = "Weekly"
    duration = "P${var.backup_retention_days * 4}D"
    priority = 20
    
    criteria {
      absolute_criteria = "FirstOfWeek"
    }
  }
}

# ============================================================================
# Disk Encryption Set
# ============================================================================

resource "azurerm_disk_encryption_set" "main" {
  count               = var.cloud_provider == "azure" && var.azure_disk_encryption_set_id == "" ? 1 : 0
  name                = "${var.cluster_name}-disk-encryption"
  resource_group_name = var.azure_resource_group_name
  location            = var.azure_region
  key_vault_key_id    = var.azure_key_vault_key_id

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}