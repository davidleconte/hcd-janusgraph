/**
 * Bare Metal Production Environment
 * 
 * This configuration deploys a production-grade Kubernetes cluster on bare metal
 * infrastructure with high availability and enterprise features.
 * 
 * Architecture:
 * - 3 Control Plane Nodes (HA with etcd quorum)
 * - 5-10 Worker Nodes (auto-scaling capable)
 * - 3 HCD Nodes (also used as Ceph storage nodes)
 * - Ceph distributed storage with 3x replication
 * - MetalLB load balancer
 * - HAProxy + Keepalived for API HA (mandatory)
 * - Enhanced monitoring and alerting
 * - Automated backups
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

  # Production uses remote backend (S3, GCS, or Terraform Cloud)
  backend "s3" {
    bucket         = "janusgraph-terraform-state"
    key            = "baremetal-prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

# ============================================================================
# Local Variables
# ============================================================================

locals {
  cluster_name = "janusgraph-baremetal-prod"
  environment  = "production"
  
  common_tags = {
    Environment = local.environment
    Project     = "JanusGraph Banking Platform"
    ManagedBy   = "Terraform"
    Platform    = "BareMetal"
    CostCenter  = "Infrastructure"
    Compliance  = "SOC2,PCI-DSS"
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
  
  # Bare metal configuration - HA setup
  baremetal_control_plane_count = var.baremetal_control_plane_count
  baremetal_control_plane_hosts = var.baremetal_control_plane_hosts
  
  baremetal_worker_count = var.baremetal_worker_count
  baremetal_worker_hosts = var.baremetal_worker_hosts
  
  baremetal_hcd_count = var.baremetal_hcd_count
  baremetal_hcd_hosts = var.baremetal_hcd_hosts
  
  # IPMI credentials (from Vault or secure storage)
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
  
  # Load balancer (mandatory for production HA)
  baremetal_load_balancer_ip = var.baremetal_load_balancer_ip
  
  # PXE server (if using network boot)
  baremetal_pxe_server = var.baremetal_pxe_server
  
  # NTP servers (critical for production)
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
  
  # Ceph configuration - production settings
  baremetal_ceph_pool_pg_num  = 256  # Higher for production
  baremetal_ceph_replica_size = 3    # 3x replication
  baremetal_ceph_min_size     = 2    # Minimum 2 replicas
  
  # NFS (optional, for legacy workloads)
  baremetal_enable_nfs = var.baremetal_enable_nfs
  
  # Reclaim policies (production - retain data)
  hcd_reclaim_policy        = "Retain"
  janusgraph_reclaim_policy = "Retain"
  opensearch_reclaim_policy = "Retain"
  pulsar_reclaim_policy     = "Retain"
  
  # Backup configuration
  backup_retention_days   = 90   # 90 days for production
  snapshot_retention_days = 30   # 30 days for snapshots
  
  # Not used for bare metal
  availability_zones = []
  
  tags = local.common_tags
  
  depends_on = [module.cluster, module.networking]
}

# ============================================================================
# Monitoring Module (Optional)
# ============================================================================

module "monitoring" {
  source = "../../modules/monitoring"
  count  = var.enable_monitoring ? 1 : 0

  cluster_name   = local.cluster_name
  environment    = local.environment
  cloud_provider = "baremetal"
  
  # Prometheus configuration
  prometheus_retention_days    = 90
  prometheus_storage_size      = "500Gi"
  prometheus_storage_class     = "general-storage"
  
  # Grafana configuration
  grafana_admin_password = var.grafana_admin_password
  grafana_storage_size   = "50Gi"
  grafana_storage_class  = "general-storage"
  
  # AlertManager configuration
  alertmanager_storage_size  = "20Gi"
  alertmanager_storage_class = "general-storage"
  
  # Slack/PagerDuty integration
  alert_slack_webhook_url    = var.alert_slack_webhook_url
  alert_pagerduty_service_key = var.alert_pagerduty_service_key
  
  tags = local.common_tags
  
  depends_on = [module.storage]
}

# ============================================================================
# Backup Configuration
# ============================================================================

resource "null_resource" "backup_configuration" {
  count = var.enable_automated_backups ? 1 : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_control_plane_hosts[0].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Install Velero for Kubernetes backups",
      "wget https://github.com/vmware-tanzu/velero/releases/download/v1.12.0/velero-v1.12.0-linux-amd64.tar.gz",
      "tar -xvf velero-v1.12.0-linux-amd64.tar.gz",
      "mv velero-v1.12.0-linux-amd64/velero /usr/local/bin/",
      "",
      "# Configure Velero with S3-compatible storage",
      "kubectl create namespace velero",
      "velero install \\",
      "  --provider aws \\",
      "  --plugins velero/velero-plugin-for-aws:v1.8.0 \\",
      "  --bucket ${var.backup_s3_bucket} \\",
      "  --backup-location-config region=${var.backup_s3_region},s3Url=${var.backup_s3_endpoint} \\",
      "  --snapshot-location-config region=${var.backup_s3_region} \\",
      "  --secret-file ./velero-credentials",
      "",
      "# Create backup schedule",
      "velero schedule create daily-backup \\",
      "  --schedule='0 2 * * *' \\",
      "  --ttl 2160h0m0s \\",
      "  --include-namespaces banking,monitoring",
      "",
      "# Create weekly full backup",
      "velero schedule create weekly-full-backup \\",
      "  --schedule='0 3 * * 0' \\",
      "  --ttl 4320h0m0s"
    ]
  }

  depends_on = [module.storage]
}

# ============================================================================
# Security Hardening
# ============================================================================

resource "null_resource" "security_hardening" {
  count = var.enable_security_hardening ? 1 : 0

  connection {
    type        = "ssh"
    host        = var.baremetal_control_plane_hosts[0].ip_address
    user        = var.baremetal_ssh_user
    private_key = file(var.baremetal_ssh_private_key_path)
  }

  provisioner "remote-exec" {
    inline = [
      "# Install Falco for runtime security",
      "helm repo add falcosecurity https://falcosecurity.github.io/charts",
      "helm repo update",
      "helm install falco falcosecurity/falco \\",
      "  --namespace falco \\",
      "  --create-namespace \\",
      "  --set falco.grpc.enabled=true \\",
      "  --set falco.grpcOutput.enabled=true",
      "",
      "# Install OPA Gatekeeper for policy enforcement",
      "kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.14/deploy/gatekeeper.yaml",
      "",
      "# Enable Pod Security Standards",
      "kubectl label namespace banking pod-security.kubernetes.io/enforce=restricted",
      "kubectl label namespace banking pod-security.kubernetes.io/audit=restricted",
      "kubectl label namespace banking pod-security.kubernetes.io/warn=restricted",
      "",
      "# Install cert-manager for certificate management",
      "kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml"
    ]
  }

  depends_on = [module.cluster]
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
  description = "Kubernetes API endpoint (via load balancer)"
  value       = module.networking.api_endpoint
}

output "load_balancer_ip" {
  description = "Load balancer virtual IP"
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

output "prometheus_url" {
  description = "Prometheus URL (if monitoring enabled)"
  value       = var.enable_monitoring ? "http://${module.networking.load_balancer_ip}:9090" : null
}

output "grafana_url" {
  description = "Grafana URL (if monitoring enabled)"
  value       = var.enable_monitoring ? "http://${module.networking.load_balancer_ip}:3000" : null
}

output "kubeconfig_command" {
  description = "Command to get kubeconfig"
  value       = "scp ${var.baremetal_ssh_user}@${var.baremetal_control_plane_hosts[0].ip_address}:/etc/kubernetes/admin.conf ~/.kube/config"
}

output "backup_status_command" {
  description = "Command to check backup status (if backups enabled)"
  value       = var.enable_automated_backups ? "kubectl exec -n velero deploy/velero -- velero backup get" : null
}