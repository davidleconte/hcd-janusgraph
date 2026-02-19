# Azure Production Environment

This directory contains Terraform configuration for the Azure production environment of the JanusGraph Banking Platform.

## ⚠️ PRODUCTION ENVIRONMENT ⚠️

This is a **PRODUCTION** environment. All changes require:
- Change management approval
- Peer review
- Testing in staging environment first
- Scheduled maintenance window

## Overview

- **Environment**: Production
- **Cloud Provider**: Azure (AKS)
- **Region**: East US
- **Cluster Size**: 10-20 nodes
- **VM Sizes**: 
  - Default: Standard_D16s_v3 (16 vCPU, 64 GB RAM)
  - HCD: Standard_E32s_v3 (32 vCPU, 256 GB RAM)

## Prerequisites

1. **Azure CLI** installed and configured
2. **Terraform** >= 1.5.0
3. **kubectl** for Kubernetes management
4. **kubelogin** for Azure AD authentication
5. **Azure Service Principal** with appropriate permissions
6. **Change Management Approval** for any modifications

## Setup

### 1. Configure Azure Authentication

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "your-production-subscription-id"

# Create service principal (if not exists)
az ad sp create-for-rbac --name "janusgraph-prod-terraform" \
  --role="Contributor" \
  --scopes="/subscriptions/your-subscription-id"
```

### 2. Configure Terraform Backend

Create the backend storage account:

```bash
# Create resource group for Terraform state
az group create --name janusgraph-terraform-state --location eastus

# Create storage account with GRS replication
az storage account create \
  --name janusgraphterraform \
  --resource-group janusgraph-terraform-state \
  --location eastus \
  --sku Standard_GRS

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
- `alert_email`: Email for critical alerts

### 4. Initialize Terraform

```bash
terraform init
```

## Deployment

### Plan

```bash
terraform plan -out=tfplan
```

### Apply (Requires Approval)

```bash
# Review plan
terraform show tfplan

# Apply with approval
terraform apply tfplan
```

### Destroy (Emergency Only)

```bash
# Requires multiple approvals
terraform destroy
```

## Post-Deployment

### Get Cluster Credentials

```bash
az aks get-credentials \
  --resource-group janusgraph-banking-azure-prod-rg \
  --name janusgraph-banking-azure-prod
```

### Verify Cluster Access

