# VMware vSphere Production Environment

This directory contains Terraform configuration for deploying the JanusGraph Banking Platform to a VMware vSphere on-premises production environment.

## Overview

- **Environment**: Production
- **Cloud Provider**: VMware vSphere (On-Premises)
- **Cluster Size**: 11-16 nodes (3 control plane, 5-10 workers, 3 HCD nodes)
- **Cost Model**: CapEx (hardware already owned)
- **Purpose**: Production workloads with high availability and disaster recovery

## Architecture

### Cluster Configuration

| Component | Count | vCPU | Memory | Disk | Purpose |
|-----------|-------|------|--------|------|---------|
| Control Plane | 3 | 8 | 32 GB | 200 GB | HA Kubernetes control plane |
| Worker Nodes | 5-10 | 16 | 64 GB | 500 GB | Application workloads |
| HCD Nodes | 3 | 32 | 256 GB | 200 GB OS + 2 TB data | Cassandra/HCD cluster |
| Load Balancer | 1 | 4 | 8 GB | 100 GB | HAProxy load balancer (HA) |

**Total Resources**: 11-16 VMs, 212-372 vCPU, 1,288-2,088 GB RAM, 8.5-13.5 TB storage

### High Availability Features

- **Control Plane**: 3 nodes for HA (survives 1 node failure)
- **Workers**: 5-10 nodes with auto-scaling
- **HCD**: 3 nodes with RF=3 (survives 1 node failure)
- **Load Balancer**: Active-passive HA configuration
- **Monitoring**: 2 Prometheus replicas, 3 AlertManager replicas
- **Storage**: vSAN with FTT=1 (survives 1 disk/host failure)

### Network Configuration

- **Network CIDR**: 10.200.0.0/24
- **Gateway**: 10.200.0.1
- **DNS Servers**: 10.200.0.10, 10.200.0.11
- **VLAN**: 200 (production network)
- **Switch Type**: Distributed vSwitch (vDS)
- **Network Redundancy**: Multiple uplinks, NIC teaming

### Storage Configuration

| Storage Class | Provisioner | Reclaim Policy | Use Case | Size |
|---------------|-------------|----------------|----------|------|
| hcd-storage | vSphere CSI | Retain | HCD/Cassandra data | 2 TB per node |
| janusgraph-storage | vSphere CSI | Retain | JanusGraph data | 500 GB |
| opensearch-storage | vSphere CSI | Delete | OpenSearch indices | 1 TB |
| pulsar-storage | vSphere CSI | Delete | Pulsar messages | 500 GB |
| vsphere-general | vSphere CSI | Delete | General purpose | Variable |
| nfs-storage | NFS CSI | Retain | Shared storage | 5 TB |
| vsan-storage | vSphere CSI | Delete | vSAN-backed | Variable |

**Storage Policies**: 
- HCD: Production vSAN Policy (FTT=1, RAID-1)
- JanusGraph: Production vSAN Policy (FTT=1, RAID-1)
- OpenSearch: Standard vSAN Policy (FTT=1, RAID-5)
- Pulsar: Standard vSAN Policy (FTT=1, RAID-5)

### Monitoring Stack

| Component | Replicas | Storage | Retention | Purpose |
|-----------|----------|---------|-----------|---------|
| Prometheus | 2 | 500 GB | 90 days | Metrics collection |
| Grafana | 2 | 50 GB | N/A | Visualization |
| AlertManager | 3 | 50 GB | N/A | Alert routing |
| Loki | 2 | 500 GB | 30 days | Log aggregation |
| Jaeger | 2 | 100 GB | 14 days | Distributed tracing |

## Prerequisites

### vSphere Infrastructure

1. **vCenter Server**: 7.0 or later (8.0 recommended)
2. **ESXi Hosts**: 7.0 or later, minimum 4 hosts for HA
3. **vSphere Cluster**: DRS enabled, HA enabled, vSAN enabled
4. **Datastore**: Minimum 10 TB available space (vSAN or shared storage)
5. **Network**: Production network with redundant uplinks
6. **Distributed vSwitch**: Production-DVS configured
7. **Resource Pool**: `janusgraph-production` (will be created)
8. **vSphere Tags**: Production, Critical, PCI-DSS, SOX

