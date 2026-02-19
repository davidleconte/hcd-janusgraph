# Azure Staging Environment

This directory contains Terraform configuration for the Azure staging environment of the JanusGraph Banking Platform.

## Overview

- **Environment**: Staging
- **Cloud Provider**: Azure (AKS)
- **Region**: East US
- **Cluster Size**: 5-10 nodes
- **VM Sizes**: 
  - Default: Standard_D8s_v3 (8 vCPU, 32 GB RAM)
  - HCD: Standard_E16s_v3 (16 vCPU, 128 GB RAM)

## Prerequisites

1. **Azure CLI** installed and configured
2. **Terraform** >= 1.5.0
3. **kubectl** for Kubernetes management
4. **kubelogin** for Azure AD authentication
5. **Azure Service Principal** with appropriate permissions

## Setup

### 1. Configure Azure Authentication

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "your-subscription-id"

# Create service principal (if not exists)
az ad sp create-for-rbac --name "janusgraph-staging-terraform" \
  --role="Contributor" \
  --scopes="/subscriptions/your-subscription-id"
```

### 2. Configure Terraform Backend

Create the backend storage account:

```bash
# Create resource group for Terraform state
az group create --name janusgraph-terraform-state --location eastus

# Create storage account
az storage account create \
  --name janusgraphterraform \
  --resource-group janusgraph-terraform-state \
  --location eastus \
  --sku Standard_LRS

# Create container
az storage container create \
  --name tfstate \
  --account-name janusgraphterraform
```

### 3. Configure Variables

```bash
# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars
```

Required variables:
- `azure_client_id`: Service Principal Client ID
- `azure_tenant_id`: Azure Tenant ID
- `azure_admin_group_ids`: Azure AD group IDs for cluster admins

### 4. Initialize Terraform

```bash
terraform init
```

## Deployment

### Plan

```bash
terraform plan -out=tfplan
```

### Apply

```bash
terraform apply tfplan
```

### Destroy

```bash
terraform destroy
```

## Post-Deployment

### Get Cluster Credentials

```bash
az aks get-credentials \
  --resource-group janusgraph-banking-azure-staging-rg \
  --name janusgraph-banking-azure-staging
```

### Verify Cluster Access

```bash
kubectl get nodes
kubectl get namespaces
```

### Install kubelogin

```bash
# macOS
brew install Azure/kubelogin/kubelogin

# Linux
curl -LO https://github.com/Azure/kubelogin/releases/latest/download/kubelogin-linux-amd64.zip
unzip kubelogin-linux-amd64.zip
sudo mv bin/linux_amd64/kubelogin /usr/local/bin/
```

### Convert kubeconfig for Azure AD

```bash
kubelogin convert-kubeconfig -l azurecli
```

## Configuration Details

### Networking

- **VNet CIDR**: 10.10.0.0/16
- **Availability Zones**: 1, 2, 3
- **NAT Gateway**: Zone-redundant
- **Network Security Groups**: Enabled
- **Flow Logs**: Enabled (14-day retention)

### Storage

- **HCD Storage**: Premium_LRS (Premium SSD)
- **JanusGraph Storage**: Premium_LRS (Premium SSD)
- **OpenSearch Storage**: StandardSSD_LRS
- **Pulsar Storage**: StandardSSD_LRS
- **Backup Retention**: 14 days
- **Snapshot Retention**: 7 days

### Monitoring

- **Log Analytics**: 30-day retention
- **Prometheus**: Enabled
- **Grafana**: Enabled
- **Loki**: Enabled
- **Network Flow Logs**: Enabled

### Auto-Scaling

- **Min Nodes**: 5
- **Max Nodes**: 10
- **Auto-scaling**: Enabled

## Cost Optimization

Staging environment includes:
- Smaller VM sizes than production
- Standard SSD for non-critical workloads
- 14-day backup retention (vs 90 days in prod)
- 30-day log retention (vs 90 days in prod)

Estimated monthly cost: $2,500-$4,000 (depending on usage)

## Security

- **Azure AD Integration**: Enabled
- **RBAC**: Enabled
- **Network Policies**: Enabled
- **Private Cluster**: Disabled (for easier access in staging)
- **Disk Encryption**: Enabled
- **Secrets Management**: Azure Key Vault

## Troubleshooting

### Authentication Issues

```bash
# Re-login to Azure
az login

# Convert kubeconfig
kubelogin convert-kubeconfig -l azurecli

# Test access
kubectl get nodes
```

### Terraform State Issues

```bash
# List state
terraform state list

# Show specific resource
terraform state show module.cluster.azurerm_kubernetes_cluster.main[0]

# Refresh state
terraform refresh
```

### Network Connectivity

```bash
# Check NSG rules
az network nsg list --resource-group janusgraph-banking-azure-staging-rg

# Check flow logs
az network watcher flow-log list --location eastus
```

## Maintenance

### Upgrade Kubernetes Version

```bash
# Check available versions
az aks get-upgrades \
  --resource-group janusgraph-banking-azure-staging-rg \
  --name janusgraph-banking-azure-staging

# Update terraform.tfvars
# kubernetes_version = "1.29"

# Apply upgrade
terraform plan
terraform apply
```

### Scale Cluster

```bash
# Update node_count in main.tf
# node_count = 7

# Apply changes
terraform plan
terraform apply
```

## Related Documentation

- [Azure Module Documentation](../../modules/openshift-cluster/README.md)
- [Networking Module](../../modules/networking/README.md)
- [Storage Module](../../modules/storage/README.md)
- [Multi-Cloud Specification](../../../docs/implementation/terraform-multi-cloud-specification-2026-02-19.md)

## Support

For issues or questions:
- Create an issue in the repository
- Contact the platform team
- Check Azure documentation: https://docs.microsoft.com/azure/aks/