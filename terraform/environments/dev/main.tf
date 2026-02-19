# Development Environment Configuration
# JanusGraph Banking Platform - Dev Environment

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state backend (configure after initial setup)
  # backend "s3" {
  #   bucket         = "janusgraph-terraform-state-dev"
  #   key            = "environments/dev/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-state-lock-dev"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "janusgraph-banking"
      Environment = "dev"
      ManagedBy   = "terraform"
      Owner       = "platform-engineering"
    }
  }
}

# Local variables
locals {
  cluster_name = "janusgraph-banking-dev"
  environment  = "dev"
  
  common_tags = {
    Project     = "janusgraph-banking"
    Environment = local.environment
    ManagedBy   = "terraform"
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC Module
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${local.cluster_name}-vpc"
  cidr = var.vpc_cidr

  azs             = slice(data.aws_availability_zones.available.names, 0, 3)
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_nat_gateway   = true
  single_nat_gateway   = true  # Dev: single NAT for cost savings
  enable_dns_hostnames = true
  enable_dns_support   = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }

  tags = local.common_tags
}

# OpenShift/EKS Cluster Module
module "openshift_cluster" {
  source = "../../modules/openshift-cluster"

  cluster_name       = local.cluster_name
  environment        = local.environment
  cloud_provider     = "aws"
  kubernetes_version = var.kubernetes_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  node_count     = var.node_count
  node_count_min = var.node_count_min
  node_count_max = var.node_count_max
  instance_type  = var.instance_type
  capacity_type  = "ON_DEMAND"
  disk_size      = 100

  enable_public_access = true
  public_access_cidrs  = var.public_access_cidrs

  enable_ebs_csi = true
  
  log_retention_days = 7  # Dev: shorter retention

  tags = local.common_tags
}

# Storage Module (placeholder - to be implemented)
# module "storage" {
#   source = "../../modules/storage"
#   
#   cluster_name = local.cluster_name
#   environment  = local.environment
#   
#   tags = local.common_tags
# }

# Monitoring Module (placeholder - to be implemented)
# module "monitoring" {
#   source = "../../modules/monitoring"
#   
#   cluster_name = local.cluster_name
#   environment  = local.environment
#   
#   tags = local.common_tags
# }