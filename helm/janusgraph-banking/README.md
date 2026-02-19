# JanusGraph Banking Platform - Helm Chart

Enterprise-grade Banking Fraud Detection & AML Compliance platform on JanusGraph with IBM DataStax HCD.

## Overview

This Helm chart deploys a complete banking graph analytics platform with:

- **IBM DataStax HCD** (Hyper-Converged Database) - Enterprise Cassandra distribution
- **JanusGraph** - Distributed graph database (StatefulSet)
- **Mission Control** - Centralized HCD cluster management
- **OpenSearch** - Full-text search and analytics
- **Apache Pulsar** - Event streaming with geo-replication
- **HashiCorp Vault** - Secrets management
- **Monitoring Stack** - Prometheus, Grafana, AlertManager

## Prerequisites

### Required

- Kubernetes 1.24+ or OpenShift 4.12+
- Helm 3.8+
- kubectl or oc CLI
- Persistent storage provisioner (StorageClass)
- Minimum 3 worker nodes for production

### Resource Requirements

**Per Site (3-node cluster):**
- CPU: 24 cores minimum (HCD: 12, JanusGraph: 6, Others: 6)
- Memory: 64 GB minimum (HCD: 48GB, JanusGraph: 12GB, Others: 4GB)
- Storage: 1.5 TB minimum (HCD: 1.5TB, JanusGraph: 300GB, Others: 200GB)

## Installation

### 1. Add Helm Repositories

```bash
# Add DataStax repository for Cass Operator
helm repo add datastax https://datastax.github.io/charts

# Add OpenSearch repository
helm repo add opensearch https://opensearch-project.github.io/helm-charts

# Add Pulsar repository
helm repo add pulsar https://pulsar.apache.org/charts

# Add HashiCorp repository
helm repo add hashicorp https://helm.releases.hashicorp.com

# Update repositories
helm repo update
```

### 2. Create Namespace

```bash
kubectl create namespace janusgraph-banking
```

### 3. Create Secrets

```bash
# Create Mission Control secrets
kubectl create secret generic mission-control-secrets \
  --from-literal=postgres-user=mcadmin \
  --from-literal=postgres-password=CHANGE_ME \
  --from-literal=admin-user=admin \
  --from-literal=admin-password=CHANGE_ME \
  --from-literal=agent-token=CHANGE_ME \
  -n janusgraph-banking

# Create JanusGraph secrets
kubectl create secret generic janusgraph-secrets \
  --from-literal=password=CHANGE_ME \
  -n janusgraph-banking

# Create OpenSearch secrets
kubectl create secret generic opensearch-secrets \
  --from-literal=password=CHANGE_ME \
  -n janusgraph-banking
```

### 4. Install Dependencies

```bash
# Update Helm dependencies
helm dependency update

# This will download:
# - cass-operator (DataStax Cass Operator for HCD)
# - opensearch
# - pulsar
# - vault
```

### 5. Install Chart

**Development:**

```bash
helm install janusgraph-banking . \
  --namespace janusgraph-banking \
  --create-namespace \
  --wait \
  --timeout 30m
```

**Production (3-site deployment):**

```bash
# Site 1 (Paris)
helm install janusgraph-banking-paris . \
  --namespace janusgraph-banking \
  --values values-prod.yaml \
  --set hcd.datacenterName=paris-dc \
  --set hcd.racks[0].zone=eu-west-3a \
  --set hcd.racks[1].zone=eu-west-3b \
  --set hcd.racks[2].zone=eu-west-3c \
  --wait \
  --timeout 30m

# Site 2 (London)
helm install janusgraph-banking-london . \
  --namespace janusgraph-banking \
  --values values-prod.yaml \
  --set hcd.datacenterName=london-dc \
  --set hcd.racks[0].zone=eu-west-2a \
  --set hcd.racks[1].zone=eu-west-2b \
  --set hcd.racks[2].zone=eu-west-2c \
  --wait \
  --timeout 30m

# Site 3 (Frankfurt)
helm install janusgraph-banking-frankfurt . \
  --namespace janusgraph-banking \
  --values values-prod.yaml \
  --set hcd.datacenterName=frankfurt-dc \
  --set hcd.racks[0].zone=eu-central-1a \
  --set hcd.racks[1].zone=eu-central-1b \
  --set hcd.racks[2].zone=eu-central-1c \
  --wait \
  --timeout 30m
```

