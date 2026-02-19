# OpenShift Cluster Module
# Provisions OpenShift cluster on AWS/Azure/GCP

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    vsphere = {
      source  = "hashicorp/vsphere"
      version = "~> 2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}

# Local variables
locals {
  cluster_name = var.cluster_name
  common_tags = merge(
    var.tags,
    {
      "kubernetes.io/cluster/${var.cluster_name}" = "owned"
      "Project"                                    = "janusgraph-banking"
      "ManagedBy"                                  = "terraform"
      "Environment"                                = var.environment
    }
  )
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

# EKS Cluster (AWS)
resource "aws_eks_cluster" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name     = local.cluster_name
  role_arn = aws_iam_role.cluster[0].arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = var.enable_public_access
    public_access_cidrs     = var.public_access_cidrs
    security_group_ids      = [aws_security_group.cluster[0].id]
  }

  encryption_config {
    provider {
      key_arn = var.kms_key_arn
    }
    resources = ["secrets"]
  }

  enabled_cluster_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler"
  ]

  tags = local.common_tags

  depends_on = [
    aws_iam_role_policy_attachment.cluster_policy[0],
    aws_iam_role_policy_attachment.vpc_resource_controller[0]
  ]
}

# IAM Role for EKS Cluster
resource "aws_iam_role" "cluster" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name = "${local.cluster_name}-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

# Attach required policies
resource "aws_iam_role_policy_attachment" "cluster_policy" {
  count = var.cloud_provider == "aws" ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.cluster[0].name
}

resource "aws_iam_role_policy_attachment" "vpc_resource_controller" {
  count = var.cloud_provider == "aws" ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.cluster[0].name
}

# Security Group for Cluster
resource "aws_security_group" "cluster" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name        = "${local.cluster_name}-cluster-sg"
  description = "Security group for ${local.cluster_name} EKS cluster"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.cluster_name}-cluster-sg"
    }
  )
}

# EKS Node Group
resource "aws_eks_node_group" "main" {
  count = var.cloud_provider == "aws" ? 1 : 0

  cluster_name    = aws_eks_cluster.main[0].name
  node_group_name = "${local.cluster_name}-node-group"
  node_role_arn   = aws_iam_role.node[0].arn
  subnet_ids      = var.subnet_ids

  scaling_config {
    desired_size = var.node_count
    max_size     = var.node_count_max
    min_size     = var.node_count_min
  }

  instance_types = [var.instance_type]
  capacity_type  = var.capacity_type
  disk_size      = var.disk_size

  labels = {
    Environment = var.environment
    Project     = "janusgraph-banking"
  }

  tags = local.common_tags

  depends_on = [
    aws_iam_role_policy_attachment.node_policy[0],
    aws_iam_role_policy_attachment.cni_policy[0],
    aws_iam_role_policy_attachment.registry_policy[0]
  ]
}

# IAM Role for Node Group
resource "aws_iam_role" "node" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name = "${local.cluster_name}-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

# Attach required policies to node role
resource "aws_iam_role_policy_attachment" "node_policy" {
  count = var.cloud_provider == "aws" ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.node[0].name
}

resource "aws_iam_role_policy_attachment" "cni_policy" {
  count = var.cloud_provider == "aws" ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.node[0].name
}

resource "aws_iam_role_policy_attachment" "registry_policy" {
  count = var.cloud_provider == "aws" ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.node[0].name
}

# EBS CSI Driver IAM Role
resource "aws_iam_role" "ebs_csi" {
  count = var.cloud_provider == "aws" && var.enable_ebs_csi ? 1 : 0

  name = "${local.cluster_name}-ebs-csi-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRoleWithWebIdentity"
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.cluster[0].arn
      }
      Condition = {
        StringEquals = {
          "${replace(aws_iam_openid_connect_provider.cluster[0].url, "https://", "")}:sub" = "system:serviceaccount:kube-system:ebs-csi-controller-sa"
        }
      }
    }]
  })

  tags = local.common_tags
}

# OIDC Provider for IRSA
resource "aws_iam_openid_connect_provider" "cluster" {
  count = var.cloud_provider == "aws" ? 1 : 0

  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.cluster[0].certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main[0].identity[0].oidc[0].issuer

  tags = local.common_tags
}

data "tls_certificate" "cluster" {
  count = var.cloud_provider == "aws" ? 1 : 0

  url = aws_eks_cluster.main[0].identity[0].oidc[0].issuer
}

# EBS CSI Driver Addon
resource "aws_eks_addon" "ebs_csi" {
  count = var.cloud_provider == "aws" && var.enable_ebs_csi ? 1 : 0

  cluster_name             = aws_eks_cluster.main[0].name
  addon_name               = "aws-ebs-csi-driver"
  addon_version            = var.ebs_csi_version
  service_account_role_arn = aws_iam_role.ebs_csi[0].arn

  tags = local.common_tags
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "cluster" {
  count = var.cloud_provider == "aws" ? 1 : 0

  name              = "/aws/eks/${local.cluster_name}/cluster"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}