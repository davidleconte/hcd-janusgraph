# Bare Metal Production Environment

This Terraform configuration deploys a production-grade, highly available Kubernetes cluster on bare metal infrastructure with enterprise features.

## Architecture

### Infrastructure Components

- **3 Control Plane Nodes** (HA with etcd quorum)
- **5-10 Worker Nodes** (scalable based on workload)
- **3 HCD Nodes** (Cassandra + Ceph storage)
- **Ceph Distributed Storage** (3x replication)
- **MetalLB Load Balancer** (L2 mode)
- **HAProxy + Keepalived** (API HA - mandatory)
- **Prometheus + Grafana** (monitoring)
- **Velero** (automated backups)
- **Falco + OPA Gatekeeper** (security)

### Network Layout

```
Control Plane: 10.10.1.0/24 (3 nodes)
Workers:       10.10.2.0/24 (5-10 nodes)
HCD Nodes:     10.10.3.0/24 (3 nodes)
Pod Network:   10.244.0.0/16
Services:      10.96.0.0/12
MetalLB Pool:  10.10.1.200-250
API VIP:       10.10.1.100 (HAProxy + Keepalived)
```

### High Availability Features

- **Control Plane HA:** 3 nodes with etcd quorum
- **API HA:** HAProxy + Keepalived with VIP
- **Storage HA:** Ceph 3x replication
- **Network HA:** MetalLB with multiple speakers
- **Application HA:** Pod Disruption Budgets
- **Auto-scaling:** Horizontal Pod Autoscaling

## Prerequisites

### Hardware Requirements

**Control Plane Nodes (3 required):**
- CPU: 8 cores minimum
- RAM: 32 GB minimum
- Disk: 200 GB SSD minimum
- Network: 10 Gbps recommended
- IPMI/BMC: Required

**Worker Nodes (5-10 required):**
- CPU: 16 cores minimum
- RAM: 64 GB minimum
- Disk: 500 GB SSD minimum
- Network: 10 Gbps recommended
- IPMI/BMC: Required

**HCD Nodes (3 required):**
- CPU: 32 cores minimum
- RAM: 256 GB minimum
- OS Disk: 200 GB SSD minimum
- Data Disk: 2 TB NVMe minimum (for Ceph)
- Network: 25 Gbps recommended
- IPMI/BMC: Required

### Software Requirements

- **IPMI/BMC Access** - All servers must have IPMI enabled
- **Ubuntu 22.04 LTS** - Pre-installed or via PXE
- **SSH Access** - Root or sudo access required
- **Terraform** - Version 1.5.0 or later
- **ipmitool** - For IPMI management
- **Internal DNS** - For production-grade name resolution
- **Internal NTP** - For time synchronization

### Network Requirements

- **Static IP Addresses** - All nodes require static IPs
- **Internal DNS** - Production DNS servers
- **Dedicated VLANs** - Network segmentation recommended
- **Firewall Rules** - Proper security policies
- **Load Balancer VIP** - Virtual IP for API HA
- **Internet Access** - For package downloads (or local mirror)

### Security Requirements

- **Strong Passwords** - Minimum 16 characters for IPMI
- **SSH Keys** - Key-based authentication only
- **Network Segmentation** - VLANs for different node types
- **Firewall** - Host-based and network firewalls
- **Audit Logging** - Enabled and retained for 365 days
- **Compliance** - SOC2, PCI-DSS ready

## Configuration

### 1. Copy Example Configuration

```bash
cd terraform/environments/baremetal-prod
cp terraform.tfvars.example terraform.tfvars
```

### 2. Update terraform.tfvars

**CRITICAL:** Update all passwords and sensitive values!