### VM Template

Create a production-grade RHCOS template:

```bash
# Download RHCOS OVA
wget https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.14/latest/rhcos-vmware.x86_64.ova

# Import to vSphere
govc import.ova -name=rhcos-4.14-template -ds=production-datastore rhcos-vmware.x86_64.ova

# Configure template
govc vm.change -vm rhcos-4.14-template -nested-hv-enabled=true
govc vm.change -vm rhcos-4.14-template -sync-time-with-host=true

# Convert to template
govc vm.markastemplate rhcos-4.14-template
```

### Storage Policies

Create production storage policies:

```bash
# HCD Production Policy (high performance, high availability)
govc storage.policy.create -name "HCD Production Storage Policy" \
  -rule "vSAN.hostFailuresToTolerate=1" \
  -rule "vSAN.stripeWidth=2" \
  -rule "vSAN.forceProvisioning=false"

# JanusGraph Production Policy
govc storage.policy.create -name "JanusGraph Production Storage Policy" \
  -rule "vSAN.hostFailuresToTolerate=1" \
  -rule "vSAN.stripeWidth=1"

# OpenSearch Production Policy
govc storage.policy.create -name "OpenSearch Production Storage Policy" \
  -rule "vSAN.hostFailuresToTolerate=1" \
  -rule "vSAN.replicaPreference=RAID-5/6"

# Pulsar Production Policy
govc storage.policy.create -name "Pulsar Production Storage Policy" \
  -rule "vSAN.hostFailuresToTolerate=1" \
  -rule "vSAN.replicaPreference=RAID-5/6"
```

### Required Tools

- Terraform >= 1.5.0
- vSphere credentials with administrator privileges
- kubectl (for cluster access)
- govc (for vSphere CLI operations)
- velero (for backup/restore)

### vSphere Permissions

Production service account requires:

- **Global**: All privileges (or specific privileges below)
- **Datastore**: All privileges
- **Network**: All privileges
- **Resource**: All privileges
- **Virtual Machine**: All privileges
- **vApp**: All privileges
- **Storage Policy**: View and assign
- **Tags**: Create, edit, assign

## Setup Instructions

### 1. Pre-Deployment Checklist

```bash
# Verify vSphere connectivity
govc about

# Check available resources
govc cluster.info Production-Cluster

# Verify datastore space
govc datastore.info production-datastore

# Check network configuration
govc dvs.portgroup.info Production-DVS

# Verify template exists
govc vm.info rhcos-4.14-template

# Check storage policies
govc storage.policy.ls
```

### 2. Clone Repository

```bash
git clone <repository-url>
cd terraform/environments/vsphere-prod
```

### 3. Configure Variables

```bash
# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit with your production values
vim terraform.tfvars
```

**CRITICAL**: Use strong, unique passwords for production:

```hcl
# vSphere Connection
vsphere_user                 = "svc-terraform-prod@vsphere.local"
vsphere_password             = "STRONG-UNIQUE-PASSWORD-HERE"
vsphere_server               = "vcenter-prod.example.com"
vsphere_allow_unverified_ssl = false  # MUST be false for production

# vSphere Infrastructure
vsphere_datacenter = "Production-Datacenter"
vsphere_cluster    = "Production-Cluster"
vsphere_datastore  = "production-datastore"

# NFS Storage (if using shared storage)
vsphere_nfs_server = "nfs-prod.example.com"

# Monitoring (REQUIRED for production)
slack_webhook_url = "https://hooks.slack.com/services/YOUR/PRODUCTION/WEBHOOK"
pagerduty_key     = "your-production-pagerduty-integration-key"
```

### 4. Initialize Terraform

```bash
terraform init
```

### 5. Review Plan

```bash
terraform plan -out=production.tfplan
```

