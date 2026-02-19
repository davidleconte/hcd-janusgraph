# VMware vSphere Production Environment
# Purpose: Production deployment for on-premises infrastructure
# Cluster Size: 5-10 nodes (3 control plane, 5-10 workers, 3 HCD nodes)
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
    key    = "vsphere-prod/terraform.tfstate"
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
  cluster_name = "janusgraph-vsphere-prod"
  environment  = "production"
  
  common_tags = {
    Environment = "production"
    ManagedBy   = "terraform"
    Project     = "janusgraph-banking"
    CostCenter  = "operations"
    Owner       = "platform-team"
    Compliance  = "pci-dss,sox"
    Criticality = "high"
  }
  
  # vSphere-specific settings
  vsphere_datacenter = var.vsphere_datacenter
  vsphere_cluster    = var.vsphere_cluster
  vsphere_datastore  = var.vsphere_datastore
  vsphere_folder     = "janusgraph-production"
  vsphere_domain     = "prod.janusgraph.local"
  
  # Network configuration (production network)
  network_cidr = "10.200.0.0/24"
  gateway      = "10.200.0.1"
  dns_servers  = ["10.200.0.10", "10.200.0.11"]
  
  # VM sizing for production (larger than staging)
  control_plane_count  = 3  # HA control plane
  control_plane_cpu    = 8
  control_plane_memory = 32768  # 32 GB
  
  worker_count  = 5  # Minimum for production
  worker_cpu    = 16
  worker_memory = 65536  # 64 GB
  
  hcd_count         = 3
  hcd_cpu           = 32
  hcd_memory        = 262144  # 256 GB
  hcd_data_disk_size = 2048   # 2 TB
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
  vsphere_resource_pool   = "janusgraph-production"
  vsphere_template        = "rhcos-4.14-template"
  vsphere_domain          = local.vsphere_domain
  vsphere_network_name    = "Production Network"
  vsphere_network_cidr    = local.network_cidr
  vsphere_gateway         = local.gateway
  vsphere_dns_servers     = local.dns_servers
  
  # Control Plane Configuration (HA)
  vsphere_control_plane_count  = local.control_plane_count
  vsphere_control_plane_cpu    = local.control_plane_cpu
  vsphere_control_plane_memory = local.control_plane_memory
  vsphere_control_plane_disk   = 200  # GB (larger for production)
  
  # Worker Configuration
  vsphere_worker_count  = local.worker_count
  vsphere_worker_cpu    = local.worker_cpu
  vsphere_worker_memory = local.worker_memory
  vsphere_worker_disk   = 500  # GB (larger for production)
  
  # HCD Configuration
  vsphere_hcd_count         = local.hcd_count
  vsphere_hcd_cpu           = local.hcd_cpu
  vsphere_hcd_memory        = local.hcd_memory
  vsphere_hcd_disk          = 200  # OS disk
  vsphere_hcd_data_disk_size = local.hcd_data_disk_size
  
  # Load Balancer Configuration
  vsphere_lb_cpu    = 4
  vsphere_lb_memory = 8192  # 8 GB
  vsphere_lb_disk   = 100   # GB
  
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
  vsphere_network_name         = "Production Network"
  vsphere_use_distributed_switch = true  # Use distributed switch for production
  vsphere_dvs_name             = "Production-DVS"
  vsphere_vlan_id              = 200
  
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
  
  # Storage Policies (production uses dedicated policies)
  vsphere_hcd_storage_policy        = "HCD Production Storage Policy"
  vsphere_janusgraph_storage_policy = "JanusGraph Production Storage Policy"
  vsphere_opensearch_storage_policy = "OpenSearch Production Storage Policy"
  vsphere_pulsar_storage_policy     = "Pulsar Production Storage Policy"
  
  # Optional Storage Backends
  vsphere_enable_nfs  = true   # Enabled for shared storage
  vsphere_nfs_server  = var.vsphere_nfs_server
  vsphere_nfs_path    = "/export/janusgraph-prod"
  vsphere_enable_vsan = true   # Enabled for production
  vsphere_vsan_policy = "Production vSAN Policy"
  
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
  
  # Monitoring Configuration (all features enabled for production)
  enable_prometheus     = true
  enable_grafana        = true
  enable_alertmanager   = true
  enable_loki           = true
  enable_jaeger         = true
  
  # Resource Limits (production sizing)
  prometheus_storage_size = "500Gi"
  grafana_storage_size    = "50Gi"
  alertmanager_storage_size = "50Gi"
  loki_storage_size       = "500Gi"
  jaeger_storage_size     = "100Gi"
  
  # Retention Policies (longer for production)
  prometheus_retention = "90d"
  loki_retention       = "30d"
  jaeger_retention     = "14d"
  
  # Alert Configuration
  alertmanager_config = {
    slack_webhook_url = var.slack_webhook_url
    pagerduty_key     = var.pagerduty_key
    email_to          = "platform-oncall@example.com"
    email_from        = "alerts@janusgraph.local"
  }
  
  # High Availability
  prometheus_replicas    = 2
  alertmanager_replicas  = 3
  grafana_replicas       = 2
  
  # Tags
  tags = local.common_tags
  
  depends_on = [module.storage]
}

# Backup Configuration
resource "kubernetes_cron_job_v1" "backup" {
  metadata {
    name      = "janusgraph-backup"
    namespace = "backup"
  }
  
  spec {
    schedule = "0 2 * * *"  # Daily at 2 AM
    
    job_template {
      metadata {
        name = "janusgraph-backup"
      }
      
      spec {
        template {
          metadata {
            labels = {
              app = "backup"
            }
          }
          
          spec {
            container {
              name  = "backup"
              image = "velero/velero:v1.12"
              
              command = [
                "/bin/sh",
                "-c",
                "velero backup create janusgraph-$(date +%Y%m%d-%H%M%S) --include-namespaces=hcd,janusgraph,opensearch,pulsar --wait"
              ]
              
              env {
                name  = "VELERO_NAMESPACE"
                value = "velero"
              }
            }
            
            restart_policy = "OnFailure"
          }
        }
      }
    }
  }
  
  depends_on = [module.monitoring]
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
    prometheus    = "https://${module.openshift_cluster.load_balancer_ip}:9090"
    grafana       = "https://${module.openshift_cluster.load_balancer_ip}:3000"
    alertmanager  = "https://${module.openshift_cluster.load_balancer_ip}:9093"
    loki          = "https://${module.openshift_cluster.load_balancer_ip}:3100"
    jaeger        = "https://${module.openshift_cluster.load_balancer_ip}:16686"
  }
}

output "backup_schedule" {
  description = "Backup schedule configuration"
  value = {
    schedule = "Daily at 2 AM UTC"
    retention = "90 days"
    namespaces = ["hcd", "janusgraph", "opensearch", "pulsar"]
  }
}