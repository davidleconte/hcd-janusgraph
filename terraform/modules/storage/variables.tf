/**
 * Storage Module Variables
 *
 * Version: 1.0
 * Date: 2026-02-19
 */

# ============================================================================
# Cloud Provider Selection
# ============================================================================

variable "cloud_provider" {
  description = "Cloud provider (aws, azure, gcp, vsphere, baremetal)"
  type        = string

  validation {
    condition     = contains(["aws", "azure", "gcp", "vsphere", "baremetal"], var.cloud_provider)
    error_message = "Cloud provider must be aws, azure, gcp, vsphere, or baremetal."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

# ============================================================================
# Required Variables
# ============================================================================

variable "cluster_name" {
  description = "Name of the cluster (used for resource naming and tagging)"
  type        = string

  validation {
    condition     = length(var.cluster_name) > 0 && length(var.cluster_name) <= 40
    error_message = "Cluster name must be between 1 and 40 characters."
  }
}

variable "availability_zones" {
  description = "List of availability zones for storage topology"
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least 2 availability zones are required for high availability."
  }
}

variable "kms_key_id" {
  description = "KMS key ID for encryption (AWS/Azure/GCP)"
  type        = string
  default     = ""
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption (AWS only)"
  type        = string
  default     = ""
}

# ============================================================================
# HCD Storage Configuration
# ============================================================================

variable "hcd_volume_type" {
  description = "EBS volume type for HCD (gp3, io2)"
  type        = string
  default     = "io2"

  validation {
    condition     = contains(["gp3", "io2"], var.hcd_volume_type)
    error_message = "HCD volume type must be gp3 or io2."
  }
}

variable "hcd_iops" {
  description = "IOPS for HCD volumes (only for io2)"
  type        = number
  default     = 10000

  validation {
    condition     = var.hcd_iops >= 100 && var.hcd_iops <= 64000
    error_message = "HCD IOPS must be between 100 and 64000."
  }
}

variable "hcd_reclaim_policy" {
  description = "Reclaim policy for HCD volumes (Retain, Delete)"
  type        = string
  default     = "Retain"

  validation {
    condition     = contains(["Retain", "Delete"], var.hcd_reclaim_policy)
    error_message = "Reclaim policy must be Retain or Delete."
  }
}

# ============================================================================
# JanusGraph Storage Configuration
# ============================================================================

variable "janusgraph_volume_type" {
  description = "EBS volume type for JanusGraph (gp3, io2)"
  type        = string
  default     = "gp3"

  validation {
    condition     = contains(["gp3", "io2"], var.janusgraph_volume_type)
    error_message = "JanusGraph volume type must be gp3 or io2."
  }
}

variable "janusgraph_iops" {
  description = "IOPS for JanusGraph volumes (only for io2)"
  type        = number
  default     = 5000

  validation {
    condition     = var.janusgraph_iops >= 100 && var.janusgraph_iops <= 64000
    error_message = "JanusGraph IOPS must be between 100 and 64000."
  }
}

variable "janusgraph_reclaim_policy" {
  description = "Reclaim policy for JanusGraph volumes (Retain, Delete)"
  type        = string
  default     = "Retain"

  validation {
    condition     = contains(["Retain", "Delete"], var.janusgraph_reclaim_policy)
    error_message = "Reclaim policy must be Retain or Delete."
  }
}

# ============================================================================
# OpenSearch Storage Configuration
# ============================================================================

variable "opensearch_volume_type" {
  description = "EBS volume type for OpenSearch (gp3, io2)"
  type        = string
  default     = "gp3"

  validation {
    condition     = contains(["gp3", "io2"], var.opensearch_volume_type)
    error_message = "OpenSearch volume type must be gp3 or io2."
  }
}

variable "opensearch_iops" {
  description = "IOPS for OpenSearch volumes (only for io2)"
  type        = number
  default     = 5000

  validation {
    condition     = var.opensearch_iops >= 100 && var.opensearch_iops <= 64000
    error_message = "OpenSearch IOPS must be between 100 and 64000."
  }
}

variable "opensearch_reclaim_policy" {
  description = "Reclaim policy for OpenSearch volumes (Retain, Delete)"
  type        = string
  default     = "Retain"

  validation {
    condition     = contains(["Retain", "Delete"], var.opensearch_reclaim_policy)
    error_message = "Reclaim policy must be Retain or Delete."
  }
}

# ============================================================================
# Pulsar Storage Configuration
# ============================================================================

variable "pulsar_volume_type" {
  description = "EBS volume type for Pulsar (gp3, io2)"
  type        = string
  default     = "gp3"

  validation {
    condition     = contains(["gp3", "io2"], var.pulsar_volume_type)
    error_message = "Pulsar volume type must be gp3 or io2."
  }
}

variable "pulsar_iops" {
  description = "IOPS for Pulsar volumes (only for io2)"
  type        = number
  default     = 5000

  validation {
    condition     = var.pulsar_iops >= 100 && var.pulsar_iops <= 64000
    error_message = "Pulsar IOPS must be between 100 and 64000."
  }
}

variable "pulsar_reclaim_policy" {
  description = "Reclaim policy for Pulsar volumes (Retain, Delete)"
  type        = string
  default     = "Retain"

  validation {
    condition     = contains(["Retain", "Delete"], var.pulsar_reclaim_policy)
    error_message = "Reclaim policy must be Retain or Delete."
  }
}

# ============================================================================
# Backup Configuration
# ============================================================================

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30

  validation {
    condition     = var.backup_retention_days >= 7 && var.backup_retention_days <= 365
    error_message = "Backup retention must be between 7 and 365 days."
  }
}

