/**
 * Networking Module Variables
 * 
 * Version: 1.0
 * Date: 2026-02-19
 */

# ============================================================================
# Required Variables
# ============================================================================

variable "cluster_name" {
  description = "Name of the EKS cluster (used for resource naming and tagging)"
  type        = string

  validation {
    condition     = length(var.cluster_name) > 0 && length(var.cluster_name) <= 40
    error_message = "Cluster name must be between 1 and 40 characters."
  }
}

variable "region" {
  description = "AWS region for VPC and networking resources"
  type        = string

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.region))
    error_message = "Region must be a valid AWS region (e.g., us-east-1, eu-west-1)."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones for subnet distribution"
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least 2 availability zones are required for high availability."
  }
}

# ============================================================================
# Optional Variables
# ============================================================================

variable "enable_nat_gateway" {
  description = "Enable NAT gateways for private subnet internet access"
  type        = bool
  default     = true
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for AWS services (S3, ECR)"
  type        = bool
  default     = true
}

variable "enable_network_acls" {
  description = "Enable custom network ACLs for additional security"
  type        = bool
  default     = false
}

variable "enable_flow_logs" {
  description = "Enable VPC flow logs for network monitoring"
  type        = bool
  default     = true
}

variable "flow_logs_retention_days" {
  description = "Number of days to retain VPC flow logs"
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.flow_logs_retention_days)
    error_message = "Flow logs retention must be a valid CloudWatch Logs retention period."
  }
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}

# ============================================================================
# Cloud Provider Selection
# ============================================================================

variable "cloud_provider" {
  description = "Cloud provider (aws, azure, gcp, vsphere, baremetal)"
  type        = string
  default     = "aws"

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
# Azure-Specific Variables
# ============================================================================

variable "azure_region" {
  description = "Azure region for networking resources"
  type        = string
  default     = "eastus"
}

variable "azure_resource_group_name" {
  description = "Azure resource group name"
  type        = string
  default     = ""
}

variable "azure_network_watcher_name" {
  description = "Azure Network Watcher name for flow logs"
  type        = string
  default     = "NetworkWatcher"
}

variable "azure_network_watcher_rg" {
  description = "Azure Network Watcher resource group"
  type        = string
  default     = "NetworkWatcherRG"
}

variable "azure_flow_logs_storage_account_id" {
  description = "Azure Storage Account ID for flow logs"
  type        = string
  default     = ""
}

variable "azure_log_analytics_workspace_id" {
  description = "Azure Log Analytics Workspace ID"
  type        = string
  default     = ""
}

variable "azure_log_analytics_workspace_resource_id" {
  description = "Azure Log Analytics Workspace Resource ID"
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
  description = "GCP region for networking resources"
  type        = string
  default     = "us-central1"
}

variable "gcp_pod_cidr" {
  description = "CIDR for GKE pods"
  type        = string
  default     = "10.4.0.0/14"
}

variable "gcp_service_cidr" {
  description = "CIDR for GKE services"
  type        = string
  default     = "10.8.0.0/20"
}

variable "gcp_flow_logs_bucket" {
  description = "GCS bucket for VPC flow logs"
  type        = string
  default     = ""
}

# ============================================================================
# vSphere-Specific Variables
# ============================================================================

variable "vsphere_datacenter" {
  description = "vSphere datacenter name"
  type        = string
  default     = ""
}

variable "vsphere_network_name" {
  description = "vSphere network/port group name"
  type        = string
  default     = ""
}

variable "vsphere_use_distributed_switch" {
  description = "Use vSphere Distributed Switch (vDS)"
  type        = bool
  default     = false
}

variable "vsphere_dvs_name" {
  description = "vSphere Distributed Virtual Switch name"
  type        = string
  default     = ""
}

variable "vsphere_vlan_id" {
  description = "VLAN ID for vSphere port group"
  type        = number
  default     = 0
}

# ============================================================================
# Bare Metal-Specific Variables
# ============================================================================

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

variable "baremetal_hcd_count" {
  description = "Number of bare metal HCD nodes"
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

variable "baremetal_gateway" {
  description = "Gateway IP for bare metal network"
  type        = string
  default     = "192.168.1.1"
}

variable "baremetal_dns_servers" {
  description = "DNS servers for bare metal network"
  type        = list(string)
  default     = ["8.8.8.8", "8.8.4.4"]
}

variable "baremetal_domain" {
  description = "Domain name for bare metal cluster"
  type        = string
  default     = "local"
}

variable "baremetal_load_balancer_ip" {
  description = "Virtual IP for bare metal load balancer (HAProxy/Keepalived)"
  type        = string
  default     = ""
}

variable "baremetal_worker_cidr" {
  description = "CIDR for worker nodes network"
  type        = string
  default     = "192.168.2.0/24"
}

variable "baremetal_hcd_cidr" {
  description = "CIDR for HCD nodes network"
  type        = string
  default     = "192.168.3.0/24"
}
}