## Verification

### Check HCD Cluster Status

```bash
# Check CassandraDatacenter CRD
kubectl get cassandradatacenters -n janusgraph-banking

# Check HCD pods
kubectl get pods -n janusgraph-banking -l cassandra.datastax.com/cluster=hcd-cluster-global

# Check cluster status
kubectl exec -it hcd-cluster-global-paris-dc-default-sts-0 -n janusgraph-banking -- nodetool status

# Expected output:
# Datacenter: paris-dc
# Status=Up/Down
# |/ State=Normal/Leaving/Joining/Moving
# --  Address     Load       Tokens  Owns    Host ID                               Rack
# UN  10.0.1.10   1.5 TB     16      33.3%   a1b2c3d4-...                          rack1
# UN  10.0.1.11   1.5 TB     16      33.3%   e5f6g7h8-...                          rack2
# UN  10.0.1.12   1.5 TB     16      33.3%   i9j0k1l2-...                          rack3
```

### Check JanusGraph StatefulSet

```bash
# Check StatefulSet
kubectl get statefulsets -n janusgraph-banking

# Check pods
kubectl get pods -n janusgraph-banking -l app=janusgraph

# Check PVCs
kubectl get pvc -n janusgraph-banking

# Test JanusGraph connection
kubectl port-forward svc/janusgraph 8182:8182 -n janusgraph-banking
curl http://localhost:8182?gremlin=g.V().count()
```

### Check Mission Control

```bash
# Check Mission Control pods
kubectl get pods -n janusgraph-banking -l app=mission-control-server
kubectl get pods -n janusgraph-banking -l app=mission-control-agent

# Access Mission Control UI
kubectl port-forward svc/mission-control-server 8080:8080 -n janusgraph-banking
# Open browser to http://localhost:8080
```

## Configuration

### Key Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `hcd.enabled` | Enable HCD deployment | `true` |
| `hcd.size` | Number of HCD nodes | `3` |
| `hcd.storageSize` | Storage per HCD node | `500Gi` |
| `janusgraph.enabled` | Enable JanusGraph | `true` |
| `janusgraph.replicas` | Number of JanusGraph pods | `3` |
| `janusgraph.storage.size` | Storage per JanusGraph pod | `100Gi` |
| `missionControl.enabled` | Enable Mission Control | `true` |
| `missionControl.server.replicas` | Mission Control server replicas | `2` |
| `opensearch.enabled` | Enable OpenSearch | `true` |
| `pulsar.enabled` | Enable Pulsar | `true` |
| `vault.enabled` | Enable Vault | `true` |

### Storage Classes

The chart creates StorageClasses for each component. Modify `storageClasses` section in `values.yaml` to match your cloud provider:

**AWS:**
```yaml
storageClasses:
  hcd:
    provisioner: ebs.csi.aws.com
    parameters:
      type: gp3
      iops: "3000"
      encrypted: "true"
```

**Azure:**
```yaml
storageClasses:
  hcd:
    provisioner: disk.csi.azure.com
    parameters:
      storageaccounttype: Premium_LRS
      kind: Managed
```

**GCP:**
```yaml
storageClasses:
  hcd:
    provisioner: pd.csi.storage.gke.io
    parameters:
      type: pd-ssd
```

## Multi-DC Deployment

### Create Keyspace with Multi-DC Replication

```bash
# Connect to HCD
kubectl exec -it hcd-cluster-global-paris-dc-default-sts-0 -n janusgraph-banking -- cqlsh

# Create keyspace
CREATE KEYSPACE janusgraph
WITH replication = {
  'class': 'NetworkTopologyStrategy',
  'paris-dc': 3,
  'london-dc': 3,
  'frankfurt-dc': 3
}
AND durable_writes = true;
```

### Register Clusters with Mission Control

```bash
# Get Mission Control URL
export MC_URL=$(kubectl get svc mission-control-server -n janusgraph-banking -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Register HCD cluster
curl -X POST http://$MC_URL:8080/api/v1/clusters \
  -H "Authorization: Bearer $MC_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hcd-cluster-global",
    "datacenters": [
      {"name": "paris-dc", "nodes": ["..."]},
      {"name": "london-dc", "nodes": ["..."]},
      {"name": "frankfurt-dc", "nodes": ["..."]}
    ]
  }'
```

## Backup and Restore

### Configure Backups

Backups are configured via Mission Control. Default schedule: Daily at 2 AM.

