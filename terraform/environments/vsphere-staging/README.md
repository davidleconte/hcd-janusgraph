# VMware vSphere Staging Environment

This directory contains Terraform configuration for deploying the JanusGraph Banking Platform to a VMware vSphere on-premises staging environment.

## Overview

- **Environment**: Staging (Development/Testing)
- **Cloud Provider**: VMware vSphere (On-Premises)
- **Cluster Size**: 3-5 nodes (1 control plane, 2-4 workers, 3 HCD nodes)
- **Cost Model**: CapEx (hardware already owned)
- **Purpose**: Development, testing, and validation before production deployment

## Architecture

### Cluster Configuration

| Component | Count | vCPU | Memory | Disk | Purpose |
|-----------|-------|------|--------|------|---------|
| Control Plane | 1 | 4 | 16 GB | 100 GB | Kubernetes control plane |
| Worker Nodes | 2-4 | 8 | 32 GB | 200 GB | Application workloads |
| HCD Nodes | 3 | 16 | 128 GB | 100 GB OS + 512 GB data | Cassandra/HCD cluster |
| Load Balancer | 1 | 2 | 4 GB | 50 GB | HAProxy load balancer |

**Total Resources**: 6-8 VMs, 82-114 vCPU, 456-584 GB RAM, 2.4-3.0 TB storage

### Network Configuration

- **Network CIDR**: 10.100.0.0/24
- **Gateway**: 10.100.0.1
- **DNS Servers**: 10.100.0.10, 10.100.0.11
- **VLAN**: 100 (configurable)
- **Switch Type**: Standard vSwitch (not distributed)

### Storage Configuration

| Storage Class | Provisioner | Reclaim Policy | Use Case |
|---------------|-------------|----------------|----------|
| hcd-storage | vSphere CSI | Retain | HCD/Cassandra data |
| janusgraph-storage | vSphere CSI | Retain | JanusGraph data |
| opensearch-storage | vSphere CSI | Delete | OpenSearch indices |
| pulsar-storage | vSphere CSI | Delete | Pulsar message storage |
| vsphere-general | vSphere CSI | Delete | General purpose |
| vsan-storage | vSphere CSI | Delete | vSAN-backed storage |

**Storage Policy**: vSAN Default Storage Policy (configurable)

## Prerequisites

### vSphere Infrastructure

1. **vCenter Server**: 7.0 or later
2. **ESXi Hosts**: 7.0 or later
3. **vSphere Cluster**: Configured with DRS enabled
4. **Datastore**: Minimum 3 TB available space
5. **Network**: VM Network with DHCP or static IP pool
6. **Resource Pool**: `janusgraph-staging` (will be created if not exists)

### VM Template

Create a RHCOS (Red Hat CoreOS) template:

```bash
# Download RHCOS OVA
wget https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.14/latest/rhcos-vmware.x86_64.ova

# Import to vSphere
govc import.ova -name=rhcos-4.14-template rhcos-vmware.x86_64.ova

# Convert to template
govc vm.markastemplate rhcos-4.14-template
```

### Required Tools

- Terraform >= 1.5.0
- vSphere credentials with appropriate permissions
- kubectl (for cluster access)
- govc (optional, for vSphere CLI operations)

### vSphere Permissions

Required permissions for the service account:

- **Datastore**: Allocate space, Browse datastore, Low level file operations
- **Network**: Assign network
- **Resource**: Assign virtual machine to resource pool
- **Virtual Machine**: All privileges
- **vApp**: All privileges

## Setup Instructions

### 1. Clone Repository

```bash
git clone <repository-url>
cd terraform/environments/vsphere-staging
```

### 2. Configure Variables

```bash
# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars
```

Required variables:

```hcl
# vSphere Connection
vsphere_user                 = "administrator@vsphere.local"
vsphere_password             = "your-secure-password"
vsphere_server               = "vcenter.example.com"
vsphere_allow_unverified_ssl = false

# vSphere Infrastructure
vsphere_datacenter = "Datacenter1"
vsphere_cluster    = "Cluster1"
vsphere_datastore  = "datastore1"

# Monitoring (Optional)
slack_webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
pagerduty_key     = "your-pagerduty-integration-key"
```

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Review Plan

```bash
terraform plan
```

Expected resources:
- 6-8 vSphere virtual machines
- 7 Kubernetes storage classes
- 1 vSphere resource pool
- 1 vSphere folder
- Monitoring stack (Prometheus, Grafana, AlertManager)

### 5. Deploy Infrastructure

```bash
terraform apply
```

Deployment time: ~30-45 minutes

### 6. Access Cluster

```bash
# Get kubeconfig
terraform output -raw kubeconfig > ~/.kube/config-vsphere-staging

# Set KUBECONFIG
export KUBECONFIG=~/.kube/config-vsphere-staging

# Verify cluster
kubectl get nodes
kubectl get pods -A
```

### 7. Verify Services

```bash
# Check HCD nodes
kubectl get pods -n hcd -o wide

# Check storage classes
kubectl get sc

# Check monitoring
kubectl get pods -n monitoring
```

## Post-Deployment Configuration

### 1. Configure DNS

Add DNS records for the load balancer IP:

```bash
# Get load balancer IP
LB_IP=$(terraform output -raw load_balancer_ip)

# Add DNS records
api.staging.janusgraph.local     -> $LB_IP
*.apps.staging.janusgraph.local  -> $LB_IP
```

### 2. Access Monitoring

```bash
# Get monitoring endpoints
terraform output monitoring_endpoints

# Access Grafana
# URL: http://<load-balancer-ip>:3000
# Default credentials: admin/admin (change immediately)

# Access Prometheus
# URL: http://<load-balancer-ip>:9090

# Access AlertManager
# URL: http://<load-balancer-ip>:9093
```

