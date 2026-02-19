# Variables for OpenShift Cluster Module

variable "cluster_name" {
  description = "Name of the OpenShift/EKS cluster"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "cloud_provider" {
  description = "Cloud provider (aws, azure, gcp, vsphere, baremetal)"
  type        = string
  default     = "aws"

  validation {
    condition     = contains(["aws", "azure", "gcp", "vsphere", "baremetal"], var.cloud_provider)
    error_message = "Cloud provider must be aws, azure, gcp, vsphere, or baremetal."
  }
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "vpc_id" {
  description = "VPC ID where cluster will be deployed"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for cluster"
  type        = list(string)
}

variable "node_count" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 3
}

variable "node_count_min" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 3
}

variable "node_count_max" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 10
}

variable "instance_type" {
  description = "EC2 instance type for worker nodes"
  type        = string
  default     = "m5.2xlarge"
}

variable "capacity_type" {
  description = "Capacity type (ON_DEMAND or SPOT)"
  type        = string
  default     = "ON_DEMAND"

  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.capacity_type)
    error_message = "Capacity type must be ON_DEMAND or SPOT."
  }
}

variable "disk_size" {
  description = "Disk size in GB for worker nodes"
  type        = number
  default     = 100
}

variable "enable_public_access" {
  description = "Enable public access to cluster API"
  type        = bool
  default     = true
}

