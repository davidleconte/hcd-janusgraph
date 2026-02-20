# Production Secure Overrides

This repository keeps demo defaults for deterministic local execution.  
Use secure overrides for production-like deployments.

## Podman Compose

Run from `config/compose`:

```bash
export OPENSEARCH_INITIAL_ADMIN_PASSWORD="<strong-secret>"
export GRAFANA_ADMIN_USER="<admin-user>"
export GRAFANA_ADMIN_PASSWORD="<strong-secret>"
export API_JWT_SECRET="<strong-secret>"
export API_USER_PASSWORD="<strong-secret>"

podman-compose -p janusgraph-demo \
  -f docker-compose.full.yml \
  -f docker-compose.prod-secure.override.yml \
  up -d
```

## Helm

```bash
helm upgrade --install janusgraph-banking ./helm/janusgraph-banking \
  -f helm/janusgraph-banking/values.yaml \
  -f helm/janusgraph-banking/values.prod-secure.yaml
```

## Security Effects

- Enables API authentication in deployment profile (`AUTH_ENABLED=true`)
- Removes weak Grafana password fallback
- Enables OpenSearch security plugin for production profile
- Leaves deterministic local profile unchanged