```hcl
# Control Plane Nodes (3 for HA)
baremetal_control_plane_hosts = [
  {
    id           = "cp-01"
    ipmi_address = "10.0.0.101"
    ip_address   = "10.10.1.101"
    hostname     = "k8s-prod-cp-01"
    mac_address  = "00:50:56:00:01:01"
  },
  # Add 2 more control plane nodes...
]

# Worker Nodes (5-10)
baremetal_worker_hosts = [
  # Add 5-10 worker nodes...
]

# HCD Nodes (3 for Ceph)
baremetal_hcd_hosts = [
  # Add 3 HCD nodes...
]

# CRITICAL: Change these passwords!
baremetal_ipmi_password = "YOUR_SECURE_PASSWORD_16_CHARS_MIN"
grafana_admin_password  = "YOUR_SECURE_PASSWORD_12_CHARS_MIN"

# Load Balancer VIP (MANDATORY)
baremetal_load_balancer_ip = "10.10.1.100"
```

### 3. Configure Remote Backend

Update `main.tf` backend configuration:

```hcl
backend "s3" {
  bucket         = "your-terraform-state-bucket"
  key            = "baremetal-prod/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-state-lock"
}
```

### 4. Prepare Servers

**Pre-deployment Checklist:**

- [ ] All servers have Ubuntu 22.04 LTS installed
- [ ] Static IP addresses configured
- [ ] SSH access configured with keys
- [ ] IPMI/BMC enabled and accessible
- [ ] Data disks attached to HCD nodes
- [ ] Network connectivity verified
- [ ] DNS records created
- [ ] NTP configured
- [ ] Firewall rules configured

### 5. Verify IPMI Access

```bash
# Test IPMI access to all nodes
for ip in 10.0.0.101 10.0.0.102 10.0.0.103; do
  echo "Testing $ip..."
  ipmitool -I lanplus -H $ip -U admin -P password power status
done
```

### 6. Verify SSH Access

```bash
# Test SSH access to all nodes
for ip in 10.10.1.101 10.10.1.102 10.10.1.103; do
  echo "Testing $ip..."
  ssh root@$ip "hostname"
done
```

## Deployment

### Initialize Terraform

```bash
terraform init
```

### Plan Deployment

```bash
terraform plan -out=tfplan
```

**Review the plan carefully!** Verify:
- All 11 nodes are included
- Network configuration is correct
- Load balancer VIP is set
- Storage configuration is correct

### Deploy Cluster

```bash
terraform apply tfplan
```

**Deployment Time:** Approximately 90-120 minutes

**Deployment Phases:**
1. Power on servers via IPMI (5 minutes)
2. Network configuration (10 minutes)
3. Kubernetes cluster initialization (30 minutes)
4. Ceph cluster setup (30 minutes)
5. Storage classes creation (10 minutes)
6. MetalLB installation (5 minutes)
7. HAProxy + Keepalived setup (10 minutes)
8. Monitoring stack deployment (15 minutes)
9. Security hardening (10 minutes)
10. Backup configuration (10 minutes)

### Get Kubeconfig

```bash
# Copy kubeconfig from control plane
scp root@10.10.1.101:/etc/kubernetes/admin.conf ~/.kube/config-prod

# Or use Terraform output
terraform output kubeconfig_command

# Set KUBECONFIG
export KUBECONFIG=~/.kube/config-prod
```

### Verify Deployment

```bash
# Check cluster status
kubectl get nodes -o wide

# Check control plane health
kubectl get pods -n kube-system

# Check storage classes
kubectl get storageclass

# Check Ceph status
kubectl exec -n rook-ceph deploy/rook-ceph-tools -- ceph status
kubectl exec -n rook-ceph deploy/rook-ceph-tools -- ceph osd tree

# Check MetalLB
kubectl get pods -n metallb-system
kubectl get ipaddresspool -n metallb-system

# Check HAProxy status
ssh root@10.10.1.101 "systemctl status haproxy"
ssh root@10.10.1.102 "systemctl status haproxy"
ssh root@10.10.1.103 "systemctl status haproxy"

# Check Keepalived VIP
ping 10.10.1.100

# Check monitoring
kubectl get pods -n monitoring

# Check security
kubectl get pods -n falco
kubectl get pods -n gatekeeper-system

# Check backups
kubectl exec -n velero deploy/velero -- velero backup get
```