variable "backup_transition_days" {
  description = "Number of days before transitioning backups to Glacier"
  type        = number
  default     = 7

  validation {
    condition     = var.backup_transition_days >= 1 && var.backup_transition_days <= 90
    error_message = "Backup transition must be between 1 and 90 days."
  }
}

variable "snapshot_retention_days" {
  description = "Number of days to retain EBS snapshots"
  type        = number
  default     = 14

  validation {
    condition     = var.snapshot_retention_days >= 1 && var.snapshot_retention_days <= 90
    error_message = "Snapshot retention must be between 1 and 90 days."
  }
}

# ============================================================================
# Optional Variables
# ============================================================================

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# ============================================================================
# Azure-Specific Variables
# ============================================================================

variable "azure_region" {
  description = "Azure region for storage resources"
  type        = string
  default     = ""
}

variable "azure_resource_group_name" {
  description = "Azure resource group name"
  type        = string
  default     = ""
}

variable "azure_hcd_disk_type" {
  description = "Azure disk type for HCD (Premium_LRS, StandardSSD_LRS, UltraSSD_LRS)"
  type        = string
  default     = "Premium_LRS"
}

variable "azure_janusgraph_disk_type" {
  description = "Azure disk type for JanusGraph"
  type        = string
  default     = "StandardSSD_LRS"
}

variable "azure_opensearch_disk_type" {
  description = "Azure disk type for OpenSearch"
  type        = string
  default     = "StandardSSD_LRS"
}

variable "azure_pulsar_disk_type" {
  description = "Azure disk type for Pulsar"
  type        = string
  default     = "StandardSSD_LRS"
}

variable "azure_disk_encryption_set_id" {
  description = "Azure Disk Encryption Set ID"
  type        = string
  default     = ""
}

variable "azure_key_vault_key_id" {
  description = "Azure Key Vault Key ID for disk encryption"
  type        = string
  default     = ""
}

# ============================================================================
# GCP-Specific Variables
# ============================================================================

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
  default     = ""
}

variable "gcp_region" {
  description = "GCP region for storage resources"
  type        = string
  default     = ""
}

variable "gcp_zones" {
  description = "GCP zones for storage topology"
  type        = list(string)
  default     = []
}

variable "gcp_hcd_disk_type" {
  description = "GCP disk type for HCD (pd-ssd, pd-balanced, pd-extreme)"
  type        = string
  default     = "pd-ssd"
}

variable "gcp_janusgraph_disk_type" {
  description = "GCP disk type for JanusGraph"
  type        = string
  default     = "pd-balanced"
}

variable "gcp_opensearch_disk_type" {
  description = "GCP disk type for OpenSearch"
  type        = string
  default     = "pd-balanced"
}

variable "gcp_pulsar_disk_type" {
  description = "GCP disk type for Pulsar"
  type        = string
  default     = "pd-ssd"
}

# ============================================================================
# vSphere-Specific Variables
# ============================================================================

variable "vsphere_datacenter" {
  description = "vSphere datacenter name"
  type        = string
  default     = ""
}

variable "vsphere_datastore_name" {
  description = "vSphere datastore name"
  type        = string
  default     = ""
}

variable "vsphere_datastore_url" {
  description = "vSphere datastore URL"
  type        = string
  default     = ""
}

variable "vsphere_hcd_storage_policy" {
  description = "vSphere storage policy for HCD"
  type        = string
  default     = "vSAN Default Storage Policy"
}

variable "vsphere_janusgraph_storage_policy" {
  description = "vSphere storage policy for JanusGraph"
  type        = string
  default     = "vSAN Default Storage Policy"
}