```bash
# Trigger manual backup
kubectl exec -it hcd-cluster-global-paris-dc-default-sts-0 -n janusgraph-banking -- \
  medusa backup --backup-name manual-backup-$(date +%Y%m%d)

# List backups
kubectl exec -it hcd-cluster-global-paris-dc-default-sts-0 -n janusgraph-banking -- \
  medusa list-backups

# Restore from backup
kubectl exec -it hcd-cluster-global-paris-dc-default-sts-0 -n janusgraph-banking -- \
  medusa restore --backup-name manual-backup-20260219
```

## Monitoring

### Access Monitoring Dashboards

```bash
# Prometheus
kubectl port-forward svc/prometheus-server 9090:9090 -n janusgraph-banking
# Open http://localhost:9090

# Grafana
kubectl port-forward svc/grafana 3000:3000 -n janusgraph-banking
# Open http://localhost:3000
# Default credentials: admin/admin (change on first login)
```

### Key Metrics

- `janusgraph_vertices_total` - Total vertex count
- `janusgraph_edges_total` - Total edge count
- `janusgraph_query_duration_seconds` - Query latency
- `cassandra_node_status` - HCD node health
- `mission_control_cluster_health` - Cluster health score

## Troubleshooting

### HCD Pods Not Starting

```bash
# Check pod events
kubectl describe pod hcd-cluster-global-paris-dc-default-sts-0 -n janusgraph-banking

# Check logs
kubectl logs hcd-cluster-global-paris-dc-default-sts-0 -n janusgraph-banking

# Common issues:
# - Insufficient resources: Increase node capacity
# - Storage not available: Check StorageClass and PVC
# - Network issues: Check NetworkPolicies
```

### JanusGraph Cannot Connect to HCD

```bash
# Check HCD service
kubectl get svc -n janusgraph-banking | grep hcd

# Test connectivity from JanusGraph pod
kubectl exec -it janusgraph-0 -n janusgraph-banking -- \
  nc -zv hcd-cluster-global-paris-dc-service 9042

# Check JanusGraph logs
kubectl logs janusgraph-0 -n janusgraph-banking
```

### Mission Control Not Showing Clusters

```bash
# Check Mission Control server logs
kubectl logs -l app=mission-control-server -n janusgraph-banking

# Check Mission Control agent logs
kubectl logs -l app=mission-control-agent -n janusgraph-banking

# Verify cluster registration
curl http://localhost:8080/api/v1/clusters \
  -H "Authorization: Bearer $MC_TOKEN"
```

## Upgrading

### Upgrade Chart

```bash
# Update dependencies
helm dependency update

# Upgrade release
helm upgrade janusgraph-banking . \
  --namespace janusgraph-banking \
  --values values-prod.yaml \
  --wait \
  --timeout 30m
```

### Upgrade HCD Version

```bash
# Update HCD version in values.yaml
hcd:
  serverVersion: "1.2.4"  # New version
  serverImage: "datastax/hcd-server:1.2.4"

# Upgrade with rolling restart
helm upgrade janusgraph-banking . \
  --namespace janusgraph-banking \
  --values values-prod.yaml \
  --wait
```

## Uninstallation

```bash
# Uninstall release
helm uninstall janusgraph-banking -n janusgraph-banking

# Delete PVCs (WARNING: This deletes all data)
kubectl delete pvc -n janusgraph-banking --all

# Delete namespace
kubectl delete namespace janusgraph-banking
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/janusgraph-banking/issues
- Documentation: https://docs.example.com/janusgraph-banking
- IBM DataStax HCD Docs: https://docs.datastax.com/en/hyper-converged-database/
- Mission Control Docs: https://docs.datastax.com/en/mission-control/

## License

See [LICENSE](../../LICENSE) file.

## References

- [IBM DataStax HCD Documentation](https://docs.datastax.com/en/hyper-converged-database/1.2/)
- [DataStax Mission Control](https://docs.datastax.com/en/mission-control/)
- [Cass Operator](https://docs.datastax.com/en/cass-operator/)
- [JanusGraph Documentation](https://docs.janusgraph.org/)
- [Technical Specification](../../docs/implementation/k8s-openshift-deployment-technical-spec-2026-02-19.md)
- [HCD/Mission Control Addendum](../../docs/implementation/k8s-openshift-hcd-mission-control-addendum-2026-02-19.md)