## Post-Deployment

### Access Monitoring Dashboards

```bash
# Get Grafana URL
terraform output grafana_url

# Get Grafana admin password
echo $GRAFANA_ADMIN_PASSWORD

# Access Grafana
open http://10.10.1.100:3000

# Get Prometheus URL
terraform output prometheus_url

# Access Prometheus
open http://10.10.1.100:9090
```

### Access Ceph Dashboard

```bash
# Get Ceph dashboard URL
terraform output ceph_dashboard_url

# Get Ceph dashboard password
kubectl -n rook-ceph get secret rook-ceph-dashboard-password \
  -o jsonpath="{['data']['password']}" | base64 --decode

# Access Ceph dashboard
open https://10.10.3.121:8443
```

### Configure Alerting

```bash
# Update AlertManager configuration
kubectl edit configmap -n monitoring alertmanager-config

# Add Slack webhook
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'

# Add PagerDuty integration
receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
```

### Deploy Banking Platform

```bash
# Deploy via Helm
cd ../../../helm/janusgraph-banking
helm install janusgraph-banking . \
  --namespace banking \
  --create-namespace \
  --values values-prod.yaml

# Verify deployment
kubectl get pods -n banking
kubectl get svc -n banking
```

### Configure Backups

```bash
# Verify backup schedule
kubectl exec -n velero deploy/velero -- velero schedule get

# Test backup
kubectl exec -n velero deploy/velero -- velero backup create test-backup

# Check backup status
kubectl exec -n velero deploy/velero -- velero backup describe test-backup
```

## Operations

### Scaling

#### Add Worker Nodes

1. Update `terraform.tfvars`:

```hcl
baremetal_worker_count = 6

baremetal_worker_hosts = [
  # Existing workers...
  {
    id           = "worker-06"
    ipmi_address = "10.0.0.116"
    ip_address   = "10.10.2.116"
    hostname     = "k8s-prod-worker-06"
    mac_address  = "00:50:56:00:02:06"
  }
]
```

2. Apply changes:

```bash
terraform plan
terraform apply
```

#### Scale Application Workloads

```bash
# Scale deployment
kubectl scale deployment janusgraph-api -n banking --replicas=5

# Enable HPA
kubectl autoscale deployment janusgraph-api -n banking \
  --cpu-percent=70 \
  --min=3 \
  --max=10
```

### Maintenance

#### Update Kubernetes

```bash
# SSH to first control plane
ssh root@10.10.1.101

# Update kubeadm
apt-get update && apt-get install -y kubeadm=1.28.x-00

# Upgrade control plane
kubeadm upgrade plan
kubeadm upgrade apply v1.28.x

# Update kubelet and kubectl
apt-get install -y kubelet=1.28.x-00 kubectl=1.28.x-00
systemctl daemon-reload
systemctl restart kubelet

# Repeat for other control plane nodes
# Then update worker nodes
```

#### Expand Ceph Storage

```bash
# Add new OSD to existing node
ssh root@10.10.3.121

# Prepare new disk
ceph-volume lvm create --data /dev/sdc

# Verify OSD
ceph osd tree
```

#### Rotate Certificates

```bash
# Rotate Kubernetes certificates
kubeadm certs renew all

# Restart control plane components
systemctl restart kubelet
```

### Monitoring

#### Key Metrics to Monitor

- **Cluster Health:**
  - Node status and resource usage
  - Pod status and restarts
  - API server latency
  - etcd health and latency

- **Storage Health:**
  - Ceph cluster health
  - OSD status and usage
  - PV/PVC status
  - Storage capacity

- **Application Health:**
  - Pod CPU/Memory usage
  - Request latency
  - Error rates
  - Queue depths

- **Network Health:**
  - Network throughput
  - Packet loss
  - DNS latency
  - Load balancer health

#### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Node CPU | >70% | >90% |
| Node Memory | >75% | >90% |
| Disk Usage | >75% | >90% |
| Ceph Health | WARN | ERR |
| Pod Restarts | >3/hour | >10/hour |
| API Latency | >500ms | >1000ms |

### Backup & Recovery

#### Manual Backup

```bash
# Create full backup
kubectl exec -n velero deploy/velero -- velero backup create manual-backup-$(date +%Y%m%d)

# Backup specific namespace
kubectl exec -n velero deploy/velero -- velero backup create banking-backup \
  --include-namespaces banking

# Backup with volume snapshots
kubectl exec -n velero deploy/velero -- velero backup create full-backup \
  --snapshot-volumes
```

#### Restore from Backup

```bash
# List available backups
kubectl exec -n velero deploy/velero -- velero backup get

# Restore from backup
kubectl exec -n velero deploy/velero -- velero restore create \
  --from-backup manual-backup-20260219

# Restore specific namespace
kubectl exec -n velero deploy/velero -- velero restore create \
  --from-backup banking-backup \
  --include-namespaces banking
```

#### Disaster Recovery

**Scenario: Complete Cluster Loss**

1. **Restore Infrastructure:**
   ```bash
   cd terraform/environments/baremetal-prod
   terraform apply
   ```

2. **Restore etcd:**
   ```bash
   # Copy etcd backup to control plane
   scp etcd-backup.db root@10.10.1.101:/tmp/

   # Restore etcd
   ssh root@10.10.1.101
   ETCDCTL_API=3 etcdctl snapshot restore /tmp/etcd-backup.db \
     --data-dir=/var/lib/etcd-restore
   ```

3. **Restore Applications:**
   ```bash
   kubectl exec -n velero deploy/velero -- velero restore create \
     --from-backup latest-backup
   ```

4. **Verify Recovery:**
   ```bash
   kubectl get nodes
   kubectl get pods --all-namespaces
   kubectl exec -n rook-ceph deploy/rook-ceph-tools -- ceph status
   ```

## Troubleshooting

### Control Plane Issues

```bash
# Check control plane pods
kubectl get pods -n kube-system

# Check etcd health
kubectl exec -n kube-system etcd-k8s-prod-cp-01 -- \
  etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health

# Check API server logs
kubectl logs -n kube-system kube-apiserver-k8s-prod-cp-01
```

### Load Balancer Issues

```bash
# Check HAProxy status
ssh root@10.10.1.101 "systemctl status haproxy"
ssh root@10.10.1.101 "cat /var/log/haproxy.log"

# Check Keepalived status
ssh root@10.10.1.101 "systemctl status keepalived"
ssh root@10.10.1.101 "ip addr show | grep 10.10.1.100"

# Test VIP connectivity
ping 10.10.1.100
curl -k https://10.10.1.100:6443/healthz
```

### Ceph Issues

```bash
# Check Ceph health
kubectl exec -n rook-ceph deploy/rook-ceph-tools -- ceph health detail

# Check OSD status
kubectl exec -n rook-ceph deploy/rook-ceph-tools -- ceph osd tree
kubectl exec -n rook-ceph deploy/rook-ceph-tools -- ceph osd df

# Check pool status
kubectl exec -n rook-ceph deploy/rook-ceph-tools -- ceph df

# Restart problematic OSD
kubectl delete pod -n rook-ceph rook-ceph-osd-0-xxxxx
```

### Network Issues

```bash
# Check pod network
kubectl get pods -n kube-system -l k8s-app=calico-node

# Check MetalLB
kubectl get pods -n metallb-system
kubectl logs -n metallb-system -l app=metallb

# Test DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup kubernetes.default
```

## Security

### Security Hardening Checklist

