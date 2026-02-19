# VMware vSphere Staging Environment
# Purpose: Development and testing environment for on-premises deployment
# Cluster Size: 3-5 nodes (1 control plane, 2-4 workers, 3 HCD nodes)
# Cost: On-premises CapEx (hardware already owned)

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    vsphere = {
      source  = "hashicorp/vsphere"
      version = "~> 2.6"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }
  
  backend "s3" {
    bucket = "janusgraph-terraform-state"
    key    = "vsphere-staging/terraform.tfstate"
    region = "us-east-1"
    
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}

# vSphere Provider Configuration
provider "vsphere" {
  user                 = var.vsphere_user
  password             = var.vsphere_password
  vsphere_server       = var.vsphere_server
  allow_unverified_ssl = var.vsphere_allow_unverified_ssl
}

# Kubernetes Provider (configured after cluster creation)
provider "kubernetes" {
  host                   = module.openshift_cluster.kubeconfig_host
  cluster_ca_certificate = base64decode(module.openshift_cluster.kubeconfig_ca_cert)
  token                  = module.openshift_cluster.kubeconfig_token
}

# Helm Provider (configured after cluster creation)
provider "helm" {
  kubernetes {
    host                   = module.openshift_cluster.kubeconfig_host
    cluster_ca_certificate = base64decode(module.openshift_cluster.kubeconfig_ca_cert)
    token                  = module.openshift_cluster.kubeconfig_token
  }
}

# Local Variables
locals {
  cluster_name = "janusgraph-vsphere-staging"
  environment  = "staging"
  
  common_tags = {
    Environment = "staging"
    ManagedBy   = "terraform"
    Project     = "janusgraph-banking"
    CostCenter  = "engineering"
    Owner       = "platform-team"
  }
  
  # vSphere-specific settings
  vsphere_datacenter = var.vsphere_datacenter
  vsphere_cluster    = var.vsphere_cluster
  vsphere_datastore  = var.vsphere_datastore
  vsphere_folder     = "janusgraph-staging"
  vsphere_domain     = "staging.janusgraph.local"
  
  # Network configuration
  network_cidr = "10.100.0.0/24"
  gateway      = "10.100.0.1"
  dns_servers  = ["10.100.0.10", "10.100.0.11"]
  
  # VM sizing for staging (smaller than production)
  control_plane_count  = 1
  control_plane_cpu    = 4
  control_plane_memory = 16384  # 16 GB
  
  worker_count  = 2
  worker_cpu    = 8
  worker_memory = 32768  # 32 GB
  
  hcd_count         = 3
  hcd_cpu           = 16
  hcd_memory        = 131072  # 128 GB
  hcd_data_disk_size = 512    # 512 GB (smaller than prod)
}

# OpenShift/Kubernetes Cluster Module
module "openshift_cluster" {
  source = "../../modules/openshift-cluster"
  
  # Cloud Provider
  cloud_provider = "vsphere"
  
  # Cluster Configuration
  cluster_name    = local.cluster_name
  cluster_version = "4.14"
  
  # vSphere Configuration
  vsphere_datacenter      = local.vsphere_datacenter
  vsphere_cluster         = local.vsphere_cluster
  vsphere_datastore       = local.vsphere_datastore
  vsphere_folder          = local.vsphere_folder
  vsphere_resource_pool   = "janusgraph-staging"
  vsphere_template        = "rhcos-4.14-template"
  vsphere_domain          = local.vsphere_domain
  vsphere_network_name    = "VM Network"
  vsphere_network_cidr    = local.network_cidr
  vsphere_gateway         = local.gateway
  vsphere_dns_servers     = local.dns_servers
  
  # Control Plane Configuration
  vsphere_control_plane_count  = local.control_plane_count
  vsphere_control_plane_cpu    = local.control_plane_cpu
  vsphere_control_plane_memory = local.control_plane_memory
  vsphere_control_plane_disk   = 100  # GB
  
  # Worker Configuration
  vsphere_worker_count  = local.worker_count
  vsphere_worker_cpu    = local.worker_cpu
  vsphere_worker_memory = local.worker_memory
  vsphere_worker_disk   = 200  # GB
  
