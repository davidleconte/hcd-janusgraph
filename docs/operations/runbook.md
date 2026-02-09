# Operations Runbook

**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)  
**Contact:** 

## Common Operations

### Start Services

```bash
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh
```

### Stop Services

```bash
cd config/compose
bash ../../scripts/deployment/stop_full_stack.sh
```

### Check Status

```bash
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

## Troubleshooting

### JanusGraph Not Responding

```bash
# Check logs
podman logs janusgraph

# Restart
podman restart janusgraph
```

### OpenSearch Connection Issues

```bash
# Verify health
curl http://localhost:9200/_cluster/health?pretty

# Check logs
podman logs opensearch
```

### Pulsar Backlog Growing

```bash
# Check subscriptions
pulsar-admin topics stats persistent://public/default/entities

# Clear backlog (caution!)
pulsar-admin topics skip-all persistent://public/default/entities -s graph-consumer
```

## Backup Procedures

### JanusGraph/Cassandra

```bash
# Snapshot
nodetool snapshot janusgraph
```

### OpenSearch

```bash
# Create snapshot repository
curl -X PUT "localhost:9200/_snapshot/backup"
```

## Emergency Contacts

- **Author:** David Leconte
- **Phone:** 