Expected resources:
- 11-16 vSphere virtual machines
- 7 Kubernetes storage classes
- 1 vSphere resource pool
- 1 vSphere folder
- Monitoring stack (Prometheus, Grafana, AlertManager, Loki, Jaeger)
- Backup CronJob

### 6. Deploy Infrastructure

```bash
# Apply with approval
terraform apply production.tfplan

# Or apply with auto-approve (use with caution)
terraform apply -auto-approve
```

Deployment time: ~60-90 minutes

### 7. Verify Deployment

```bash
# Get kubeconfig
terraform output -raw kubeconfig > ~/.kube/config-vsphere-prod

# Set KUBECONFIG
export KUBECONFIG=~/.kube/config-vsphere-prod

# Verify cluster
kubectl get nodes
kubectl get pods -A

# Check all nodes are Ready
kubectl get nodes -o wide

# Verify storage classes
kubectl get sc

# Check monitoring stack
kubectl get pods -n monitoring

# Verify backup job
kubectl get cronjob -n backup
```

## Post-Deployment Configuration

### 1. Configure DNS

Add production DNS records:

```bash
# Get load balancer IP
LB_IP=$(terraform output -raw load_balancer_ip)

# Add DNS records (A records)
api.prod.janusgraph.local           -> $LB_IP
*.apps.prod.janusgraph.local        -> $LB_IP
grafana.prod.janusgraph.local       -> $LB_IP
prometheus.prod.janusgraph.local    -> $LB_IP
alertmanager.prod.janusgraph.local  -> $LB_IP
```

### 2. Configure SSL/TLS

```bash
# Generate production certificates
cd ../../../scripts/security
./generate_certificates.sh --environment production

# Apply certificates
kubectl create secret tls janusgraph-tls \
  --cert=certs/prod/janusgraph.crt \
  --key=certs/prod/janusgraph.key \
  -n janusgraph
```

### 3. Access Monitoring

```bash
# Get monitoring endpoints
terraform output monitoring_endpoints

# Access Grafana (HTTPS)
# URL: https://grafana.prod.janusgraph.local
# Default credentials: admin/admin (CHANGE IMMEDIATELY)

# Access Prometheus
# URL: https://prometheus.prod.janusgraph.local

# Access AlertManager
# URL: https://alertmanager.prod.janusgraph.local

# Access Loki
# URL: https://loki.prod.janusgraph.local

# Access Jaeger
# URL: https://jaeger.prod.janusgraph.local
```

### 4. Configure Backup

```bash
# Install Velero
velero install \
  --provider vsphere \
  --plugins velero/velero-plugin-for-vsphere:v1.5 \
  --bucket janusgraph-backups \
  --backup-location-config region=us-east-1

# Verify backup schedule
kubectl get cronjob -n backup janusgraph-backup

# Test backup
velero backup create test-backup --include-namespaces=hcd --wait

# Verify backup
velero backup describe test-backup
```

### 5. Deploy Applications

```bash
# Deploy in order (dependencies)
kubectl apply -f ../../../k8s/base/hcd/
kubectl apply -f ../../../k8s/base/janusgraph/
kubectl apply -f ../../../k8s/base/opensearch/
kubectl apply -f ../../../k8s/base/pulsar/
kubectl apply -f ../../../k8s/base/api/

# Verify deployments
kubectl get pods -n hcd
kubectl get pods -n janusgraph
kubectl get pods -n opensearch
kubectl get pods -n pulsar
```

## Production Operations

### Scaling

#### Scale Workers

```bash
# Edit main.tf
vim main.tf

# Change worker_count
locals {
  worker_count = 10  # Increase from 5 to 10
}

# Apply changes
terraform apply
```

#### Scale HCD

```bash
# HCD scaling requires careful planning
# 1. Add new node
# 2. Run nodetool repair
# 3. Verify data distribution

# Add node (edit main.tf)
locals {
  hcd_count = 5  # Increase from 3 to 5
}

terraform apply

# Wait for node to join
kubectl exec -n hcd hcd-0 -- nodetool status

# Run repair
kubectl exec -n hcd hcd-0 -- nodetool repair
```