variable "vsphere_opensearch_storage_policy" {
  description = "vSphere storage policy for OpenSearch"
  type        = string
  default     = "vSAN Default Storage Policy"
}

variable "vsphere_pulsar_storage_policy" {
  description = "vSphere storage policy for Pulsar"
  type        = string
  default     = "vSAN Default Storage Policy"
}

variable "vsphere_general_storage_policy" {
  description = "vSphere storage policy for general use"
  type        = string
  default     = "vSAN Default Storage Policy"
}

variable "vsphere_enable_nfs" {
  description = "Enable NFS storage class"
  type        = bool
  default     = false
}

variable "vsphere_nfs_server" {
  description = "NFS server address"
  type        = string
  default     = ""
}

variable "vsphere_nfs_share" {
  description = "NFS share path"
  type        = string
  default     = ""
}

variable "vsphere_enable_vsan" {
  description = "Enable vSAN storage class"
  type        = bool
  default     = false
}

variable "vsphere_vsan_datastore_url" {
  description = "vSAN datastore URL"
  type        = string
  default     = ""
}

variable "vsphere_vsan_storage_policy" {
  description = "vSAN storage policy"
  type        = string
  default     = "vSAN Default Storage Policy"
}

# ============================================================================
# Bare Metal-Specific Variables
# ============================================================================

variable "baremetal_hcd_count" {
  description = "Number of bare metal HCD nodes (used as Ceph storage nodes)"
  type        = number
  default     = 3
}

variable "baremetal_hcd_hosts" {
  description = "List of bare metal HCD host configurations"
  type = list(object({
    id           = string
    ipmi_address = string
    ip_address   = string
    hostname     = string
    mac_address  = string
  }))
  default = []
}

variable "baremetal_control_plane_count" {
  description = "Number of bare metal control plane nodes"
  type        = number
  default     = 3
}

variable "baremetal_control_plane_hosts" {
  description = "List of bare metal control plane host configurations"
  type = list(object({
    id           = string
    ipmi_address = string
    ip_address   = string
    hostname     = string
    mac_address  = string
  }))
  default = []
}

variable "baremetal_worker_count" {
  description = "Number of bare metal worker nodes"
  type        = number
  default     = 3
}

variable "baremetal_worker_hosts" {
  description = "List of bare metal worker host configurations"
  type = list(object({
    id           = string
    ipmi_address = string
    ip_address   = string
    hostname     = string
    mac_address  = string
  }))
  default = []
}

variable "baremetal_ssh_user" {
  description = "SSH username for bare metal servers"
  type        = string
  default     = "root"
}

variable "baremetal_ssh_private_key_path" {
  description = "Path to SSH private key for bare metal servers"
  type        = string
  default     = "~/.ssh/id_rsa"
}

variable "baremetal_hcd_cidr" {
  description = "CIDR for HCD nodes network"
  type        = string
  default     = "192.168.3.0/24"
}

variable "baremetal_worker_cidr" {
  description = "CIDR for worker nodes network"
  type        = string
  default     = "192.168.2.0/24"
}

variable "baremetal_enable_nfs" {
  description = "Enable NFS storage for bare metal"
  type        = bool
  default     = false
}

variable "baremetal_ceph_pool_pg_num" {
  description = "Number of placement groups for Ceph pools"
  type        = number
  default     = 128

  validation {
    condition     = var.baremetal_ceph_pool_pg_num >= 32 && var.baremetal_ceph_pool_pg_num <= 512
    error_message = "Ceph pool PG number must be between 32 and 512."
  }
}

variable "baremetal_ceph_replica_size" {
  description = "Number of replicas for Ceph data"
  type        = number
  default     = 3

  validation {
    condition     = var.baremetal_ceph_replica_size >= 2 && var.baremetal_ceph_replica_size <= 5
    error_message = "Ceph replica size must be between 2 and 5."
  }
}

variable "baremetal_ceph_min_size" {
  description = "Minimum number of replicas for Ceph data"
  type        = number
  default     = 2

  validation {
    condition     = var.baremetal_ceph_min_size >= 1 && var.baremetal_ceph_min_size <= 3
    error_message = "Ceph minimum replica size must be between 1 and 3."
  }

variable "baremetal_hcd_data_disk" {
  description = "Data disk device for Ceph OSDs (e.g., /dev/sdb, /dev/nvme0n1, /dev/vdb)"
  type        = string
  default     = "/dev/sdb"

  validation {
    condition     = can(regex("^/dev/[a-z0-9]+$", var.baremetal_hcd_data_disk))
    error_message = "Disk device must be a valid device path (e.g., /dev/sdb, /dev/nvme0n1)."
  }
}
}