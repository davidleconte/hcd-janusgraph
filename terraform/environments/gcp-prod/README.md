# GCP Production Environment

This directory contains Terraform configuration for the GCP production environment of the JanusGraph Banking Platform.

## ⚠️ PRODUCTION ENVIRONMENT ⚠️

This is a **PRODUCTION** environment. All changes require:
- Change management approval
- Peer review
- Testing in staging environment first
- Scheduled maintenance window

## Overview

- **Environment**: Production
- **Cloud Provider**: Google Cloud Platform (GKE)
- **Region**: us-east1
- **Zones**: us-east1-b, us-east1-c, us-east1-d
- **Cluster Size**: 10-20 nodes
- **Machine Types**: 
  - Default: n2-standard-16 (16 vCPU, 64 GB RAM)
  - HCD: n2-highmem-32 (32 vCPU, 256 GB RAM)

## Prerequisites

1. **gcloud CLI** installed and configured
2. **Terraform** >= 1.5.0
3. **kubectl** for Kubernetes management
4. **GCP Project** with appropriate APIs enabled
5. **Service Account** with appropriate permissions
6. **Change Management Approval** for any modifications

## Setup

### 1. Configure GCP Authentication

```bash
# Login to GCP
gcloud auth login

# Set project
gcloud config set project your-production-project-id

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable binaryauthorization.googleapis.com
gcloud services enable containeranalysis.googleapis.com
```

### 2. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create janusgraph-prod-terraform \
  --display-name="JanusGraph Production Terraform"

# Grant permissions
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:janusgraph-prod-terraform@your-project-id.iam.gserviceaccount.com" \
  --role="roles/container.admin"

gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:janusgraph-prod-terraform@your-project-id.iam.gserviceaccount.com" \
  --role="roles/compute.networkAdmin"

gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:janusgraph-prod-terraform@your-project-id.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:janusgraph-prod-terraform@your-project-id.iam.gserviceaccount.com" \
  --role="roles/binaryauthorization.policyEditor"

# Create key
gcloud iam service-accounts keys create ~/janusgraph-prod-terraform.json \
  --iam-account=janusgraph-prod-terraform@your-project-id.iam.gserviceaccount.com

# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS=~/janusgraph-prod-terraform.json
```

### 3. Configure Terraform Backend

Create the backend storage bucket:

```bash
# Create bucket for Terraform state with versioning
gsutil mb -p your-project-id -l us-east1 gs://janusgraph-terraform-state

# Enable versioning
gsutil versioning set on gs://janusgraph-terraform-state

# Set lifecycle policy for old versions
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "numNewerVersions": 10
        }
      }
    ]
  }
}
EOF
gsutil lifecycle set lifecycle.json gs://janusgraph-terraform-state
```

### 4. Configure Variables

```bash
# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars
```

Required variables:
- `gcp_project_id`: Your GCP project ID
- `alert_email`: Email for critical alerts

### 5. Initialize Terraform

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
gcloud container clusters get-credentials janusgraph-banking-gcp-prod \
  --region us-east1 \
  --project your-project-id
```

### Verify Cluster Access

```bash
kubectl get nodes
kubectl get namespaces
kubectl get pods --all-namespaces
```

## Configuration Details

### Networking

- **VPC CIDR**: 10.40.0.0/16
- **Pods CIDR**: 10.44.0.0/14
- **Services CIDR**: 10.48.0.0/20
- **Zones**: us-east1-b, us-east1-c, us-east1-d
- **Cloud NAT**: Enabled
- **VPC Flow Logs**: Enabled
- **Private Google Access**: Enabled

### Storage

- **HCD Storage**: pd-ssd (SSD Persistent Disk)
- **JanusGraph Storage**: pd-ssd (SSD Persistent Disk)
- **OpenSearch Storage**: pd-ssd (SSD Persistent Disk)
- **Pulsar Storage**: pd-ssd (SSD Persistent Disk)
- **Backup Retention**: 90 days
- **Snapshot Retention**: 30 days
- **Multi-regional Backups**: Enabled

### Monitoring

- **Cloud Logging**: 90-day retention
- **Prometheus**: Enabled
- **Grafana**: Enabled
- **Loki**: Enabled
- **VPC Flow Logs**: Enabled
- **Cloud Monitoring Alerts**: Enabled
- **Notification Channels**: Email configured

### Auto-Scaling

