/**
 * Bare Metal Staging Environment Variables
 * 
 * Version: 1.0
 * Date: 2026-02-19
 */

# ============================================================================
# Bare Metal Control Plane Configuration
# ============================================================================

variable "baremetal_control_plane_count" {
  description = "Number of control plane nodes (1 for staging, 3 for HA)"
  type        = number
  default     = 1
}

variable "baremetal_control_plane_hosts" {
  description = "List of control plane host configurations"
  type = list(object({
    id           = string
    ipmi_address = string
    ip_address   = string
    hostname     = string
    mac_address  = string
  }))
  
  # Example configuration:
  # [
  #   {
  #     id           = "cp-01"
  #     ipmi_address = "192.168.0.101"
  #     ip_address   = "192.168.1.101"
  #     hostname     = "k8s-cp-01"
  #     mac_address  = "00:50:56:00:01:01"
  #   }
  # ]
}

# ============================================================================
# Bare Metal Worker Configuration
# ============================================================================

variable "baremetal_worker_count" {
  description = "Number of worker nodes (2-3 for staging)"
  type        = number
  default     = 2
}

variable "baremetal_worker_hosts" {
  description = "List of worker host configurations"
  type = list(object({
    id           = string
    ipmi_address = string
    ip_address   = string
    hostname     = string
    mac_address  = string
  }))
  
  # Example configuration:
  # [
  #   {
  #     id           = "worker-01"
  #     ipmi_address = "192.168.0.111"
  #     ip_address   = "192.168.2.111"
  #     hostname     = "k8s-worker-01"
  #     mac_address  = "00:50:56:00:02:01"
  #   },
  #   {
  #     id           = "worker-02"
  #     ipmi_address = "192.168.0.112"
  #     ip_address   = "192.168.2.112"
  #     hostname     = "k8s-worker-02"
  #     mac_address  = "00:50:56:00:02:02"
  #   }
  # ]
}

# ============================================================================
# Bare Metal HCD Configuration
# ============================================================================

variable "baremetal_hcd_count" {
  description = "Number of HCD nodes (also used as Ceph storage nodes)"
  type        = number
  default     = 3
}

variable "baremetal_hcd_hosts" {
  description = "List of HCD host configurations"
  type = list(object({
    id           = string
    ipmi_address = string
    ip_address   = string
    hostname     = string
    mac_address  = string
  }))
  
  # Example configuration:
  # [
  #   {
  #     id           = "hcd-01"
  #     ipmi_address = "192.168.0.121"
  #     ip_address   = "192.168.3.121"
  #     hostname     = "k8s-hcd-01"
  #     mac_address  = "00:50:56:00:03:01"
  #   },
  #   {
  #     id           = "hcd-02"
  #     ipmi_address = "192.168.0.122"
  #     ip_address   = "192.168.3.122"
  #     hostname     = "k8s-hcd-02"
  #     mac_address  = "00:50:56:00:03:02"
  #   },
  #   {
  #     id           = "hcd-03"
  #     ipmi_address = "192.168.0.123"
  #     ip_address   = "192.168.3.123"
  #     hostname     = "k8s-hcd-03"
  #     mac_address  = "00:50:56:00:03:03"
  #   }
  # ]
}

# ============================================================================
# IPMI Configuration
# ============================================================================

variable "baremetal_ipmi_user" {
  description = "IPMI username for all servers"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "baremetal_ipmi_password" {
  description = "IPMI password for all servers"
  type        = string
  sensitive   = true
}

# ============================================================================
# SSH Configuration
# ============================================================================

variable "baremetal_ssh_user" {
  description = "SSH username for server access"
  type        = string
  default     = "root"
}

variable "baremetal_ssh_private_key_path" {
  description = "Path to SSH private key"
  type        = string
  default     = "~/.ssh/id_rsa"
}

# ============================================================================
# Network Configuration
# ============================================================================

variable "baremetal_pod_network_cidr" {
  description = "Pod network CIDR (Calico/Flannel)"
  type        = string
  default     = "10.244.0.0/16"
}

variable "baremetal_service_cidr" {
  description = "Service CIDR"
  type        = string
  default     = "10.96.0.0/12"
}

variable "baremetal_gateway" {
  description = "Default gateway IP"
  type        = string
  default     = "192.168.1.1"
}

variable "baremetal_dns_servers" {
  description = "DNS servers"
  type        = list(string)
  default     = ["8.8.8.8", "8.8.4.4"]
}

variable "baremetal_domain" {
  description = "Domain name for cluster"
  type        = string
  default     = "staging.local"
}

variable "baremetal_worker_cidr" {
  description = "CIDR for worker nodes"
  type        = string
  default     = "192.168.2.0/24"
}

variable "baremetal_hcd_cidr" {
  description = "CIDR for HCD nodes"
  type        = string
  default     = "192.168.3.0/24"
}

# ============================================================================
# Load Balancer Configuration
# ============================================================================

variable "baremetal_metallb_ip_range" {
  description = "IP range for MetalLB load balancer"
  type        = string
  default     = "192.168.1.200-192.168.1.250"
}

variable "baremetal_load_balancer_ip" {
  description = "Virtual IP for API load balancer (optional, for HA)"
  type        = string
  default     = ""
  
  # Example: "192.168.1.100"
  # Leave empty for single control plane
}

# ============================================================================
# PXE Boot Configuration
# ============================================================================

variable "baremetal_pxe_server" {
  description = "PXE server address (if using network boot)"
  type        = string
  default     = ""
  
  # Example: "192.168.1.10"
  # Leave empty if not using PXE boot
}

# ============================================================================
# Time Synchronization
# ============================================================================

variable "baremetal_ntp_servers" {
  description = "NTP servers for time synchronization"
  type        = list(string)
  default     = ["time.google.com", "time.cloudflare.com"]
}

# ============================================================================
# Storage Configuration
# ============================================================================

variable "baremetal_enable_nfs" {
  description = "Enable NFS storage class (in addition to Ceph)"
  type        = bool
  default     = false
}