### 3. Deploy Applications

```bash
# Deploy JanusGraph
kubectl apply -f ../../../k8s/base/janusgraph/

# Deploy HCD
kubectl apply -f ../../../k8s/base/hcd/

# Deploy OpenSearch
kubectl apply -f ../../../k8s/base/opensearch/

# Deploy Pulsar
kubectl apply -f ../../../k8s/base/pulsar/
```

## Maintenance

### Scaling Workers

```bash
# Edit main.tf
vim main.tf

# Change worker_count
locals {
  worker_count = 4  # Increase from 2 to 4
}

# Apply changes
terraform apply
```

### Upgrading Cluster

```bash
# Update cluster version in main.tf
cluster_version = "4.15"

# Apply upgrade
terraform apply
```

### Backup and Restore

```bash
# Backup cluster state
terraform state pull > backup-$(date +%Y%m%d).tfstate

# Backup persistent volumes
kubectl get pv -o yaml > pv-backup-$(date +%Y%m%d).yaml
```

## Monitoring and Alerts

### Prometheus Metrics

- **Node Metrics**: CPU, memory, disk, network
- **Pod Metrics**: Resource usage, restart counts
- **HCD Metrics**: Cassandra-specific metrics
- **JanusGraph Metrics**: Graph operations, query latency

### Grafana Dashboards

Pre-configured dashboards:
- Kubernetes Cluster Overview
- Node Exporter Full
- HCD/Cassandra Dashboard
- JanusGraph Performance
- Storage Utilization

### Alert Rules

Configured alerts:
- Node down or unreachable
- High CPU/memory usage (>80%)
- Disk space low (<20%)
- Pod crash loop
- HCD node down
- High query latency (>1s)

## Troubleshooting

### VM Provisioning Fails

```bash
# Check vSphere credentials
govc about

# Verify template exists
govc vm.info rhcos-4.14-template

# Check resource availability
govc cluster.info Cluster1
```

### Network Connectivity Issues

```bash
# Check VM network configuration
govc vm.info <vm-name> | grep -A5 "Network:"

# Verify VLAN configuration
govc host.portgroup.info "VM Network"

# Test connectivity from VM
govc vm.console <vm-name>
```

### Storage Provisioning Fails

```bash
# Check datastore space
govc datastore.info datastore1

# Verify storage policy
govc storage.policy.ls

# Check CSI driver
kubectl get pods -n kube-system | grep vsphere-csi
kubectl logs -n kube-system <csi-pod-name>
```

### Cluster Not Accessible

```bash
# Check control plane VM
govc vm.info janusgraph-vsphere-staging-control-plane-1

# Verify load balancer
govc vm.info janusgraph-vsphere-staging-lb-1

# Check API server
curl -k https://<load-balancer-ip>:6443/healthz
```

### Performance Issues

```bash
# Check resource usage
kubectl top nodes
kubectl top pods -A

# Review HCD performance
kubectl exec -n hcd hcd-0 -- nodetool status
kubectl exec -n hcd hcd-0 -- nodetool tpstats

# Check storage performance
kubectl exec -n hcd hcd-0 -- iostat -x 1 5
```

## Cost Optimization

### Resource Sizing

For smaller staging workloads:

```hcl
# Reduce worker resources
worker_cpu    = 4   # Down from 8
worker_memory = 16384  # Down from 32768

# Reduce HCD resources
hcd_cpu    = 8   # Down from 16
hcd_memory = 65536  # Down from 131072
```

### Disable Optional Features

```hcl
# Disable Loki (log aggregation)
enable_loki = false

# Disable Jaeger (distributed tracing)
enable_jaeger = false

# Disable NFS storage
vsphere_enable_nfs = false
```

## Security Considerations

### Network Security

- Use private VLANs for cluster communication
- Implement firewall rules between VLANs
- Enable vSphere DRS anti-affinity rules
- Use NSX-T for micro-segmentation (if available)

### Access Control

- Use vSphere RBAC for infrastructure access
- Implement Kubernetes RBAC for application access
- Enable audit logging in vSphere and Kubernetes
- Rotate credentials regularly

### Data Protection

- Enable vSphere encryption (if available)
- Use encrypted storage policies
- Implement backup and disaster recovery
- Test restore procedures regularly

## Disaster Recovery

### Backup Strategy

1. **VM Snapshots**: Daily snapshots of all VMs
2. **Persistent Volume Backups**: Velero with vSphere plugin
3. **Configuration Backups**: Terraform state and Kubernetes manifests
4. **Database Backups**: HCD/Cassandra snapshots

### Recovery Procedures

```bash
# Restore from Terraform state
terraform state pull > current.tfstate
terraform apply -state=backup-YYYYMMDD.tfstate

# Restore persistent volumes
velero restore create --from-backup staging-backup-YYYYMMDD

# Restore applications
kubectl apply -f backup-manifests/
```

## Support and Documentation

- **Terraform Modules**: `../../modules/`
- **Kubernetes Manifests**: `../../../k8s/`
- **Architecture Docs**: `../../../docs/implementation/`
- **Troubleshooting Guide**: `../../../docs/guides/troubleshooting-guide.md`

## Related Environments

- **vSphere Production**: `../vsphere-prod/`
- **AWS Staging**: `../aws-staging/`
- **Azure Staging**: `../azure-staging/`
- **GCP Staging**: `../gcp-staging/`

## Version History

- **v1.0.0** (2026-02-19): Initial vSphere staging environment
  - 1 control plane, 2-4 workers, 3 HCD nodes
  - vSphere CSI driver integration
  - Monitoring stack (Prometheus, Grafana, AlertManager)
  - 7 storage classes with configurable policies