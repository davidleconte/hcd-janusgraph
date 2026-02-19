# GCP Staging Environment

This directory contains Terraform configuration for the GCP staging environment of the JanusGraph Banking Platform.

## Overview

- **Environment**: Staging
- **Cloud Provider**: Google Cloud Platform (GKE)
- **Region**: us-east1
- **Zones**: us-east1-b, us-east1-c, us-east1-d
- **Cluster Size**: 5-10 nodes
- **Machine Types**: 
  - Default: n2-standard-8 (8 vCPU, 32 GB RAM)
  - HCD: n2-highmem-16 (16 vCPU, 128 GB RAM)

## Prerequisites

1. **gcloud CLI** installed and configured
2. **Terraform** >= 1.5.0
3. **kubectl** for Kubernetes management
4. **GCP Project** with appropriate APIs enabled
5. **Service Account** with appropriate permissions

## Setup

### 1. Configure GCP Authentication

```bash
# Login to GCP
gcloud auth login

# Set project
gcloud config set project your-project-id

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com
```

### 2. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create janusgraph-staging-terraform \
  --display-name="JanusGraph Staging Terraform"

# Grant permissions
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:janusgraph-staging-terraform@your-project-id.iam.gserviceaccount.com" \
  --role="roles/container.admin"

gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:janusgraph-staging-terraform@your-project-id.iam.gserviceaccount.com" \
  --role="roles/compute.networkAdmin"

gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:janusgraph-staging-terraform@your-project-id.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Create key
gcloud iam service-accounts keys create ~/janusgraph-staging-terraform.json \
  --iam-account=janusgraph-staging-terraform@your-project-id.iam.gserviceaccount.com

# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS=~/janusgraph-staging-terraform.json
```

### 3. Configure Terraform Backend

Create the backend storage bucket:

```bash
# Create bucket for Terraform state
gsutil mb -p your-project-id -l us-east1 gs://janusgraph-terraform-state

# Enable versioning
gsutil versioning set on gs://janusgraph-terraform-state
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

### 5. Initialize Terraform

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
gcloud container clusters get-credentials janusgraph-banking-gcp-staging \
  --region us-east1 \
  --project your-project-id
```

### Verify Cluster Access

```bash
kubectl get nodes
kubectl get namespaces
```

## Configuration Details

### Networking

- **VPC CIDR**: 10.30.0.0/16
- **Pods CIDR**: 10.32.0.0/14
- **Services CIDR**: 10.36.0.0/20
- **Zones**: us-east1-b, us-east1-c, us-east1-d
- **Cloud NAT**: Enabled
- **VPC Flow Logs**: Enabled

### Storage

- **HCD Storage**: pd-ssd (SSD Persistent Disk)
- **JanusGraph Storage**: pd-ssd (SSD Persistent Disk)
- **OpenSearch Storage**: pd-balanced (Balanced Persistent Disk)
- **Pulsar Storage**: pd-balanced (Balanced Persistent Disk)
- **Backup Retention**: 14 days
- **Snapshot Retention**: 7 days

### Monitoring

- **Cloud Logging**: 30-day retention
- **Prometheus**: Enabled
- **Grafana**: Enabled
- **Loki**: Enabled
- **VPC Flow Logs**: Enabled

### Auto-Scaling

- **Min Nodes**: 5
- **Max Nodes**: 10
- **Auto-scaling**: Enabled

## Cost Optimization

Staging environment includes:
- Smaller machine types than production
- Balanced persistent disks for non-critical workloads
- 14-day backup retention (vs 90 days in prod)
- 30-day log retention (vs 90 days in prod)

Estimated monthly cost: $2,000-$3,500 (depending on usage)

## Security

- **Workload Identity**: Enabled
- **Shielded Nodes**: Enabled
- **Private Cluster**: Disabled (for easier access in staging)
- **Network Policies**: Enabled
- **Binary Authorization**: Disabled (enabled in production)
- **Disk Encryption**: Enabled (Google-managed keys)

## Troubleshooting

### Authentication Issues

```bash
# Re-authenticate
gcloud auth login

# Get credentials
gcloud container clusters get-credentials janusgraph-banking-gcp-staging \
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

## Maintenance

### Upgrade Kubernetes Version

```bash
# Check available versions
gcloud container get-server-config --region us-east1

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

- [GCP Module Documentation](../../modules/openshift-cluster/README.md)
- [Networking Module](../../modules/networking/README.md)
- [Storage Module](../../modules/storage/README.md)
- [Multi-Cloud Specification](../../../docs/implementation/terraform-multi-cloud-specification-2026-02-19.md)

## Support

For issues or questions:
- Create an issue in the repository
- Contact the platform team
- Check GCP documentation: https://cloud.google.com/kubernetes-engine/docs