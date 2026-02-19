# Horizontal Scaling Guide

**Version:** 1.0  
**Date:** 2026-02-19  
**Status:** Active

## Overview

This guide provides comprehensive procedures for horizontally scaling the JanusGraph Banking Platform across all deployment platforms (AWS, Azure, GCP, vSphere, Bare Metal).

## Table of Contents

1. [Scaling Strategies](#scaling-strategies)
2. [Kubernetes Cluster Scaling](#kubernetes-cluster-scaling)
3. [Application Scaling](#application-scaling)
4. [Database Scaling](#database-scaling)
5. [Storage Scaling](#storage-scaling)
6. [Network Scaling](#network-scaling)
7. [Monitoring & Metrics](#monitoring--metrics)
8. [Cost Optimization](#cost-optimization)
9. [Troubleshooting](#troubleshooting)

---

## Scaling Strategies

### Manual Scaling

**When to Use:**
- Predictable traffic patterns
- Scheduled events
- Cost-sensitive environments
- Testing and validation

**Advantages:**
- Full control over resources
- Predictable costs
- No automation overhead

**Disadvantages:**
- Requires manual intervention
- Slower response to load changes
- Risk of under/over-provisioning

### Automatic Scaling (HPA)

**When to Use:**
- Unpredictable traffic patterns
- Variable workloads
- Production environments
- 24/7 operations

**Advantages:**
- Automatic response to load
- Optimal resource utilization
- Reduced operational overhead

**Disadvantages:**
- Requires proper metrics configuration
- Potential cost variability
- Complexity in tuning

### Scheduled Scaling

**When to Use:**
- Known traffic patterns
- Business hours scaling
- Batch processing windows
- Cost optimization

**Advantages:**
- Proactive scaling
- Cost predictability
- Reduced latency

**Disadvantages:**
- Requires accurate forecasting
- Less flexible than HPA
- Manual schedule updates

---

## Kubernetes Cluster Scaling

### AWS EKS Cluster Scaling

#### Add Worker Nodes

```bash
# Update Terraform configuration
cd terraform/environments/prod

# Edit terraform.tfvars
vim terraform.tfvars
```

```hcl
# Increase node count
node_count     = 5  # Was 3
node_count_min = 3
node_count_max = 10
```

```bash
# Apply changes
terraform plan
terraform apply

# Verify new nodes
kubectl get nodes
```

#### Enable Cluster Autoscaler

```bash
# Deploy cluster autoscaler
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Configure autoscaler
kubectl -n kube-system edit deployment cluster-autoscaler
```

```yaml
spec:
  template:
    spec:
      containers:
      - name: cluster-autoscaler
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/janusgraph-prod
        - --balance-similar-node-groups
        - --skip-nodes-with-system-pods=false
```

### Azure AKS Cluster Scaling

#### Manual Scaling

```bash
# Scale node pool
az aks nodepool scale \
  --resource-group janusgraph-prod-rg \
  --cluster-name janusgraph-prod-aks \
  --name workerpool \
  --node-count 5

# Verify
kubectl get nodes
```

#### Enable Autoscaler

```bash
# Enable cluster autoscaler
az aks nodepool update \
  --resource-group janusgraph-prod-rg \
  --cluster-name janusgraph-prod-aks \
  --name workerpool \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 10

# Update autoscaler settings
az aks update \
  --resource-group janusgraph-prod-rg \
  --name janusgraph-prod-aks \
  --cluster-autoscaler-profile \
    scale-down-delay-after-add=10m \
    scale-down-unneeded-time=10m
```

### GCP GKE Cluster Scaling

#### Manual Scaling

```bash
# Scale node pool
gcloud container clusters resize janusgraph-prod-gke \
  --node-pool worker-pool \
  --num-nodes 5 \
  --region us-central1

# Verify
kubectl get nodes
```

#### Enable Autoscaler

```bash
# Enable autoscaling
gcloud container clusters update janusgraph-prod-gke \
  --enable-autoscaling \
  --node-pool worker-pool \
  --min-nodes 3 \
  --max-nodes 10 \
  --region us-central1

# Update autoscaler profile
gcloud container clusters update janusgraph-prod-gke \
  --autoscaling-profile optimize-utilization \
  --region us-central1
```

### vSphere Cluster Scaling

#### Add Worker Nodes

```bash
# Update Terraform configuration
cd terraform/environments/vsphere-prod

# Edit terraform.tfvars
vim terraform.tfvars
```

```hcl
# Add new worker nodes
vsphere_worker_count = 5  # Was 3

vsphere_worker_hosts = [
  # Existing workers...
  {
    name       = "k8s-worker-04"
    ip_address = "192.168.2.114"
    cpu        = 8
    memory     = 32768
    disk_size  = 200
  },
  {
    name       = "k8s-worker-05"
    ip_address = "192.168.2.115"
    cpu        = 8
    memory     = 32768
    disk_size  = 200
  }
]
```

```bash
# Apply changes
terraform plan
terraform apply

# Verify new nodes
kubectl get nodes
```

### Bare Metal Cluster Scaling

#### Add Worker Nodes

```bash
# Update Terraform configuration
cd terraform/environments/baremetal-prod

# Edit terraform.tfvars
vim terraform.tfvars
```

```hcl
# Add new worker nodes
baremetal_worker_count = 6  # Was 5

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

```bash
# Apply changes
terraform plan
terraform apply

# Verify new node
kubectl get nodes

# Check node status
kubectl describe node k8s-prod-worker-06
```

---

## Application Scaling

### Manual Pod Scaling

#### Scale Deployment

```bash
# Scale API deployment
kubectl scale deployment janusgraph-api \
  -n banking \
  --replicas=5

# Verify
kubectl get pods -n banking -l app=janusgraph-api

# Check resource usage
kubectl top pods -n banking -l app=janusgraph-api
```

#### Scale StatefulSet

```bash
# Scale HCD StatefulSet
kubectl scale statefulset hcd \
  -n banking \
  --replicas=5

# Verify
kubectl get pods -n banking -l app=hcd

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod \
  -l app=hcd \
  -n banking \
  --timeout=300s
```

### Horizontal Pod Autoscaler (HPA)

#### Create HPA for API

```bash
# Create HPA based on CPU
kubectl autoscale deployment janusgraph-api \
  -n banking \
  --cpu-percent=70 \
  --min=3 \
  --max=10

# Verify HPA
kubectl get hpa -n banking

# Describe HPA
kubectl describe hpa janusgraph-api -n banking
```

#### Create HPA with Custom Metrics

```yaml
# hpa-api-custom.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: janusgraph-api
  namespace: banking
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: janusgraph-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 30
      selectPolicy: Max
```

```bash
# Apply HPA
kubectl apply -f hpa-api-custom.yaml

# Monitor HPA
watch kubectl get hpa -n banking
```

### Vertical Pod Autoscaler (VPA)

#### Install VPA

```bash
# Clone VPA repository
git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler

# Install VPA
./hack/vpa-up.sh

# Verify installation
kubectl get pods -n kube-system | grep vpa
```

#### Create VPA for API

```yaml
# vpa-api.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: janusgraph-api-vpa
  namespace: banking
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: janusgraph-api
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: janusgraph-api
      minAllowed:
        cpu: 100m
        memory: 256Mi
      maxAllowed:
        cpu: 2000m
        memory: 4Gi
      controlledResources:
      - cpu
      - memory
```

```bash
# Apply VPA
kubectl apply -f vpa-api.yaml

# Check VPA recommendations
kubectl describe vpa janusgraph-api-vpa -n banking
```

---

## Database Scaling

### HCD (Cassandra) Scaling

#### Add HCD Nodes

```bash
# Scale HCD StatefulSet
kubectl scale statefulset hcd \
  -n banking \
  --replicas=5

# Wait for new pods
kubectl wait --for=condition=ready pod \
  -l app=hcd \
  -n banking \
  --timeout=600s

# Verify cluster status
kubectl exec -it hcd-0 -n banking -- nodetool status

# Run repair on new nodes
kubectl exec -it hcd-4 -n banking -- nodetool repair
```

#### Rebalance Data

```bash
# Check data distribution
kubectl exec -it hcd-0 -n banking -- nodetool ring

# Run cleanup on existing nodes
for i in {0..2}; do
  kubectl exec -it hcd-$i -n banking -- nodetool cleanup
done

# Verify data distribution
kubectl exec -it hcd-0 -n banking -- nodetool status
```

### JanusGraph Scaling

#### Scale JanusGraph Server

```bash
# Scale JanusGraph deployment
kubectl scale deployment janusgraph-server \
  -n banking \
  --replicas=5

# Verify
kubectl get pods -n banking -l app=janusgraph-server

# Check connection pool
kubectl logs -n banking janusgraph-server-0 | grep "connection pool"
```

#### Configure Connection Pooling

```yaml
# janusgraph-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: janusgraph-config
  namespace: banking
data:
  janusgraph-server.yaml: |
    storage:
      backend: hbase
      hostname: hcd-service
      hbase:
        connection-pool-size: 100
        connection-timeout: 30000
    cache:
      db-cache: true
      db-cache-time: 180000
      db-cache-size: 0.5
```

---

## Storage Scaling

### AWS EBS Scaling

#### Expand PVC

```bash
# Edit PVC
kubectl edit pvc hcd-data-hcd-0 -n banking
```

```yaml
spec:
  resources:
    requests:
      storage: 200Gi  # Was 100Gi
```

```bash
# Verify expansion
kubectl get pvc -n banking

# Check pod events
kubectl describe pod hcd-0 -n banking
```

### Azure Disk Scaling

#### Expand Managed Disk

```bash
# Expand PVC
kubectl patch pvc hcd-data-hcd-0 -n banking \
  -p '{"spec":{"resources":{"requests":{"storage":"200Gi"}}}}'

# Verify
kubectl get pvc -n banking -w
```

### GCP Persistent Disk Scaling

#### Expand PD

```bash
# Expand PVC
kubectl patch pvc hcd-data-hcd-0 -n banking \
  -p '{"spec":{"resources":{"requests":{"storage":"200Gi"}}}}'

# Verify
kubectl get pvc -n banking
```

### Ceph Storage Scaling (Bare Metal/vSphere)

#### Add Ceph OSD

```bash
# SSH to HCD node
ssh root@10.10.3.121

# Prepare new disk
parted -s /dev/sdc mklabel gpt
parted -s /dev/sdc mkpart primary xfs 0% 100%
mkfs.xfs -f /dev/sdc1

# Create OSD
OSD_ID=$(ceph osd create)
mkdir -p /var/lib/ceph/osd/ceph-$OSD_ID
mount /dev/sdc1 /var/lib/ceph/osd/ceph-$OSD_ID

# Initialize OSD
ceph-osd -i $OSD_ID --mkfs --mkkey

# Register OSD
ceph auth add osd.$OSD_ID osd 'allow *' mon 'allow profile osd' \
  -i /var/lib/ceph/osd/ceph-$OSD_ID/keyring

# Add to CRUSH map
ceph osd crush add osd.$OSD_ID 1.0 host=k8s-prod-hcd-01

# Start OSD
systemctl enable ceph-osd@$OSD_ID
systemctl start ceph-osd@$OSD_ID

# Verify
ceph osd tree
ceph -s
```

---

## Network Scaling

### MetalLB IP Pool Expansion

```bash
# Edit MetalLB config
kubectl edit configmap config -n metallb-system
```

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: config
  namespace: metallb-system
data:
  config: |
    address-pools:
    - name: default
      protocol: layer2
      addresses:
      - 10.10.1.200-10.10.1.250  # Expanded from 200-220
```

```bash
# Restart MetalLB
kubectl rollout restart deployment controller -n metallb-system
kubectl rollout restart daemonset speaker -n metallb-system
```

### Ingress Controller Scaling

```bash
# Scale NGINX Ingress
kubectl scale deployment ingress-nginx-controller \
  -n ingress-nginx \
  --replicas=3

# Enable HPA for Ingress
kubectl autoscale deployment ingress-nginx-controller \
  -n ingress-nginx \
  --cpu-percent=75 \
  --min=2 \
  --max=5
```

---

## Monitoring & Metrics

### Key Metrics to Monitor

#### Cluster Metrics

```bash
# Node resource usage
kubectl top nodes

# Pod resource usage
kubectl top pods -n banking

# HPA status
kubectl get hpa -n banking

# VPA recommendations
kubectl describe vpa -n banking
```

#### Application Metrics

```promql
# Request rate
rate(http_requests_total[5m])

# Response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Pod CPU usage
container_cpu_usage_seconds_total{namespace="banking"}

# Pod memory usage
container_memory_usage_bytes{namespace="banking"}
```

#### Database Metrics

```promql
# HCD read latency
cassandra_read_latency_seconds

# HCD write latency
cassandra_write_latency_seconds

# JanusGraph query latency
janusgraph_query_duration_seconds

# Connection pool usage
janusgraph_connection_pool_active
```

### Grafana Dashboards

```bash
# Import scaling dashboard
kubectl create configmap scaling-dashboard \
  -n monitoring \
  --from-file=scaling-dashboard.json

# Access Grafana
kubectl port-forward -n monitoring svc/grafana 3000:80
```

---

## Cost Optimization

### Right-Sizing Recommendations

#### Analyze Resource Usage

```bash
# Get resource usage over time
kubectl top pods -n banking --containers

# Get VPA recommendations
kubectl get vpa -n banking -o yaml

# Analyze with Prometheus
# Query: avg_over_time(container_cpu_usage_seconds_total[7d])
```

#### Implement Recommendations

```yaml
# Update deployment with right-sized resources
apiVersion: apps/v1
kind: Deployment
metadata:
  name: janusgraph-api
spec:
  template:
    spec:
      containers:
      - name: api
        resources:
          requests:
            cpu: 500m      # Based on VPA recommendation
            memory: 1Gi    # Based on VPA recommendation
          limits:
            cpu: 2000m
            memory: 4Gi
```

### Spot/Preemptible Instances

#### AWS Spot Instances

```hcl
# terraform/environments/prod/terraform.tfvars
capacity_type = "SPOT"
```

#### Azure Spot VMs

```hcl
# terraform/environments/azure-prod/terraform.tfvars
azure_spot_enabled = true
azure_spot_max_price = -1  # Pay up to on-demand price
```

#### GCP Preemptible VMs

```hcl
# terraform/environments/gcp-prod/terraform.tfvars
gcp_preemptible = true
```

### Scheduled Scaling

```yaml
# scheduled-scaler.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-up-business-hours
  namespace: banking
spec:
  schedule: "0 8 * * 1-5"  # 8 AM Mon-Fri
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: kubectl
            image: bitnami/kubectl:latest
            command:
            - /bin/sh
            - -c
            - |
              kubectl scale deployment janusgraph-api -n banking --replicas=10
          restartPolicy: OnFailure
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-down-after-hours
  namespace: banking
spec:
  schedule: "0 18 * * 1-5"  # 6 PM Mon-Fri
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: kubectl
            image: bitnami/kubectl:latest
            command:
            - /bin/sh
            - -c
            - |
              kubectl scale deployment janusgraph-api -n banking --replicas=3
          restartPolicy: OnFailure
```

---

## Troubleshooting

### Common Issues

#### Pods Not Scaling

**Symptoms:**
- HPA shows `<unknown>` for metrics
- Pods remain at min replicas despite high load

**Solutions:**

```bash
# Check metrics server
kubectl get deployment metrics-server -n kube-system

# Check HPA status
kubectl describe hpa janusgraph-api -n banking

# Check pod metrics
kubectl top pods -n banking

# Restart metrics server if needed
kubectl rollout restart deployment metrics-server -n kube-system
```

#### Nodes Not Joining Cluster

**Symptoms:**
- New nodes in `NotReady` state
- Nodes not appearing in `kubectl get nodes`

**Solutions:**

```bash
# Check node status
kubectl describe node <node-name>

# Check kubelet logs
ssh <node-ip>
journalctl -u kubelet -f

# Check network connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- ping <node-ip>

# Rejoin node if needed
ssh <node-ip>
kubeadm reset
kubeadm join <api-server>:6443 --token <token> --discovery-token-ca-cert-hash <hash>
```

#### Storage Expansion Failing

**Symptoms:**
- PVC remains in `Resizing` state
- Pod cannot mount expanded volume

**Solutions:**

```bash
# Check PVC status
kubectl describe pvc <pvc-name> -n banking

# Check storage class
kubectl get storageclass

# Restart pod to trigger resize
kubectl delete pod <pod-name> -n banking

# Check pod events
kubectl describe pod <pod-name> -n banking
```

---

## Best Practices

### Scaling Checklist

- [ ] Monitor resource usage before scaling
- [ ] Set appropriate resource requests/limits
- [ ] Configure HPA with proper metrics
- [ ] Test scaling in non-production first
- [ ] Document scaling decisions
- [ ] Monitor costs after scaling
- [ ] Set up alerts for scaling events
- [ ] Review and optimize regularly

### Performance Tuning

1. **Connection Pooling:** Increase pool sizes for scaled applications
2. **Caching:** Implement caching to reduce database load
3. **Load Balancing:** Ensure even distribution across pods
4. **Health Checks:** Configure proper liveness/readiness probes
5. **Resource Limits:** Set appropriate CPU/memory limits
6. **Network Policies:** Optimize network policies for scaled deployments

### Cost Management

1. **Right-Sizing:** Use VPA recommendations
2. **Spot Instances:** Use for non-critical workloads
3. **Scheduled Scaling:** Scale down during off-hours
4. **Resource Cleanup:** Remove unused resources
5. **Monitoring:** Track costs per namespace/deployment

---

## Appendix

### Scaling Decision Matrix

| Metric | Scale Up Threshold | Scale Down Threshold | Action |
|--------|-------------------|---------------------|--------|
| CPU Usage | >70% for 5 min | <30% for 10 min | Add/Remove pods |
| Memory Usage | >80% for 5 min | <40% for 10 min | Add/Remove pods |
| Request Rate | >1000 req/s | <200 req/s | Add/Remove pods |
| Response Time | >500ms (p95) | <100ms (p95) | Add/Remove pods |
| Error Rate | >1% | <0.1% | Investigate first |
| Queue Depth | >100 | <10 | Add/Remove workers |

### Scaling Runbook

**Incident:** High CPU usage on API pods

1. **Assess:** Check current metrics
   ```bash
   kubectl top pods -n banking -l app=janusgraph-api
   ```

2. **Scale:** Increase replicas
   ```bash
   kubectl scale deployment janusgraph-api -n banking --replicas=10
   ```

3. **Monitor:** Watch for improvement
   ```bash
   watch kubectl get hpa -n banking
   ```

4. **Verify:** Check application health
   ```bash
   curl https://api.example.com/health
   ```

5. **Document:** Record scaling event
   ```bash
   echo "$(date): Scaled API to 10 replicas due to high CPU" >> scaling-log.txt
   ```

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-19  
**Maintained By:** Platform Engineering Team  
**Next Review:** 2026-03-19