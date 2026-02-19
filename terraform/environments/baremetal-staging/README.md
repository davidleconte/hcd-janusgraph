# Bare Metal Staging Environment

This Terraform configuration deploys a Kubernetes cluster on bare metal infrastructure for staging/testing purposes.

## Architecture

### Infrastructure Components

- **1 Control Plane Node** (can be scaled to 3 for HA)
- **2-3 Worker Nodes** (general workloads)
- **3 HCD Nodes** (Cassandra + Ceph storage)
- **Ceph Distributed Storage** (block and filesystem)
- **MetalLB Load Balancer** (L2 mode)
- **HAProxy + Keepalived** (optional, for API HA)

### Network Layout

```
Control Plane: 192.168.1.0/24
Workers:       192.168.2.0/24
HCD Nodes:     192.168.3.0/24
Pod Network:   10.244.0.0/16
Services:      10.96.0.0/12
MetalLB Pool:  192.168.1.200-192.168.1.250
```

### Storage Classes

- `hcd-storage` - High-performance Ceph RBD for HCD (Retain policy)
- `janusgraph-storage` - Ceph RBD for JanusGraph
- `opensearch-storage` - Ceph RBD for OpenSearch
- `pulsar-storage` - Ceph RBD for Pulsar
- `general-storage` - Default Ceph RBD for general use
- `cephfs-storage` - CephFS for shared filesystem access
- `nfs-storage` - Optional NFS for legacy workloads

## Prerequisites

### Hardware Requirements

**Control Plane Nodes:**
- CPU: 4 cores minimum
- RAM: 16 GB minimum
- Disk: 100 GB minimum
- Network: 1 Gbps minimum

**Worker Nodes:**
- CPU: 8 cores minimum
- RAM: 32 GB minimum
- Disk: 200 GB minimum
- Network: 1 Gbps minimum

**HCD Nodes:**
- CPU: 16 cores minimum
- RAM: 128 GB minimum
- OS Disk: 100 GB minimum
- Data Disk: 1 TB minimum (for Ceph)
- Network: 10 Gbps recommended

### Software Requirements

- **IPMI/BMC Access** - All servers must have IPMI enabled
- **PXE Boot** - Optional, for automated OS installation
- **Ubuntu 22.04 LTS** - Pre-installed or via PXE
- **SSH Access** - Root or sudo access required
- **Terraform** - Version 1.5.0 or later
- **ipmitool** - For IPMI management

### Network Requirements

- **Static IP Addresses** - All nodes require static IPs
- **DNS Resolution** - Internal DNS or /etc/hosts entries
- **Internet Access** - For package downloads (or local mirror)
- **VLAN Support** - Optional, for network segmentation

## Configuration

### 1. Copy Example Configuration

```bash
cd terraform/environments/baremetal-staging
cp terraform.tfvars.example terraform.tfvars
```

### 2. Update terraform.tfvars

Edit `terraform.tfvars` with your actual server details:

```hcl
# Control Plane Nodes
baremetal_control_plane_hosts = [
  {
    id           = "cp-01"
    ipmi_address = "192.168.0.101"  # IPMI/BMC address
    ip_address   = "192.168.1.101"  # Node IP address
    hostname     = "k8s-cp-01"
    mac_address  = "00:50:56:00:01:01"
  }
]

# Worker Nodes
baremetal_worker_hosts = [
  {
    id           = "worker-01"
    ipmi_address = "192.168.0.111"
    ip_address   = "192.168.2.111"
    hostname     = "k8s-worker-01"
    mac_address  = "00:50:56:00:02:01"
  },
  # Add more workers...
]

# HCD Nodes
baremetal_hcd_hosts = [
  {
    id           = "hcd-01"
    ipmi_address = "192.168.0.121"
    ip_address   = "192.168.3.121"
    hostname     = "k8s-hcd-01"
    mac_address  = "00:50:56:00:03:01"
  },
  # Add more HCD nodes...
]

# IPMI Credentials
baremetal_ipmi_user     = "admin"
baremetal_ipmi_password = "your-secure-password"

# SSH Configuration
baremetal_ssh_user             = "root"
baremetal_ssh_private_key_path = "~/.ssh/id_rsa"
```

### 3. Prepare Servers

**Option A: Manual OS Installation**

1. Install Ubuntu 22.04 LTS on all servers
2. Configure static IP addresses
3. Enable SSH access
4. Configure IPMI/BMC

**Option B: PXE Boot (Automated)**

1. Set up PXE server with Ubuntu 22.04 image
2. Configure DHCP for PXE boot
3. Set `baremetal_pxe_server` in terraform.tfvars
4. Terraform will trigger PXE boot via IPMI

### 4. Verify IPMI Access

Test IPMI connectivity before deployment:

```bash
# Test IPMI access
ipmitool -I lanplus \
  -H 192.168.0.101 \
  -U admin \
  -P your-password \
  power status

# Should return: Chassis Power is on/off
```

### 5. Verify SSH Access

Test SSH connectivity:

```bash
# Test SSH access
ssh root@192.168.1.101 "hostname"

# Should return: k8s-cp-01
```

## Deployment

### Initialize Terraform

```bash
terraform init
```

### Plan Deployment

```bash
terraform plan
```

### Deploy Cluster

```bash
terraform apply
```

**Deployment Time:** Approximately 45-60 minutes

**Deployment Steps:**
1. Power on servers via IPMI (2 minutes)
2. OS installation via PXE (10 minutes, if used)
3. Network configuration (5 minutes)
4. Kubernetes installation (15 minutes)
5. Ceph cluster setup (20 minutes)
6. Storage classes creation (5 minutes)
7. MetalLB installation (3 minutes)

### Get Kubeconfig