### Upgrading

#### Cluster Upgrade

```bash
# Update cluster version in main.tf
cluster_version = "4.15"

# Plan upgrade
terraform plan

# Apply upgrade (rolling update)
terraform apply

# Monitor upgrade
kubectl get nodes -w
```

#### Application Upgrade

```bash
# Update image tags in k8s manifests
# Apply changes
kubectl apply -f ../../../k8s/base/janusgraph/

# Monitor rollout
kubectl rollout status deployment/janusgraph -n janusgraph
```

### Backup and Restore

#### Manual Backup

```bash
# Create backup
velero backup create prod-backup-$(date +%Y%m%d) \
  --include-namespaces=hcd,janusgraph,opensearch,pulsar \
  --wait

# Verify backup
velero backup describe prod-backup-$(date +%Y%m%d)

# List backups
velero backup get
```

#### Restore from Backup

```bash
# List available backups
velero backup get

# Restore specific backup
velero restore create --from-backup prod-backup-20260219 --wait

# Verify restore
velero restore describe <restore-name>

# Check pods
kubectl get pods -A
```

#### Disaster Recovery

```bash
# Full cluster restore procedure
# 1. Deploy new cluster
terraform apply

# 2. Install Velero
velero install --provider vsphere

# 3. Restore from backup
velero restore create --from-backup prod-backup-latest --wait

# 4. Verify all services
kubectl get pods -A
kubectl get pv
kubectl get pvc -A

# 5. Test application connectivity
curl https://api.prod.janusgraph.local/health
```

## Monitoring and Alerts

### Prometheus Metrics

Production metrics collection:
- **Infrastructure**: Node CPU, memory, disk, network
- **Kubernetes**: Pod metrics, resource usage, events
- **HCD**: Cassandra metrics, compaction, repair status
- **JanusGraph**: Query latency, throughput, cache hit rate
- **OpenSearch**: Index size, query performance, cluster health
- **Pulsar**: Message rate, backlog, consumer lag

### Grafana Dashboards

Pre-configured production dashboards:
- **Cluster Overview**: Overall cluster health
- **Node Metrics**: Per-node resource usage
- **HCD Performance**: Cassandra-specific metrics
- **JanusGraph Analytics**: Graph query performance
- **Storage Utilization**: Disk usage, IOPS, latency
- **Network Traffic**: Bandwidth, packet loss, errors
- **Application Performance**: API latency, error rates

### Alert Rules (Production)

Critical alerts (PagerDuty):
- Control plane node down
- Worker node down (>20% unavailable)
- HCD node down
- Disk space critical (<10%)
- Memory usage critical (>90%)
- API error rate high (>5%)

Warning alerts (Slack):
- High CPU usage (>80%)
- High memory usage (>80%)
- Disk space low (<20%)
- High query latency (>500ms)
- Backup failed

## Security

### Network Security

- **Network Segmentation**: Production VLAN isolated from other networks
- **Firewall Rules**: Only required ports open
- **NSX-T Micro-segmentation**: If available, use for pod-level security
- **DRS Anti-Affinity**: Control plane and HCD nodes on different hosts

### Access Control

- **vSphere RBAC**: Least privilege for service accounts
- **Kubernetes RBAC**: Role-based access for users
- **Audit Logging**: Enabled for all API calls
- **MFA**: Required for all administrative access

### Data Protection

- **Encryption at Rest**: vSphere encryption enabled
- **Encryption in Transit**: TLS for all communication
- **Backup Encryption**: Velero backups encrypted
- **Key Management**: HashiCorp Vault for secrets

### Compliance

- **PCI DSS**: Payment card data protection
- **SOX**: Financial reporting controls
- **GDPR**: Data privacy and protection
- **Audit Trails**: All access logged and retained

## Troubleshooting

### VM Provisioning Issues

```bash
# Check vSphere resources
govc cluster.info Production-Cluster

# Verify template
govc vm.info rhcos-4.14-template

# Check resource pool
govc pool.info janusgraph-production

# Review Terraform logs
terraform apply -debug
```