variable "public_access_cidrs" {
  description = "CIDR blocks allowed to access cluster API"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "kms_key_arn" {
  description = "ARN of KMS key for secrets encryption"
  type        = string
  default     = ""
}

variable "enable_ebs_csi" {
  description = "Enable EBS CSI driver addon"
  type        = bool
  default     = true
}

variable "ebs_csi_version" {
  description = "Version of EBS CSI driver"
  type        = string
  default     = "v1.25.0-eksbuild.1"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

# ============================================================================
# Azure-Specific Variables
# ============================================================================

variable "azure_region" {
  description = "Azure region for AKS cluster"
  type        = string
  default     = "eastus"
}

variable "azure_vm_size" {
  description = "Azure VM size for general worker nodes"
  type        = string
  default     = "Standard_D4s_v3"
}

variable "azure_hcd_vm_size" {
  description = "Azure VM size for HCD worker nodes"
  type        = string
  default     = "Standard_E8s_v3"
}

variable "azure_subnet_id" {
  description = "Azure subnet ID for AKS nodes"
  type        = string
  default     = ""
}

variable "azure_dns_service_ip" {
  description = "IP address for Kubernetes DNS service"
  type        = string
  default     = "10.0.0.10"
}

variable "azure_service_cidr" {
  description = "CIDR for Kubernetes services"
  type        = string
  default     = "10.0.0.0/16"
}

variable "azure_admin_group_ids" {
  description = "Azure AD group IDs for cluster admins"
  type        = list(string)
  default     = []
}

variable "azure_acr_id" {
  description = "Azure Container Registry ID for AcrPull role assignment"
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
  description = "GCP region for GKE cluster"
  type        = string
  default     = "us-central1"
}

variable "gcp_zones" {
  description = "GCP zones for multi-zone GKE cluster"
  type        = list(string)
  default     = ["us-central1-a", "us-central1-b", "us-central1-c"]
}

variable "gcp_network" {
  description = "GCP VPC network name"
  type        = string
  default     = ""
}

variable "gcp_subnetwork" {
  description = "GCP VPC subnetwork name"
  type        = string
  default     = ""
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

variable "gcp_master_cidr" {
  description = "CIDR for GKE master nodes"
  type        = string
  default     = "172.16.0.0/28"
}

variable "gcp_machine_type" {
  description = "GCP machine type for general worker nodes"
  type        = string
  default     = "n2-standard-4"
}

variable "gcp_hcd_machine_type" {
  description = "GCP machine type for HCD worker nodes"
  type        = string
  default     = "n2-highmem-8"
}

variable "gcp_master_authorized_networks" {
  description = "List of CIDR blocks authorized to access GKE master"
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  default = []
}

# ============================================================================
# On-Premises Variables
# ============================================================================

variable "on_prem_platform" {
  description = "On-premises platform (vmware, baremetal)"
  type        = string
  default     = "vmware"

  validation {
    condition     = contains(["vmware", "baremetal"], var.on_prem_platform)
    error_message = "On-premises platform must be vmware or baremetal."
  }
}

variable "vsphere_server" {
  description = "vSphere server address"
  type        = string
  default     = ""
}

variable "vsphere_datacenter" {
  description = "vSphere datacenter name"
  type        = string
  default     = ""
}

variable "vsphere_datastore" {
  description = "vSphere datastore name"
  type        = string
  default     = ""
}

variable "vsphere_cluster" {
  description = "vSphere cluster name"
  type        = string
  default     = ""
}

variable "vsphere_network" {
  description = "vSphere network name"
  type        = string
  default     = ""
}

variable "vsphere_template" {
  description = "vSphere VM template name for Kubernetes nodes"
  type        = string
  default     = ""
}

variable "vsphere_resource_pool" {
  description = "vSphere resource pool name"
  type        = string
  default     = ""
}

variable "control_plane_cidr" {
  description = "CIDR for control plane nodes (on-prem)"
  type        = string
  default     = "192.168.1.0/24"
}

variable "worker_cidr" {
  description = "CIDR for worker nodes (on-prem)"
  type        = string
  default     = "192.168.2.0/24"
}

variable "hcd_worker_cidr" {
  description = "CIDR for HCD worker nodes (on-prem)"
  type        = string
  default     = "192.168.3.0/24"
}

variable "gateway_ip" {
  description = "Gateway IP for on-prem network"
  type        = string
  default     = "192.168.1.1"
}

variable "dns_servers" {
  description = "DNS servers for on-prem network"
  type        = list(string)
  default     = ["8.8.8.8", "8.8.4.4"]
}

variable "domain_name" {
  description = "Domain name for on-prem cluster"
  type        = string
  default     = "local"
}

# ============================================================================
# vSphere-Specific Variables (Extended)
# ============================================================================

variable "vsphere_folder" {
  description = "vSphere folder for VMs"
  type        = string
  default     = ""
}

variable "vsphere_domain" {
  description = "Domain name for vSphere VMs"
  type        = string
  default     = "local"
}

variable "vsphere_network_cidr" {
  description = "Network CIDR for vSphere VMs"
  type        = string
  default     = "192.168.1.0/24"
}

variable "vsphere_gateway" {
  description = "Gateway IP for vSphere network"
  type        = string
  default     = "192.168.1.1"
}

variable "vsphere_dns_servers" {
  description = "DNS servers for vSphere VMs"
  type        = list(string)
  default     = ["8.8.8.8", "8.8.4.4"]
}

variable "vsphere_control_plane_count" {
  description = "Number of control plane nodes"
  type        = number
  default     = 3
}

variable "vsphere_control_plane_cpu" {
  description = "Number of CPUs for control plane nodes"
  type        = number
  default     = 4
}

variable "vsphere_control_plane_memory" {
  description = "Memory in MB for control plane nodes"
  type        = number
  default     = 16384
}

variable "vsphere_control_plane_disk_size" {
  description = "Disk size in GB for control plane nodes"
  type        = number
  default     = 100
}

variable "vsphere_worker_cpu" {
  description = "Number of CPUs for worker nodes"
  type        = number
  default     = 8
}

variable "vsphere_worker_memory" {
  description = "Memory in MB for worker nodes"
  type        = number
  default     = 32768
}

variable "vsphere_worker_disk_size" {
  description = "Disk size in GB for worker nodes"
  type        = number
  default     = 200
}

variable "vsphere_hcd_count" {
  description = "Number of HCD nodes"
  type        = number
  default     = 3
}

variable "vsphere_hcd_cpu" {
  description = "Number of CPUs for HCD nodes"
  type        = number
  default     = 16
}

variable "vsphere_hcd_memory" {
  description = "Memory in MB for HCD nodes"
  type        = number
  default     = 131072
}

variable "vsphere_hcd_disk_size" {
  description = "OS disk size in GB for HCD nodes"
  type        = number
  default     = 100
}

variable "vsphere_hcd_data_disk_size" {
  description = "Data disk size in GB for HCD nodes"
  type        = number
  default     = 1000
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

variable "baremetal_ipmi_user" {
  description = "IPMI username for bare metal servers"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "baremetal_ipmi_password" {
  description = "IPMI password for bare metal servers"
  type        = string
  sensitive   = true
  default     = ""
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

variable "baremetal_pod_network_cidr" {
  description = "Pod network CIDR for bare metal Kubernetes cluster"
  type        = string
  default     = "10.244.0.0/16"
}

variable "baremetal_service_cidr" {
  description = "Service CIDR for bare metal Kubernetes cluster"
  type        = string
  default     = "10.96.0.0/12"
}

variable "baremetal_metallb_ip_range" {
  description = "IP address range for MetalLB load balancer"
  type        = string
  default     = "192.168.1.200-192.168.1.250"
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

variable "baremetal_pxe_server" {
  description = "PXE server address for bare metal provisioning"
  type        = string
  default     = ""
}

variable "baremetal_ntp_servers" {
  description = "NTP servers for bare metal nodes"
  type        = list(string)
  default     = ["time.google.com", "time.cloudflare.com"]
}

variable "baremetal_load_balancer_ip" {
  description = "Virtual IP for bare metal load balancer (HAProxy/Keepalived)"
  type        = string
  default     = ""
}