- **Min Nodes**: 10
- **Max Nodes**: 20
- **Auto-scaling**: Enabled
- **Scale-up Policy**: Aggressive
- **Scale-down Policy**: Conservative

### Compliance

- **Binary Authorization**: Enabled (REQUIRE_ATTESTATION)
- **Workload Identity**: Enabled
- **Shielded Nodes**: Enabled
- **GDPR Compliance**: Enabled
- **SOX Compliance**: Enabled
- **PCI DSS**: Audit mode

## High Availability

### Multi-Zone Deployment

- Nodes distributed across 3 zones
- Regional GKE cluster
- Zone-redundant persistent disks

### Disaster Recovery

- **DR Region**: us-west1
- **RTO**: 4 hours
- **RPO**: 1 hour
- **Cross-region Backups**: Enabled

### Business Continuity

- Automated snapshots every 6 hours
- Point-in-time recovery up to 90 days
- Cross-region replication for critical data

## Security

### Network Security

- **Private Cluster**: Enabled (recommended)
- **Network Policies**: Enabled
- **Authorized Networks**: Configured
- **Cloud Armor**: Recommended
- **VPC Service Controls**: Recommended

### Identity & Access

- **Workload Identity**: Enabled
- **RBAC**: Enabled with least privilege
- **Service Account**: Dedicated for production
- **Binary Authorization**: Enabled

### Data Protection

- **Disk Encryption**: Enabled (Google-managed keys)
- **Encryption at Rest**: Enabled
- **Encryption in Transit**: TLS 1.2+
- **Key Management**: Cloud KMS

### Compliance & Auditing

- **Audit Logging**: Enabled
- **Cloud Logging**: 90-day retention
- **Security Command Center**: Standard tier
- **Compliance Dashboard**: Enabled

## Cost Management

### Estimated Monthly Cost

- **Compute**: $10,000-$15,000
- **Storage**: $2,500-$3,500
- **Networking**: $1,500-$2,000
- **Monitoring**: $800-$1,200
- **Backup**: $1,000-$1,500
- **Total**: $15,800-$23,200/month

### Cost Optimization

- Committed use discounts for predictable workloads
- Auto-scaling to match demand
- Lifecycle policies for old backups
- Regular cost reviews
- Preemptible VMs for non-critical workloads (if applicable)

## Monitoring & Alerting

### Critical Alerts

- CPU usage > 80%
- Memory usage > 80%
- Disk usage > 85%
- Pod failures
- Node failures
- Backup failures
- Binary Authorization violations

### Alert Channels

- Email: platform-team@example.com
- PagerDuty: Production on-call
- Slack: #production-alerts

## Maintenance

### Upgrade Kubernetes Version

```bash
# Check available versions
gcloud container get-server-config --region us-east1

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
# List snapshots
gcloud compute snapshots list --filter="name~janusgraph-banking-gcp-prod"

# Test restore (in DR environment)
gcloud compute disks create test-restore \
  --source-snapshot=<snapshot-name> \
  --zone=us-west1-a
```

## Troubleshooting

### Authentication Issues

```bash
# Re-authenticate
gcloud auth login

# Get credentials
gcloud container clusters get-credentials janusgraph-banking-gcp-prod \
  --region us-east1 \
  --project your-project-id

# Test access
kubectl get nodes
```

### Terraform State Issues

```bash
# List state
terraform state list

# Show specific resource
terraform state show module.cluster.google_container_cluster.main[0]

# Refresh state
terraform refresh
```

### Network Connectivity

```bash
# Check firewall rules
gcloud compute firewall-rules list

# Check VPC flow logs
gcloud compute networks subnets describe <subnet-name> --region us-east1

# Test connectivity
kubectl run test-pod --image=busybox --rm -it -- /bin/sh
```

### Performance Issues

```bash
# Check node metrics
kubectl top nodes

# Check pod metrics
kubectl top pods --all-namespaces

# Check Cloud Monitoring
gcloud monitoring time-series list \
  --filter='metric.type="kubernetes.io/container/cpu/core_usage_time"'
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

- [GCP Module Documentation](../../modules/openshift-cluster/README.md)
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
- **GCP Support**: Open GCP support ticket (Premium Support)

## Change Management

All production changes must follow:
1. RFC (Request for Change) submission
2. CAB (Change Advisory Board) approval
3. Testing in staging environment
4. Scheduled maintenance window
5. Rollback plan documented
6. Post-change verification