### Network Connectivity

```bash
# Check VM network
govc vm.info <vm-name> | grep Network

# Verify DVS configuration
govc dvs.portgroup.info Production-DVS

# Test connectivity
govc vm.console <vm-name>
ping 10.200.0.1
```

### Storage Issues

```bash
# Check datastore space
govc datastore.info production-datastore

# Verify storage policy
govc storage.policy.info "HCD Production Storage Policy"

# Check CSI driver
kubectl get pods -n kube-system | grep vsphere-csi
kubectl logs -n kube-system <csi-pod>
```

### Performance Issues

```bash
# Check resource usage
kubectl top nodes
kubectl top pods -A

# Review HCD performance
kubectl exec -n hcd hcd-0 -- nodetool status
kubectl exec -n hcd hcd-0 -- nodetool tpstats
kubectl exec -n hcd hcd-0 -- nodetool cfstats

# Check storage performance
kubectl exec -n hcd hcd-0 -- iostat -x 1 10
```

### Backup Failures

```bash
# Check backup job
kubectl get cronjob -n backup janusgraph-backup
kubectl describe cronjob -n backup janusgraph-backup

# Check Velero status
velero backup get
velero backup logs <backup-name>

# Verify storage
velero backup-location get
```

## Cost Optimization

Production cost optimization strategies:

### Resource Right-Sizing

Monitor actual usage and adjust:

```bash
# Review resource usage over 30 days
kubectl top nodes --sort-by=cpu
kubectl top pods -A --sort-by=cpu

# Adjust if consistently under-utilized
# Edit main.tf and reduce CPU/memory
```

### Storage Optimization

```bash
# Review storage usage
kubectl get pv -o custom-columns=NAME:.metadata.name,SIZE:.spec.capacity.storage,USED:.status.capacity.storage

# Implement storage policies
# - Use RAID-5/6 for non-critical data
# - Use deduplication where applicable
# - Implement compression
```

### Monitoring Optimization

```bash
# Reduce retention for non-critical metrics
# Edit main.tf
prometheus_retention = "60d"  # Down from 90d
loki_retention       = "14d"  # Down from 30d
```

## Disaster Recovery

### RTO/RPO Targets

- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 1 hour
- **Backup Frequency**: Every 6 hours
- **Backup Retention**: 90 days

### DR Procedures

1. **Daily Backups**: Automated via CronJob
2. **Weekly Full Backups**: Manual verification
3. **Monthly DR Drills**: Test restore procedures
4. **Quarterly DR Tests**: Full failover test

### DR Site Configuration

If using DR site:

```bash
# Configure replication
velero backup-location create dr-site \
  --provider vsphere \
  --bucket janusgraph-dr-backups \
  --config region=us-west-1

# Schedule replication
velero schedule create prod-to-dr \
  --schedule="0 */6 * * *" \
  --backup-location dr-site
```

## Support and Documentation

- **Terraform Modules**: `../../modules/`
- **Kubernetes Manifests**: `../../../k8s/`
- **Architecture Docs**: `../../../docs/implementation/`
- **Operations Runbook**: `../../../docs/operations/operations-runbook.md`
- **Troubleshooting Guide**: `../../../docs/guides/troubleshooting-guide.md`
- **Security Guide**: `../../../docs/security/security-guide.md`

## Related Environments

- **vSphere Staging**: `../vsphere-staging/`
- **AWS Production**: `../aws-prod/`
- **Azure Production**: `../azure-prod/`
- **GCP Production**: `../gcp-prod/`

## Version History

- **v1.0.0** (2026-02-19): Initial vSphere production environment
  - 3 control plane, 5-10 workers, 3 HCD nodes
  - High availability configuration
  - Full monitoring stack (Prometheus, Grafana, AlertManager, Loki, Jaeger)
  - Automated backups with 90-day retention
  - 7 storage classes with production policies
  - Disaster recovery procedures
  - Compliance controls (PCI-DSS, SOX, GDPR)