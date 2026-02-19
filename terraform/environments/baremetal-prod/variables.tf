/**
 * Bare Metal Production Environment Variables
 * 
 * Version: 1.0
 * Date: 2026-02-19
 */

# ============================================================================
# Bare Metal Control Plane Configuration (HA Required)
# ============================================================================

variable "baremetal_control_plane_count" {
  description = "Number of control plane nodes (3 for production HA)"
  type        = number
  default     = 3

  validation {
    condition     = var.baremetal_control_plane_count == 3
    error_message = "Production requires exactly 3 control plane nodes for HA."
  }
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
  
  validation {
    condition     = length(var.baremetal_control_plane_hosts) == 3
    error_message = "Production requires exactly 3 control plane hosts."
  }
}

# ============================================================================
# Bare Metal Worker Configuration
# ============================================================================

variable "baremetal_worker_count" {
  description = "Number of worker nodes (5-10 for production)"
  type        = number
  default     = 5

  validation {
    condition     = var.baremetal_worker_count >= 5 && var.baremetal_worker_count <= 10
    error_message = "Production requires 5-10 worker nodes."
  }
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
  
  validation {
    condition     = length(var.baremetal_worker_hosts) >= 5 && length(var.baremetal_worker_hosts) <= 10
    error_message = "Production requires 5-10 worker hosts."
  }
}

# ============================================================================
# Bare Metal HCD Configuration
# ============================================================================

variable "baremetal_hcd_count" {
  description = "Number of HCD nodes (also used as Ceph storage nodes)"
  type        = number
  default     = 3

  validation {
    condition     = var.baremetal_hcd_count == 3
    error_message = "Production requires exactly 3 HCD nodes for Ceph quorum."
  }
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
  
  validation {
    condition     = length(var.baremetal_hcd_hosts) == 3
    error_message = "Production requires exactly 3 HCD hosts."
  }
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
  
  validation {
    condition     = length(var.baremetal_ipmi_password) >= 16
    error_message = "Production IPMI password must be at least 16 characters."
  }
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
  default     = "~/.ssh/id_rsa_prod"
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
}

variable "baremetal_dns_servers" {
  description = "DNS servers (production should use internal DNS)"
  type        = list(string)
  default     = ["10.0.0.10", "10.0.0.11"]
}

variable "baremetal_domain" {
  description = "Domain name for cluster"
  type        = string
  default     = "prod.example.com"
}

variable "baremetal_worker_cidr" {
  description = "CIDR for worker nodes"
  type        = string
  default     = "10.10.2.0/24"
}

variable "baremetal_hcd_cidr" {
  description = "CIDR for HCD nodes"
  type        = string
  default     = "10.10.3.0/24"
}

# ============================================================================
# Load Balancer Configuration (Mandatory for Production)
# ============================================================================

variable "baremetal_metallb_ip_range" {
  description = "IP range for MetalLB load balancer"
  type        = string
  default     = "10.10.1.200-10.10.1.250"
}

variable "baremetal_load_balancer_ip" {
  description = "Virtual IP for API load balancer (MANDATORY for production)"
  type        = string
  
  validation {
    condition     = var.baremetal_load_balancer_ip != ""
    error_message = "Production requires a load balancer VIP for HA."
  }
}

# ============================================================================
# PXE Boot Configuration
# ============================================================================

variable "baremetal_pxe_server" {
  description = "PXE server address (if using network boot)"
  type        = string
  default     = ""
}

# ============================================================================
# Time Synchronization
# ============================================================================

variable "baremetal_ntp_servers" {
  description = "NTP servers for time synchronization (use internal NTP for production)"
  type        = list(string)
  default     = ["ntp1.example.com", "ntp2.example.com"]
}

# ============================================================================
# Storage Configuration
# ============================================================================

variable "baremetal_enable_nfs" {
  description = "Enable NFS storage class (in addition to Ceph)"
  type        = bool
  default     = false
}

# ============================================================================
# Monitoring Configuration
# ============================================================================