```bash
kubectl get nodes
kubectl get namespaces
kubectl get pods --all-namespaces
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

- **VNet CIDR**: 10.20.0.0/16
- **Availability Zones**: 1, 2, 3
- **NAT Gateway**: Zone-redundant
- **Network Security Groups**: Enabled with strict rules
- **Flow Logs**: Enabled (90-day retention)
- **DDoS Protection**: Standard (recommended for production)

### Storage

- **HCD Storage**: Premium_LRS (Premium SSD)
- **JanusGraph Storage**: Premium_LRS (Premium SSD)
- **OpenSearch Storage**: Premium_LRS (Premium SSD)
- **Pulsar Storage**: Premium_LRS (Premium SSD)
- **Backup Retention**: 90 days
- **Snapshot Retention**: 30 days
- **Geo-Redundant Backups**: Enabled

### Monitoring

- **Log Analytics**: 90-day retention
- **Prometheus**: Enabled
- **Grafana**: Enabled
- **Loki**: Enabled
- **Network Flow Logs**: Enabled
- **Azure Monitor Alerts**: Enabled
- **Action Groups**: Configured for critical alerts

### Auto-Scaling

- **Min Nodes**: 10
- **Max Nodes**: 20
- **Auto-scaling**: Enabled
- **Scale-up Policy**: Aggressive
- **Scale-down Policy**: Conservative

### Compliance

- **Azure Policy**: Enabled
- **PCI DSS Compliance**: Audit mode
- **CIS Benchmark**: Audit mode
- **GDPR Compliance**: Enabled
- **SOX Compliance**: Enabled

## High Availability

### Multi-Zone Deployment

- Nodes distributed across 3 availability zones
- Zone-redundant NAT Gateway
- Zone-redundant Load Balancer

### Disaster Recovery

- **Backup Vault**: Geo-redundant
- **RTO**: 4 hours
- **RPO**: 1 hour
- **DR Region**: West US (configured but not deployed)

### Business Continuity

- Automated backups every 6 hours
- Point-in-time recovery up to 90 days
- Cross-region replication for critical data

## Security

### Network Security

- **Private Cluster**: Enabled (recommended)
- **Network Policies**: Enabled
- **NSG Rules**: Strict ingress/egress
- **Azure Firewall**: Recommended
- **DDoS Protection**: Standard tier

### Identity & Access

- **Azure AD Integration**: Enabled
- **RBAC**: Enabled with least privilege
- **Service Principal**: Dedicated for production
- **MFA**: Required for admin access

### Data Protection

- **Disk Encryption**: Enabled (Azure Disk Encryption)
- **Encryption at Rest**: Enabled
- **Encryption in Transit**: TLS 1.2+
- **Key Management**: Azure Key Vault

### Compliance & Auditing

- **Audit Logging**: Enabled
- **Activity Logs**: 90-day retention
- **Security Center**: Standard tier
- **Compliance Dashboard**: Enabled

## Cost Management

### Estimated Monthly Cost

- **Compute**: $8,000-$12,000
- **Storage**: $2,000-$3,000
- **Networking**: $1,000-$1,500
- **Monitoring**: $500-$800
- **Backup**: $500-$1,000
- **Total**: $12,000-$18,300/month

### Cost Optimization

- Reserved instances for predictable workloads
- Auto-scaling to match demand
- Lifecycle policies for old backups
- Regular cost reviews

## Monitoring & Alerting

### Critical Alerts

- CPU usage > 80%
- Memory usage > 80%
- Disk usage > 85%
- Pod failures
- Node failures
- Backup failures

### Alert Channels

- Email: platform-team@example.com
- PagerDuty: Production on-call
- Slack: #production-alerts

## Maintenance

### Upgrade Kubernetes Version

```bash
# Check available versions
az aks get-upgrades \
  --resource-group janusgraph-banking-azure-prod-rg \
  --name janusgraph-banking-azure-prod

# Schedule maintenance window
# Update terraform.tfvars
# kubernetes_version = "1.29"

# Apply upgrade during maintenance window
terraform plan
terraform apply
```

### Scale Cluster

```bash
# Update node_count in main.tf
# node_count = 15

# Apply changes during maintenance window
terraform plan
terraform apply
```

### Backup Verification

```bash
# List backups
az backup vault list --resource-group janusgraph-banking-azure-prod-rg

# Test restore (in DR environment)
az backup restore ...
```

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
az network nsg list --resource-group janusgraph-banking-azure-prod-rg

# Check flow logs
az network watcher flow-log list --location eastus

# Test connectivity
kubectl run test-pod --image=busybox --rm -it -- /bin/sh
```

### Performance Issues

```bash
# Check node metrics
kubectl top nodes

# Check pod metrics
kubectl top pods --all-namespaces

# Check Azure Monitor
az monitor metrics list --resource <cluster-id>
```

## Incident Response

### Severity 1 (Critical)

1. Page on-call engineer
2. Create incident ticket
3. Notify stakeholders
4. Begin troubleshooting
5. Document actions
6. Post-incident review

### Rollback Procedure

```bash
# Identify last known good state
terraform state list

# Rollback to previous version
git checkout <previous-commit>
terraform plan
terraform apply
```

## Related Documentation

- [Azure Module Documentation](../../modules/openshift-cluster/README.md)
- [Networking Module](../../modules/networking/README.md)
- [Storage Module](../../modules/storage/README.md)
- [Multi-Cloud Specification](../../../docs/implementation/terraform-multi-cloud-specification-2026-02-19.md)
- [Disaster Recovery Plan](../../../docs/operations/disaster-recovery-plan.md)
- [Incident Response Runbook](../../../docs/operations/incident-response-runbook.md)

## Support

For production issues:
- **Emergency**: Page on-call engineer via PagerDuty
- **Non-Emergency**: Create ticket in ServiceNow
- **Questions**: #production-support Slack channel
- **Azure Support**: Open Azure support ticket (Premier Support)

## Change Management

All production changes must follow:
1. RFC (Request for Change) submission
2. CAB (Change Advisory Board) approval
3. Testing in staging environment
4. Scheduled maintenance window
5. Rollback plan documented
6. Post-change verification