  # HCD Configuration
  vsphere_hcd_count         = local.hcd_count
  vsphere_hcd_cpu           = local.hcd_cpu
  vsphere_hcd_memory        = local.hcd_memory
  vsphere_hcd_disk          = 100  # OS disk
  vsphere_hcd_data_disk_size = local.hcd_data_disk_size
  
  # Load Balancer Configuration
  vsphere_lb_cpu    = 2
  vsphere_lb_memory = 4096  # 4 GB
  vsphere_lb_disk   = 50    # GB
  
  # Tags
  tags = local.common_tags
}

# Networking Module
module "networking" {
  source = "../../modules/networking"
  
  # Cloud Provider
  cloud_provider = "vsphere"
  
  # Cluster Configuration
  cluster_name = local.cluster_name
  
  # vSphere Configuration
  vsphere_datacenter           = local.vsphere_datacenter
  vsphere_network_name         = "VM Network"
  vsphere_use_distributed_switch = false  # Use standard switch for staging
  vsphere_vlan_id              = 100
  
  # Tags
  tags = local.common_tags
  
  depends_on = [module.openshift_cluster]
}

# Storage Module
module "storage" {
  source = "../../modules/storage"
  
  # Cloud Provider
  cloud_provider = "vsphere"
  
  # Cluster Configuration
  cluster_name = local.cluster_name
  
  # vSphere Configuration
  vsphere_datacenter    = local.vsphere_datacenter
  vsphere_datastore_name = local.vsphere_datastore
  vsphere_datastore_url = "ds:///vmfs/volumes/${local.vsphere_datastore}/"
  
  # Storage Policies (staging uses default policies)
  vsphere_hcd_storage_policy        = "vSAN Default Storage Policy"
  vsphere_janusgraph_storage_policy = "vSAN Default Storage Policy"
  vsphere_opensearch_storage_policy = "vSAN Default Storage Policy"
  vsphere_pulsar_storage_policy     = "vSAN Default Storage Policy"
  
  # Optional Storage Backends
  vsphere_enable_nfs  = false  # Disabled for staging
  vsphere_enable_vsan = true   # Enabled for staging
  
  # Tags
  tags = local.common_tags
  
  depends_on = [module.openshift_cluster]
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"
  
  # Cluster Configuration
  cluster_name = local.cluster_name
  environment  = local.environment
  
  # Monitoring Configuration
  enable_prometheus     = true
  enable_grafana        = true
  enable_alertmanager   = true
  enable_loki           = false  # Disabled for staging to save resources
  enable_jaeger         = false  # Disabled for staging
  
  # Resource Limits (smaller for staging)
  prometheus_storage_size = "50Gi"
  grafana_storage_size    = "10Gi"
  alertmanager_storage_size = "10Gi"
  
  # Retention Policies (shorter for staging)
  prometheus_retention = "7d"
  loki_retention       = "3d"
  
  # Alert Configuration
  alertmanager_config = {
    slack_webhook_url = var.slack_webhook_url
    pagerduty_key     = var.pagerduty_key
    email_to          = "platform-team@example.com"
  }
  
  # Tags
  tags = local.common_tags
  
  depends_on = [module.storage]
}

# Outputs
output "cluster_endpoint" {
  description = "Kubernetes API endpoint"
  value       = module.openshift_cluster.cluster_endpoint
  sensitive   = true
}

output "kubeconfig" {
  description = "Kubeconfig for cluster access"
  value       = module.openshift_cluster.kubeconfig
  sensitive   = true
}

output "control_plane_ips" {
  description = "Control plane node IP addresses"
  value       = module.openshift_cluster.control_plane_ips
}

output "worker_ips" {
  description = "Worker node IP addresses"
  value       = module.openshift_cluster.worker_ips
}

output "hcd_ips" {
  description = "HCD node IP addresses"
  value       = module.openshift_cluster.hcd_ips
}

output "load_balancer_ip" {
  description = "Load balancer IP address"
  value       = module.openshift_cluster.load_balancer_ip
}

output "storage_classes" {
  description = "Available storage classes"
  value       = module.storage.storage_classes
}

output "monitoring_endpoints" {
  description = "Monitoring service endpoints"
  value = {
    prometheus    = "http://${module.openshift_cluster.load_balancer_ip}:9090"
    grafana       = "http://${module.openshift_cluster.load_balancer_ip}:3000"
    alertmanager  = "http://${module.openshift_cluster.load_balancer_ip}:9093"
  }
}