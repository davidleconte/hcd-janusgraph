# Terraform Infrastructure as Code

**Version**: 1.0  
**Date**: 2026-02-19  
**Status**: Active  
**Cloud Providers**: AWS, Azure, GCP

---

## Overview

This directory contains Terraform modules for provisioning and managing the infrastructure for the JanusGraph Banking Platform on Kubernetes/OpenShift.

### Architecture

```
terraform/
├── modules/              # Reusable Terraform modules
│   ├── openshift-cluster/   # OpenShift cluster provisioning
│   ├── networking/          # VPC, subnets, load balancers
│   ├── storage/             # StorageClasses, PVs
│   └── monitoring/          # Prometheus, Grafana
├── environments/         # Environment-specific configurations
│   ├── dev/                 # Development environment
│   ├── staging/             # Staging environment
│   └── prod/                # Production (3-site)
└── README.md            # This file
```

---

## Prerequisites

### Required Tools

```bash
# Terraform 1.5+
terraform version

# Cloud CLI (choose one)
aws --version      # AWS
az --version       # Azure
gcloud --version   # GCP

# kubectl or oc
kubectl version
```

### Required Permissions

- Cloud provider admin access
- Ability to create VPCs, subnets, load balancers
- Ability to provision Kubernetes/OpenShift clusters
- Ability to create IAM roles and policies

---

## Quick Start

### 1. Initialize Terraform

```bash
cd terraform/environments/dev
terraform init
```

### 2. Configure Variables

```bash
# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit variables
vi terraform.tfvars
```

### 3. Plan Deployment

```bash
terraform plan
```

### 4. Apply Configuration

```bash
terraform apply
```

---

## Module Documentation

### openshift-cluster

Provisions OpenShift cluster with:
- Control plane nodes (3 masters)
- Worker nodes (configurable)
- Cluster autoscaling
- Monitoring and logging

**Usage**:
```hcl
module "openshift_cluster" {
  source = "../../modules/openshift-cluster"
  
  cluster_name    = "janusgraph-banking-dev"
  region          = "us-east-1"
  node_count      = 3
  instance_type   = "m5.2xlarge"
}
```

### networking

Creates networking infrastructure:
- VPC with public/private subnets
- NAT gateways
- Load balancers
- Security groups

**Usage**:
```hcl
module "networking" {
  source = "../../modules/networking"
  
  vpc_cidr        = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
}
```

### storage

Configures storage:
- StorageClasses for HCD, JanusGraph, OpenSearch
- Backup storage (S3/Azure Blob/GCS)
- Encryption keys

**Usage**:
```hcl
module "storage" {
  source = "../../modules/storage"
  
  storage_type    = "gp3"
  iops            = 3000
  encrypted       = true
}
```

### monitoring

Deploys monitoring stack:
- Prometheus
- Grafana
- AlertManager
- Log aggregation

**Usage**:
```hcl
module "monitoring" {
  source = "../../modules/monitoring"
  
  retention_days  = 30
  alert_email     = "ops@example.com"
}
```

---

## Environment Configurations

### Development

**Purpose**: Development and testing  
**Size**: Small (3 nodes)  
**Cost**: ~$500/month

```bash
cd terraform/environments/dev
terraform apply
```

### Staging

**Purpose**: Pre-production testing  
**Size**: Medium (6 nodes)  
**Cost**: ~$1,500/month

```bash
cd terraform/environments/staging
terraform apply
```

### Production

**Purpose**: Production workloads (3-site)  
**Size**: Large (9 nodes per site, 27 total)  
**Cost**: ~$15,000/month

```bash
cd terraform/environments/prod
terraform apply
```

---

## State Management

### Remote State Backend

**AWS S3 + DynamoDB**:
```hcl
terraform {
  backend "s3" {
    bucket         = "janusgraph-terraform-state"
    key            = "environments/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}
```

**Azure Blob Storage**:
```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "janusgraphterraformstate"
    container_name       = "tfstate"
    key                  = "dev.terraform.tfstate"
  }
}
```

**GCS**:
```hcl
terraform {
  backend "gcs" {
    bucket = "janusgraph-terraform-state"
    prefix = "environments/dev"
  }
}
```

---

## Best Practices

### 1. Use Workspaces

```bash
# Create workspace
terraform workspace new dev

# List workspaces
terraform workspace list

# Switch workspace
terraform workspace select dev
```

### 2. Use Variables

```hcl
# variables.tf
variable "cluster_name" {
  description = "Name of the OpenShift cluster"
  type        = string
}

variable "node_count" {
  description = "Number of worker nodes"
  type        = number
  default     = 3
}
```

### 3. Use Outputs

```hcl
# outputs.tf
output "cluster_endpoint" {
  description = "OpenShift cluster API endpoint"
  value       = module.openshift_cluster.endpoint
}

output "kubeconfig" {
  description = "Kubeconfig for cluster access"
  value       = module.openshift_cluster.kubeconfig
  sensitive   = true
}
```

### 4. Use Data Sources

```hcl
# Fetch existing VPC
data "aws_vpc" "existing" {
  id = var.vpc_id
}

# Use in module
resource "aws_subnet" "private" {
  vpc_id = data.aws_vpc.existing.id
}
```

### 5. Use Locals

```hcl
locals {
  common_tags = {
    Project     = "janusgraph-banking"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_instance" "example" {
  tags = local.common_tags
}
```

---

## Validation

### Terraform Validate

```bash
terraform validate
```

### Terraform Format

```bash
terraform fmt -recursive
```

### Terraform Plan

```bash
terraform plan -out=tfplan
```

### Security Scan

```bash
# Using tfsec
tfsec .

# Using checkov
checkov -d .
```

---

## Disaster Recovery

### Backup State

```bash
# Download current state
terraform state pull > backup-$(date +%Y%m%d).tfstate

# Upload state (if needed)
terraform state push backup-20260219.tfstate
```

### Restore Infrastructure

```bash
# Import existing resources
terraform import aws_instance.example i-1234567890abcdef0

# Refresh state
terraform refresh

# Apply to restore
terraform apply
```

---

## Troubleshooting

### Issue 1: State Lock

**Symptom**: `Error acquiring the state lock`

**Solution**:
```bash
# Force unlock (use with caution)
terraform force-unlock <lock-id>
```

### Issue 2: Resource Already Exists

**Symptom**: `Error: resource already exists`

**Solution**:
```bash
# Import existing resource
terraform import <resource_type>.<name> <resource_id>
```

### Issue 3: Provider Authentication

**Symptom**: `Error: authentication failed`

**Solution**:
```bash
# AWS
aws configure

# Azure
az login

# GCP
gcloud auth application-default login
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Terraform
on: [push]
jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
      - run: terraform init
      - run: terraform validate
      - run: terraform plan
```

### GitLab CI

```yaml
terraform:
  image: hashicorp/terraform:latest
  script:
    - terraform init
    - terraform validate
    - terraform plan
```

---

## Cost Estimation

### Terraform Cost

```bash
# Using Infracost
infracost breakdown --path .

# Monthly cost estimate
infracost diff --path .
```

### Environment Costs

| Environment | Monthly Cost | Annual Cost |
|-------------|--------------|-------------|
| Dev | $500 | $6,000 |
| Staging | $1,500 | $18,000 |
| Prod (3-site) | $15,000 | $180,000 |

---

## Support

### Resources

- [Terraform Documentation](https://www.terraform.io/docs/)
- [AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

### Contact

- Platform Engineering Team
- DevOps Team
- GitHub Issues

---

**Last Updated**: 2026-02-19  
**Version**: 1.0  
**Status**: Active