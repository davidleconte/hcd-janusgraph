/**
 * Bare Metal Staging Environment
 * 
 * This configuration deploys a Kubernetes cluster on bare metal infrastructure
 * for staging/testing purposes.
 * 
 * Architecture:
 * - 1 Control Plane Node (HA can be enabled with 3 nodes)
 * - 2-3 Worker Nodes
 * - 3 HCD Nodes (also used as Ceph storage nodes)
 * - Ceph distributed storage
 * - MetalLB load balancer
 * - HAProxy + Keepalived for API HA (optional)
 * 
 * Version: 1.0
 * Date: 2026-02-19
 */

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

# ============================================================================
# Local Variables
# ============================================================================

locals {
  cluster_name = "janusgraph-baremetal-staging"
  environment  = "staging"
  
  common_tags = {
    Environment = local.environment
    Project     = "JanusGraph Banking Platform"
    ManagedBy   = "Terraform"
    Platform    = "BareMetal"
  }
}

# ============================================================================
# OpenShift/Kubernetes Cluster Module
# ============================================================================

module "cluster" {
  source = "../../modules/openshift-cluster"

  cluster_name     = local.cluster_name
  environment      = local.environment
  cloud_provider   = "baremetal"
  
  # Kubernetes version
  kubernetes_version = "1.28"
  
  # Bare metal configuration
  baremetal_control_plane_count = var.baremetal_control_plane_count
  baremetal_control_plane_hosts = var.baremetal_control_plane_hosts
  
  baremetal_worker_count = var.baremetal_worker_count
  baremetal_worker_hosts = var.baremetal_worker_hosts
  
  baremetal_hcd_count = var.baremetal_hcd_count
  baremetal_hcd_hosts = var.baremetal_hcd_hosts
  
  # IPMI credentials
  baremetal_ipmi_user     = var.baremetal_ipmi_user
  baremetal_ipmi_password = var.baremetal_ipmi_password
  
  # SSH configuration
  baremetal_ssh_user             = var.baremetal_ssh_user
  baremetal_ssh_private_key_path = var.baremetal_ssh_private_key_path
  
  # Network configuration
  baremetal_pod_network_cidr = var.baremetal_pod_network_cidr
  baremetal_service_cidr     = var.baremetal_service_cidr
  baremetal_gateway          = var.baremetal_gateway
  baremetal_dns_servers      = var.baremetal_dns_servers
  baremetal_domain           = var.baremetal_domain
  
  # MetalLB configuration
  baremetal_metallb_ip_range = var.baremetal_metallb_ip_range
  
  # Load balancer (optional - for HA)
  baremetal_load_balancer_ip = var.baremetal_load_balancer_ip
  
  # PXE server (if using network boot)
  baremetal_pxe_server = var.baremetal_pxe_server
  
  # NTP servers
  baremetal_ntp_servers = var.baremetal_ntp_servers
  
  # Not used for bare metal
  vpc_id     = ""
  subnet_ids = []
  
  tags = local.common_tags
}

# ============================================================================
# Networking Module
# ============================================================================

module "networking" {
  source = "../../modules/networking"

  cluster_name   = local.cluster_name
  environment    = local.environment
  cloud_provider = "baremetal"
  
  # Bare metal network configuration
  baremetal_control_plane_count = var.baremetal_control_plane_count
  baremetal_control_plane_hosts = var.baremetal_control_plane_hosts
  
  baremetal_worker_count = var.baremetal_worker_count
  baremetal_worker_hosts = var.baremetal_worker_hosts
  
  baremetal_hcd_count = var.baremetal_hcd_count
  baremetal_hcd_hosts = var.baremetal_hcd_hosts
  
  baremetal_ssh_user             = var.baremetal_ssh_user
  baremetal_ssh_private_key_path = var.baremetal_ssh_private_key_path
  
  baremetal_gateway          = var.baremetal_gateway
  baremetal_dns_servers      = var.baremetal_dns_servers
  baremetal_domain           = var.baremetal_domain
  baremetal_load_balancer_ip = var.baremetal_load_balancer_ip
  
  baremetal_worker_cidr = var.baremetal_worker_cidr
  baremetal_hcd_cidr    = var.baremetal_hcd_cidr
  
  # Not used for bare metal
  region             = ""
  vpc_cidr           = ""
  availability_zones = []
  
  tags = local.common_tags
}

# ============================================================================
# Storage Module
# ============================================================================

module "storage" {
  source = "../../modules/storage"

  cluster_name   = local.cluster_name
  environment    = local.environment
  cloud_provider = "baremetal"
  
  # Bare metal storage configuration (Ceph)
  baremetal_hcd_count = var.baremetal_hcd_count
  baremetal_hcd_hosts = var.baremetal_hcd_hosts
  
  baremetal_control_plane_count = var.baremetal_control_plane_count
  baremetal_control_plane_hosts = var.baremetal_control_plane_hosts
  
  baremetal_worker_count = var.baremetal_worker_count
  baremetal_worker_hosts = var.baremetal_worker_hosts
  
  baremetal_ssh_user             = var.baremetal_ssh_user
  baremetal_ssh_private_key_path = var.baremetal_ssh_private_key_path
  
  baremetal_hcd_cidr    = var.baremetal_hcd_cidr
  baremetal_worker_cidr = var.baremetal_worker_cidr
  
  # Ceph configuration
  baremetal_ceph_pool_pg_num  = 128
  baremetal_ceph_replica_size = 3
  baremetal_ceph_min_size     = 2
  
  # NFS (optional)
  baremetal_enable_nfs = var.baremetal_enable_nfs
  
  # Reclaim policies (staging - can delete)
  hcd_reclaim_policy        = "Delete"
  janusgraph_reclaim_policy = "Delete"
  opensearch_reclaim_policy = "Delete"
  pulsar_reclaim_policy     = "Delete"
  
  # Not used for bare metal
  availability_zones = []
  
  tags = local.common_tags
  
  depends_on = [module.cluster, module.networking]
}

# ============================================================================
# Outputs
# ============================================================================

output "cluster_name" {
  description = "Name of the Kubernetes cluster"
  value       = local.cluster_name
}

output "environment" {
  description = "Environment name"
  value       = local.environment
}

output "control_plane_ips" {
  description = "IP addresses of control plane nodes"
  value       = module.networking.control_plane_ips
}

output "worker_ips" {
  description = "IP addresses of worker nodes"
  value       = module.networking.worker_ips
}

output "hcd_ips" {
  description = "IP addresses of HCD nodes"
  value       = module.networking.hcd_ips
}

output "api_endpoint" {
  description = "Kubernetes API endpoint"
  value       = module.networking.api_endpoint
}

output "load_balancer_ip" {
  description = "Load balancer virtual IP (if configured)"
  value       = module.networking.load_balancer_ip
}

output "storage_classes" {
  description = "Available storage classes"
  value       = module.storage.storage_classes
}

output "ceph_dashboard_url" {
  description = "Ceph dashboard URL"
  value       = module.storage.ceph_dashboard_url
}

output "kubeconfig_command" {
  description = "Command to get kubeconfig"
  value       = "scp ${var.baremetal_ssh_user}@${var.baremetal_control_plane_hosts[0].ip_address}:/etc/kubernetes/admin.conf ~/.kube/config"
}