- [x] IPMI passwords changed from defaults
- [x] SSH key-based authentication only
- [x] Firewall rules configured
- [x] Network segmentation (VLANs)
- [x] Pod Security Standards enforced
- [x] OPA Gatekeeper policies applied
- [x] Falco runtime security enabled
- [x] Audit logging enabled (365 days retention)
- [x] Secrets encrypted at rest
- [x] TLS for all communications
- [x] Regular security updates
- [x] Vulnerability scanning

### Compliance

**SOC 2 Type II:**
- Audit logging: 365 days retention
- Access controls: RBAC enforced
- Encryption: At rest and in transit
- Monitoring: 24/7 with alerts
- Backup: Daily with 90-day retention

**PCI DSS:**
- Network segmentation: VLANs
- Access controls: MFA required
- Encryption: AES-256
- Logging: Centralized and retained
- Vulnerability management: Regular scans

## Cost Analysis

### Hardware Costs (One-Time)

| Item | Quantity | Unit Cost | Total |
|------|----------|-----------|-------|
| Control Plane Server | 3 | $4,000 | $12,000 |
| Worker Server | 5 | $6,000 | $30,000 |
| HCD Server (with storage) | 3 | $15,000 | $45,000 |
| Network Switch (25G) | 2 | $8,000 | $16,000 |
| Firewall | 1 | $5,000 | $5,000 |
| UPS | 2 | $3,000 | $6,000 |
| Rack & Cables | - | $4,000 | $4,000 |
| **Total Hardware** | - | - | **$118,000** |

### Operational Costs (Monthly)

| Item | Cost |
|------|------|
| Power (11 servers @ ~400W) | $350 |
| Cooling | $200 |
| Network Bandwidth | $100 |
| Maintenance | $500 |
| **Total Monthly** | **$1,150** |

### 3-Year TCO Comparison

| Deployment | Setup Cost | Monthly Cost | 3-Year TCO |
|------------|------------|--------------|------------|
| Bare Metal | $118,000 | $1,150 | $159,400 |
| AWS EKS | $0 | $8,500 | $306,000 |
| Azure AKS | $0 | $8,200 | $295,200 |
| GCP GKE | $0 | $8,300 | $298,800 |

**Savings:** Bare metal saves ~$135,000-$146,000 over 3 years compared to cloud.

## Support

### Escalation Path

1. **Level 1:** Check documentation and troubleshooting guide
2. **Level 2:** Review monitoring dashboards and logs
3. **Level 3:** Contact platform engineering team
4. **Level 4:** Engage vendor support (if applicable)

### Emergency Contacts

- **Platform Engineering:** platform-team@example.com
- **Security Team:** security@example.com
- **On-Call:** +1-555-0100 (PagerDuty)

### Documentation

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Rook-Ceph Documentation](https://rook.io/docs/rook/latest/)
- [MetalLB Documentation](https://metallb.universe.tf/)
- [HAProxy Documentation](http://www.haproxy.org/)
- [Velero Documentation](https://velero.io/docs/)

## Appendix

### Network Diagram

```
                    ┌─────────────────────┐
                    │   Internet/WAN      │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │     Firewall        │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Core Switch (25G)  │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐   ┌─────────▼────────┐   ┌────────▼───────┐
│ Control Plane  │   │    Workers       │   │   HCD Nodes    │
│   VLAN 10      │   │    VLAN 20       │   │   VLAN 30      │
│ 10.10.1.0/24   │   │  10.10.2.0/24    │   │ 10.10.3.0/24   │
│                │   │                  │   │                │
│ CP-01: .101    │   │ W-01: .111       │   │ HCD-01: .121   │
│ CP-02: .102    │   │ W-02: .112       │   │ HCD-02: .122   │
│ CP-03: .103    │   │ W-03: .113       │   │ HCD-03: .123   │
│                │   │ W-04: .114       │   │                │
│ VIP:   .100    │   │ W-05: .115       │   │ Ceph Cluster   │
└────────────────┘   └──────────────────┘   └────────────────┘
```

### Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-19 | 1.0 | Initial production configuration |

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-19  
**Maintained By:** Platform Engineering Team