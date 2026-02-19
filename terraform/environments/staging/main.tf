/**
 * Staging Environment Configuration
 * 
 * Deploys JanusGraph Banking Platform to staging environment.
 * Uses production-like configuration with reduced resources.
 * 
 * Version: 1.0
 * Date: 2026-02-19
 */

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }

  backend "s3" {
    bucket         = "janusgraph-banking-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "janusgraph-banking-terraform-locks"
  }
}

# ============================================================================
# Provider Configuration
# ============================================================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "staging"
      Project     = "janusgraph-banking"
      ManagedBy   = "terraform"
      CostCenter  = "engineering"
    }
  }
}

provider "kubernetes" {
  host                   = module.openshift_cluster.cluster_endpoint
  cluster_ca_certificate = base64decode(module.openshift_cluster.cluster_ca_certificate)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = [
      "eks",
      "get-token",
      "--cluster-name",
      module.openshift_cluster.cluster_name
    ]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.openshift_cluster.cluster_endpoint
    cluster_ca_certificate = base64decode(module.openshift_cluster.cluster_ca_certificate)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args = [
        "eks",
        "get-token",
        "--cluster-name",
        module.openshift_cluster.cluster_name
      ]
    }
  }
}

# ============================================================================
# Data Sources
# ============================================================================

data "aws_availability_zones" "available" {
  state = "available"
}

# ============================================================================
# Networking Module
# ============================================================================

module "networking" {
  source = "../../modules/networking"

  cluster_name       = var.cluster_name
  region             = var.aws_region
  vpc_cidr           = var.vpc_cidr
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 3)

  enable_nat_gateway   = true
  enable_vpc_endpoints = true
  enable_flow_logs     = true

  tags = {
    Environment = "staging"
    Project     = "janusgraph-banking"
  }
}

# ============================================================================
# OpenShift Cluster Module
# ============================================================================

module "openshift_cluster" {
  source = "../../modules/openshift-cluster"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version
  region          = var.aws_region

  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids

  node_groups = {
    general = {
      desired_size   = 3
      min_size       = 3
      max_size       = 6
      instance_types = ["m5.xlarge"]
      disk_size      = 100
      labels = {
        role = "general"
      }
    }
    hcd = {
      desired_size   = 3
      min_size       = 3
      max_size       = 6
      instance_types = ["r5.2xlarge"]
      disk_size      = 500
      labels = {
        role = "hcd"
      }
      taints = [
        {
          key    = "workload"
          value  = "hcd"
          effect = "NoSchedule"
        }
      ]
    }
  }

  enable_irsa                    = true
  enable_cluster_autoscaler      = true
  enable_metrics_server          = true
  enable_aws_load_balancer_controller = true

  tags = {
    Environment = "staging"
    Project     = "janusgraph-banking"
  }
}

# ============================================================================
# Storage Module
# ============================================================================

module "storage" {
  source = "../../modules/storage"

  cluster_name       = var.cluster_name
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 3)
  kms_key_id         = var.kms_key_id
  kms_key_arn        = var.kms_key_arn

  # HCD Storage (production-like)
  hcd_volume_type    = "io2"
  hcd_iops           = 8000
  hcd_reclaim_policy = "Retain"

  # JanusGraph Storage
  janusgraph_volume_type    = "gp3"
  janusgraph_reclaim_policy = "Retain"

  # OpenSearch Storage
  opensearch_volume_type    = "gp3"
  opensearch_reclaim_policy = "Retain"

  # Pulsar Storage
  pulsar_volume_type    = "gp3"
  pulsar_reclaim_policy = "Retain"

  # Backup Configuration
  backup_retention_days   = 14
  backup_transition_days  = 3
  snapshot_retention_days = 7

  tags = {
    Environment = "staging"
    Project     = "janusgraph-banking"
  }

  depends_on = [module.openshift_cluster]
}

# ============================================================================
# Monitoring Module
# ============================================================================

module "monitoring" {
  source = "../../modules/monitoring"

  environment          = "staging"
  storage_class_name   = module.storage.general_storage_class_name
  monitoring_namespace = "monitoring"

  # Prometheus Configuration
  prometheus_retention      = "14d"
  prometheus_storage_size   = "50Gi"
  prometheus_cpu_request    = "500m"
  prometheus_memory_request = "2Gi"
  prometheus_cpu_limit      = "1000m"
  prometheus_memory_limit   = "4Gi"

  # Grafana Configuration
  grafana_admin_password = var.grafana_admin_password
  grafana_storage_size   = "5Gi"

  # AlertManager Configuration
  alertmanager_storage_size = "5Gi"
  slack_webhook_url         = var.slack_webhook_url
  slack_channel             = "#staging-alerts"
  pagerduty_service_key     = var.pagerduty_service_key

  # Loki Configuration
  enable_loki         = true
  loki_storage_size   = "25Gi"
  loki_retention_period = "168h" # 7 days

  # Jaeger Configuration
  enable_jaeger = true

  # Ingress Configuration
  enable_ingress           = true
  prometheus_hostname      = "prometheus-staging.${var.domain_name}"
  grafana_hostname         = "grafana-staging.${var.domain_name}"
  alertmanager_hostname    = "alertmanager-staging.${var.domain_name}"
  jaeger_hostname          = "jaeger-staging.${var.domain_name}"

  depends_on = [module.openshift_cluster, module.storage]
}

# ============================================================================
# Outputs
# ============================================================================

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.openshift_cluster.cluster_endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.openshift_cluster.cluster_name
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "monitoring_urls" {
  description = "Monitoring service URLs"
  value       = module.monitoring.access_instructions
}

output "kubeconfig_command" {
  description = "Command to update kubeconfig"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.openshift_cluster.cluster_name}"
}