variable "enable_monitoring" {
  description = "Enable Prometheus + Grafana monitoring stack"
  type        = bool
  default     = true
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
  default     = ""
  
  validation {
    condition     = var.grafana_admin_password == "" || length(var.grafana_admin_password) >= 12
    error_message = "Grafana password must be at least 12 characters if set."
  }
}

variable "alert_slack_webhook_url" {
  description = "Slack webhook URL for alerts"
  type        = string
  sensitive   = true
  default     = ""
}

variable "alert_pagerduty_service_key" {
  description = "PagerDuty service key for critical alerts"
  type        = string
  sensitive   = true
  default     = ""
}

# ============================================================================
# Backup Configuration
# ============================================================================

variable "enable_automated_backups" {
  description = "Enable automated backups with Velero"
  type        = bool
  default     = true
}

variable "backup_s3_bucket" {
  description = "S3 bucket for backups"
  type        = string
  default     = "janusgraph-prod-backups"
}

variable "backup_s3_region" {
  description = "S3 region for backups"
  type        = string
  default     = "us-east-1"
}

variable "backup_s3_endpoint" {
  description = "S3 endpoint (for S3-compatible storage like MinIO)"
  type        = string
  default     = ""
}

# ============================================================================
# Security Configuration
# ============================================================================

variable "enable_security_hardening" {
  description = "Enable security hardening (Falco, OPA Gatekeeper, Pod Security Standards)"
  type        = bool
  default     = true
}

# ============================================================================
# Compliance Configuration
# ============================================================================

variable "compliance_standards" {
  description = "Compliance standards to enforce (SOC2, PCI-DSS, HIPAA)"
  type        = list(string)
  default     = ["SOC2", "PCI-DSS"]
  
  validation {
    condition = alltrue([
      for standard in var.compliance_standards :
      contains(["SOC2", "PCI-DSS", "HIPAA", "GDPR"], standard)
    ])
    error_message = "Compliance standards must be one of: SOC2, PCI-DSS, HIPAA, GDPR."
  }
}

variable "audit_log_retention_days" {
  description = "Number of days to retain audit logs"
  type        = number
  default     = 365
  
  validation {
    condition     = var.audit_log_retention_days >= 90
    error_message = "Production audit logs must be retained for at least 90 days."
  }
}

# ============================================================================
# High Availability Configuration
# ============================================================================

variable "enable_pod_disruption_budgets" {
  description = "Enable Pod Disruption Budgets for critical workloads"
  type        = bool
  default     = true
}

variable "enable_horizontal_pod_autoscaling" {
  description = "Enable Horizontal Pod Autoscaling"
  type        = bool
  default     = true
}

variable "enable_vertical_pod_autoscaling" {
  description = "Enable Vertical Pod Autoscaling"
  type        = bool
  default     = false
}

# ============================================================================
# Performance Configuration
# ============================================================================

variable "enable_node_local_dns" {
  description = "Enable NodeLocal DNSCache for better DNS performance"
  type        = bool
  default     = true
}

variable "enable_topology_aware_routing" {
  description = "Enable topology-aware routing for better performance"
  type        = bool
  default     = true
}

# ============================================================================
# Disaster Recovery Configuration
# ============================================================================

variable "enable_disaster_recovery" {
  description = "Enable disaster recovery features"
  type        = bool
  default     = true
}

variable "dr_backup_frequency" {
  description = "Disaster recovery backup frequency (hourly, daily, weekly)"
  type        = string
  default     = "daily"
  
  validation {
    condition     = contains(["hourly", "daily", "weekly"], var.dr_backup_frequency)
    error_message = "DR backup frequency must be hourly, daily, or weekly."
  }
}

variable "dr_rpo_hours" {
  description = "Recovery Point Objective in hours"
  type        = number
  default     = 4
  
  validation {
    condition     = var.dr_rpo_hours >= 1 && var.dr_rpo_hours <= 24
    error_message = "RPO must be between 1 and 24 hours."
  }
}

variable "dr_rto_hours" {
  description = "Recovery Time Objective in hours"
  type        = number
  default     = 8
  
  validation {
    condition     = var.dr_rto_hours >= 1 && var.dr_rto_hours <= 48
    error_message = "RTO must be between 1 and 48 hours."
  }
}