```bash
# Copy kubeconfig from control plane
scp root@192.168.1.101:/etc/kubernetes/admin.conf ~/.kube/config

# Or use Terraform output
terraform output kubeconfig_command
```

### Verify Deployment

```bash
# Check cluster status
kubectl get nodes

# Check storage classes
kubectl get storageclass

# Check Ceph status
kubectl exec -n rook-ceph deploy/rook-ceph-tools -- ceph status

# Check MetalLB
kubectl get pods -n metallb-system
```

## Post-Deployment

### Access Ceph Dashboard

```bash
# Get Ceph dashboard URL
terraform output ceph_dashboard_url

# Get dashboard password
kubectl -n rook-ceph get secret rook-ceph-dashboard-password \
  -o jsonpath="{['data']['password']}" | base64 --decode

# Access: https://192.168.3.121:8443
```

### Deploy Banking Platform

```bash
# Deploy via Helm
cd ../../../helm/janusgraph-banking
helm install janusgraph-banking . \
  --namespace banking \
  --create-namespace \
  --values values.yaml
```

### Configure Monitoring

```bash
# Deploy Prometheus + Grafana
kubectl apply -f ../../../k8s/monitoring/
```

## Scaling

### Add Worker Nodes

1. Update `terraform.tfvars`:

```hcl
baremetal_worker_count = 3

baremetal_worker_hosts = [
  # Existing workers...
  {
    id           = "worker-03"
    ipmi_address = "192.168.0.113"
    ip_address   = "192.168.2.113"
    hostname     = "k8s-worker-03"
    mac_address  = "00:50:56:00:02:03"
  }
]
```

2. Apply changes:

```bash
terraform apply
```

### Enable HA Control Plane

1. Update `terraform.tfvars`:

```hcl
baremetal_control_plane_count = 3
baremetal_load_balancer_ip    = "192.168.1.100"

baremetal_control_plane_hosts = [
  # Add 2 more control plane nodes...
]
```

2. Apply changes:

```bash
terraform apply
```

## Maintenance

### Update Kubernetes

```bash
# SSH to control plane
ssh root@192.168.1.101

# Update kubeadm
apt-get update && apt-get install -y kubeadm=1.28.x-00

# Upgrade control plane
kubeadm upgrade apply v1.28.x

# Update kubelet
apt-get install -y kubelet=1.28.x-00
systemctl restart kubelet
```

### Expand Ceph Storage

```bash
# Add new OSD to existing node
ssh root@192.168.3.121

# Prepare new disk
ceph-volume lvm create --data /dev/sdc
```

### Backup Cluster

```bash
# Backup etcd
kubectl exec -n kube-system etcd-k8s-cp-01 -- \
  etcdctl snapshot save /tmp/etcd-backup.db

# Copy backup
kubectl cp kube-system/etcd-k8s-cp-01:/tmp/etcd-backup.db ./etcd-backup.db
```

## Troubleshooting

### IPMI Issues

```bash
# Check IPMI connectivity
ping 192.168.0.101

# Test IPMI commands
ipmitool -I lanplus -H 192.168.0.101 -U admin -P password chassis status

# Reset IPMI
ipmitool -I lanplus -H 192.168.0.101 -U admin -P password mc reset cold
```

### Network Issues

```bash
# Check network configuration
ssh root@192.168.1.101 "ip addr show"

# Test connectivity
ssh root@192.168.1.101 "ping -c 3 192.168.2.111"

# Check firewall
ssh root@192.168.1.101 "firewall-cmd --list-all"
```

### Ceph Issues

```bash
# Check Ceph health
kubectl exec -n rook-ceph deploy/rook-ceph-tools -- ceph health detail

# Check OSD status
kubectl exec -n rook-ceph deploy/rook-ceph-tools -- ceph osd tree

# Restart OSD
kubectl delete pod -n rook-ceph rook-ceph-osd-0-xxxxx
```

### Kubernetes Issues

```bash
# Check node status
kubectl get nodes -o wide

# Check pod status
kubectl get pods --all-namespaces

# Check logs
kubectl logs -n kube-system <pod-name>

# Restart kubelet
ssh root@192.168.1.101 "systemctl restart kubelet"
```

## Cleanup

### Destroy Cluster

```bash
# Destroy all resources
terraform destroy

# Confirm with: yes
```

**Warning:** This will:
- Power off all servers
- Delete Kubernetes cluster
- Remove Ceph data (if reclaim policy is Delete)
- Remove network configuration

### Manual Cleanup

If Terraform destroy fails:

```bash
# SSH to each node
ssh root@192.168.1.101

# Reset Kubernetes
kubeadm reset -f

# Clean Ceph
rm -rf /var/lib/ceph/*
rm -rf /var/lib/rook/*

# Wipe disks
wipefs -a /dev/sdb
```

## Cost Estimation

**Hardware Costs (One-Time):**
- Control Plane: $2,000 per node
- Workers: $3,000 per node
- HCD Nodes: $8,000 per node (with storage)
- Network Equipment: $5,000
- **Total: ~$35,000 for staging setup**

**Operational Costs (Monthly):**
- Power: ~$200/month
- Cooling: ~$100/month
- Network: ~$50/month
- **Total: ~$350/month**

## Support

For issues or questions:
- Check troubleshooting section above
- Review Terraform logs: `terraform.log`
- Check Kubernetes events: `kubectl get events --all-namespaces`
- Review Ceph logs: `kubectl logs -n rook-ceph <pod-name>`

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Rook-Ceph Documentation](https://rook.io/docs/rook/latest/)
- [MetalLB Documentation](https://metallb.universe.tf/)
- [HAProxy Documentation](http://www.haproxy.org/)
- [Keepalived Documentation](https://www.keepalived.org/)