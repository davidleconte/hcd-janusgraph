# Production Hardening Guide

**Date:** 2026-02-04
**Status:** Active
**Author:** David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

## Overview

This guide covers production hardening for the JanusGraph/HCD banking analytics platform.

## 1. OpenSearch Security (TLS + Authentication)

### Enable Security

```bash
# 1. Generate certificates
./scripts/security/generate_opensearch_certs.sh

# 2. Update compose configuration with security enabled
# In the full-stack compose file, change:
#   - plugins.security.disabled=true
# To:
#   - plugins.security.disabled=false
#   - plugins.security.ssl.http.enabled=true
#   - plugins.security.ssl.transport.enabled=true

# 3. Mount certificates
# volumes:
#   - ./certs/opensearch:/usr/share/opensearch/config/certs:ro
```

### Required Environment Variables

```bash
# .env.production
OPENSEARCH_INITIAL_ADMIN_PASSWORD=<strong-password-here>
OPENSEARCH_SSL_ENABLED=true
```

## 2. Vault Production Mode

### Auto-Unseal Configuration

For production, use cloud-based auto-unseal:

**AWS KMS:**

```hcl
seal "awskms" {
  region     = "us-west-2"
  kms_key_id = "your-kms-key-id"
}
```

**Azure Key Vault:**

```hcl
seal "azurekeyvault" {
  tenant_id      = "your-tenant-id"
  vault_name     = "your-vault-name"
  key_name       = "vault-unseal-key"
}
```

### High Availability Setup

1. Deploy 3+ Vault nodes
2. Use Raft storage backend
3. Configure load balancer for `vault.example.com`

```bash
# Initialize HA cluster
vault operator raft join https://vault-node-1:8200
```

## 3. JanusGraph Security

### Enable Authentication

```properties
# janusgraph.properties
gremlin.tinkergraph.graphProperties=authenticator
gremlin.remote.remoteConnectionClass=org.apache.tinkerpop.gremlin.driver.remote.DriverRemoteConnection
```

### Network Isolation

- JanusGraph should NOT be exposed outside the internal network
- Use Analytics API as the only external interface
- Configure firewall rules:

```bash
# Only allow internal network access to Gremlin port
iptables -A INPUT -p tcp --dport 8182 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 8182 -j DROP
```

## 4. Analytics API Security

### Production Settings

```python
# src/python/api/main.py - Production changes

# 1. Restrict CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# 2. Add rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

# 3. Enable HTTPS only
# Run behind reverse proxy (nginx/traefik) with TLS termination
```

### API Authentication

```bash
# Add JWT authentication
pip install python-jose[cryptography]
```

## 5. HCD/Cassandra Hardening

### Authentication

```yaml
# cassandra.yaml
authenticator: PasswordAuthenticator
authorizer: CassandraAuthorizer
```

### Network Security

- Enable client-to-node encryption
- Enable node-to-node encryption
- Rotate certificates quarterly

## 6. Monitoring & Alerting

### Security-Related Alerts

Add to `alertmanager.yml`:

```yaml
route:
  routes:
    - match:
        severity: security
      receiver: security-team

receivers:
  - name: security-team
    pagerduty_configs:
      - service_key: <pagerduty-key>
```

### Audit Log Collection

```bash
# Ship audit logs to SIEM
./scripts/security/configure_audit_shipping.sh
```

## 7. Compliance Checklist

- [ ] All passwords changed from defaults
- [ ] TLS enabled on all services
- [ ] Network segmentation implemented
- [ ] Audit logging enabled
- [ ] Backup encryption enabled
- [ ] Access control policies configured
- [ ] Security scanning scheduled
- [ ] Incident response plan documented

## 8. Quick Start - Production Deployment

```bash
# 1. Generate all certificates
./scripts/security/generate_all_certs.sh

# 2. Create production environment file
cp .env.example .env.production
# Edit .env.production with secure values

# 3. Deploy with production config
ENV_FILE=.env.production ./scripts/deployment/deploy_full_stack.sh

# 4. Initialize Vault with auto-unseal
./scripts/security/init_vault_production.sh

# 5. Run security validation
./scripts/validation/security_check.sh
```

## References

- [OpenSearch Security Plugin](https://opensearch.org/docs/latest/security-plugin/)
- [Vault Production Hardening](https://developer.hashicorp.com/vault/docs/concepts/production-hardening)
- [CassandraSSL Configuration](https://cassandra.apache.org/doc/latest/operating/security.html)
