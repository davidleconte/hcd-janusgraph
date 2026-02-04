# Week 1: Security Hardening Implementation Guide

**Date:** 2026-01-28  
**Version:** 1.0  
**Status:** In Progress  
**Phase:** Production Readiness - Week 1

## Overview

This guide provides step-by-step instructions for implementing Week 1 security hardening, including SSL/TLS enablement and HashiCorp Vault integration.

## Prerequisites

- **Podman installed and running** (podman-machine: podman-wxd)
- **podman-compose installed** (pip install podman-compose)
- Project cloned and configured
- Basic understanding of TLS/SSL certificates
- Access to terminal/command line

## Implementation Steps

### Day 1: SSL/TLS Enablement

#### Step 1: Generate Certificates

```bash
# Navigate to project root
cd /path/to/hcd-tarball-janusgraph

# Generate all TLS certificates
./scripts/security/generate_certificates.sh
```

**Expected Output:**
```
🔐 TLS/SSL Certificate Generation
====================================

📁 Certificate directory: /path/to/config/certs
⏰ Validity: 365 days

1️⃣  Generating Root Certificate Authority (CA)...
✅ Root CA generated

2️⃣  Generating JanusGraph certificates...
✅ Certificate generated for janusgraph
☕ Creating Java keystore for janusgraph...
✅ Java keystore created for janusgraph

3️⃣  Generating HCD certificates...
✅ Certificate generated for hcd
☕ Creating Java keystore for hcd...
✅ Java keystore created for hcd

4️⃣  Generating OpenSearch certificates...
✅ Certificate generated for opensearch

5️⃣  Generating Grafana certificates...
✅ Certificate generated for grafana

6️⃣  Creating certificate bundle...

====================================
✅ Certificate Generation Complete
====================================
```

**Verification:**
```bash
# Check certificate directory structure
ls -la config/certs/

# Verify JanusGraph certificates
ls -la config/certs/janusgraph/

# Verify HCD certificates
ls -la config/certs/hcd/

# Test certificate validity
openssl x509 -in config/certs/janusgraph/janusgraph-cert.pem -text -noout
```

#### Step 2: Update Configuration Files

The following files have been updated to enable TLS by default:

1. **docker-compose.yml** - Main compose file with TLS enabled
2. **.env.example** - Environment variables with TLS settings
3. **config/janusgraph/janusgraph-hcd-tls.properties** - JanusGraph TLS config
4. **config/janusgraph/janusgraph-server-tls.yaml** - Server TLS config

**Create .env file:**
```bash
# Copy example to .env
cp .env.example .env

# Edit .env and update passwords
# IMPORTANT: Replace placeholder passwords with secure values
nano .env
```

#### Step 3: Test TLS Configuration

```bash
# Start services with TLS
podman-compose up -d

# Wait for services to start (2-3 minutes)
sleep 120

# Check service status
podman-compose ps

# Test HCD TLS connection
podman exec -it hcd-server nodetool status

# Test JanusGraph TLS connection
curl -k https://localhost:8182?gremlin=g.V().count()
```

**Expected Results:**
- All services should be in "Up" state
- HCD should show "UN" (Up/Normal) status
- JanusGraph should return a count (likely 0 for new installation)

#### Step 4: Verify TLS Connections

```bash
# Test TLS handshake for HCD
openssl s_client -connect localhost:7001 -showcerts

# Test TLS handshake for JanusGraph
openssl s_client -connect localhost:8182 -showcerts

# Check certificate details
podman exec janusgraph-server keytool -list \
  -keystore /etc/janusgraph/certs/janusgraph-server.keystore.jks \
  -storepass changeit
```

### Day 2-3: HashiCorp Vault Integration

#### Step 1: Start Vault Container

```bash
# Navigate to compose directory
cd config/compose

# Start Vault service
podman-compose -f docker-compose.full.yml up -d vault

# Check Vault status
podman logs vault-server

# Verify Vault is running
podman exec vault-server vault status
```

**Expected Output:**
```
Key                Value
---                -----
Seal Type          shamir
Initialized        false
Sealed             true
Total Shares       0
Threshold          0
Unseal Progress    0/0
Unseal Nonce       n/a
Version            1.15.x
Storage Type       file
HA Enabled         false
```

#### Step 2: Initialize Vault

```bash
# Run initialization script
cd ../..
./scripts/security/init_vault.sh
```

**Expected Output:**
```
🔐 HashiCorp Vault Initialization
====================================

✅ Vault container is running

⏳ Waiting for Vault to be ready...

1️⃣  Initializing Vault...
✅ Vault initialized
⚠️  Keys saved to: /path/to/.vault-keys

2️⃣  Unsealing Vault...
✅ Vault unsealed

3️⃣  Enabling KV secrets engine...
✅ KV secrets engine enabled at: janusgraph/

4️⃣  Creating initial secrets...
✅ Initial secrets created

5️⃣  Creating access policy...
✅ Policy created: janusgraph-policy

6️⃣  Creating application token...
✅ Application token created

====================================
✅ Vault Setup Complete
====================================
```

**CRITICAL:** Save the output! The script creates `.vault-keys` file with:
- 5 unseal keys (need 3 to unseal)
- Root token (full admin access)
- Application token (read-only access)

#### Step 3: Verify Vault Setup

```bash
# Source Vault environment
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=<your-app-token-from-vault-keys>

# Test Vault access
podman exec -e VAULT_TOKEN=$VAULT_TOKEN vault-server vault status

# List secrets
podman exec -e VAULT_TOKEN=$VAULT_TOKEN vault-server vault kv list janusgraph/

# Read a secret
podman exec -e VAULT_TOKEN=$VAULT_TOKEN vault-server vault kv get janusgraph/admin
```

**Expected Output:**
```
====== Secret Path ======
janusgraph/data/admin

======= Metadata =======
Key                Value
---                -----
created_time       2026-01-28T23:00:00.000Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1

====== Data ======
Key         Value
---         -----
password    <generated-password>
username    admin
```

#### Step 4: Test Secrets Manager Integration

```bash
# Install hvac library
pip install hvac==2.1.0

# Test Python integration
python3 << 'EOF'
from scripts.utils.secrets_manager import SecretsManager
import os

# Set Vault environment
os.environ['VAULT_ADDR'] = 'http://localhost:8200'
os.environ['VAULT_TOKEN'] = '<your-app-token>'

# Initialize secrets manager with Vault backend
sm = SecretsManager(backend='vault')

# Retrieve secrets
admin_user = sm.get_secret('janusgraph/admin:username')
admin_pass = sm.get_secret('janusgraph/admin:password')

print(f"Username: {admin_user}")
print(f"Password: {admin_pass[:4]}..." if admin_pass else "None")
EOF
```

#### Step 5: Access Vault UI

```bash
# Open Vault UI in browser
open http://localhost:8200/ui

# Login with root token from .vault-keys file
# Navigate to: Secrets > janusgraph
# View stored secrets
```

### Day 4-5: Testing and Validation

#### Comprehensive Testing Checklist

**1. TLS Certificate Validation**
```bash
# Test certificate chain
openssl verify -CAfile config/certs/ca/ca-cert.pem \
  config/certs/janusgraph/janusgraph-cert.pem

# Test certificate expiration
openssl x509 -in config/certs/janusgraph/janusgraph-cert.pem \
  -noout -dates

# Test keystore integrity
keytool -list -v \
  -keystore config/certs/janusgraph/janusgraph-server.keystore.jks \
  -storepass changeit
```

**2. Service Connectivity**
```bash
# Test HCD CQL with TLS
podman exec -it hcd-server cqlsh \
  --ssl \
  -u cassandra \
  -p <password-from-vault>

# Test JanusGraph Gremlin with TLS
podman exec -it janusgraph-server \
  /opt/janusgraph/bin/gremlin.sh << 'GREMLIN'
:remote connect tinkerpop.server conf/remote-secure.yaml
:remote console
g.V().count()
GREMLIN
```

**3. Vault Operations**
```bash
# Test secret creation
podman exec -e VAULT_TOKEN=$VAULT_TOKEN vault-server \
  vault kv put janusgraph/test key=value

# Test secret retrieval
podman exec -e VAULT_TOKEN=$VAULT_TOKEN vault-server \
  vault kv get janusgraph/test

# Test secret deletion
podman exec -e VAULT_TOKEN=$VAULT_TOKEN vault-server \
  vault kv delete janusgraph/test
```

**4. Integration Testing**
```bash
# Run integration tests
cd banking/data_generators/tests
./run_tests.sh integration

# Test data loading with TLS
python3 << 'EOF'
from src.python.client.janusgraph_client import JanusGraphClient

client = JanusGraphClient(
    host='localhost',
    port=8182,
    ssl_enabled=True,
    ca_certs='config/certs/ca/ca-cert.pem'
)

# Test connection
result = client.execute("g.V().count()")
print(f"Vertex count: {result}")
EOF
```

**5. Performance Testing**
```bash
# Test TLS overhead
time curl -k https://localhost:8182?gremlin=g.V().count()

# Compare with non-TLS (if available)
# Expected: <100ms additional latency for TLS handshake
```

#### Troubleshooting

**Issue: Vault container won't start**
```bash
# Check logs
podman logs vault-server

# Common fixes:
# 1. Remove old data
podman volume rm hcd-janusgraph_vault-data

# 2. Check port availability
lsof -i :8200

# 3. Restart container
podman-compose -f config/compose/docker-compose.full.yml restart vault
```

**Issue: TLS handshake failures**
```bash
# Check certificate validity
openssl x509 -in config/certs/janusgraph/janusgraph-cert.pem -text -noout

# Verify certificate chain
openssl verify -CAfile config/certs/ca/ca-cert.pem \
  config/certs/janusgraph/janusgraph-cert.pem

# Check keystore password
keytool -list -keystore config/certs/janusgraph/janusgraph-server.keystore.jks \
  -storepass changeit
```

**Issue: Cannot retrieve secrets from Vault**
```bash
# Check Vault status
podman exec vault-server vault status

# Verify token
podman exec -e VAULT_TOKEN=$VAULT_TOKEN vault-server \
  vault token lookup

# Check policy
podman exec -e VAULT_TOKEN=$VAULT_TOKEN vault-server \
  vault policy read janusgraph-policy
```

## Security Best Practices

### Certificate Management

1. **Rotation Schedule:**
   - Certificates expire in 365 days
   - Plan rotation 30 days before expiration
   - Test rotation in staging first

2. **Storage:**
   - Keep CA private key (`ca-key.pem`) in secure location
   - Never commit certificates to version control
   - Backup certificates encrypted

3. **Access Control:**
   - Limit access to certificate directories (chmod 700)
   - Private keys should be 600 permissions
   - Use different certificates per environment

### Vault Security

1. **Unseal Keys:**
   - Distribute 5 keys to different trusted individuals
   - Store in separate secure locations
   - Never store all keys together
   - Consider using Vault auto-unseal with cloud KMS

2. **Root Token:**
   - Rotate immediately after initial setup
   - Use for emergency access only
   - Revoke after creating admin users
   - Never use in application code

3. **Application Tokens:**
   - Use short TTL (720h = 30 days)
   - Enable token renewal
   - Implement token rotation
   - Use AppRole for production

4. **Audit Logging:**
   - Enable Vault audit logs
   - Monitor access patterns
   - Alert on suspicious activity
   - Retain logs for compliance

## Validation Checklist

- [ ] All certificates generated successfully
- [ ] TLS enabled on HCD (port 9142)
- [ ] TLS enabled on JanusGraph (port 8182)
- [ ] Vault container running and initialized
- [ ] Vault unsealed with 3 keys
- [ ] KV secrets engine enabled
- [ ] Initial secrets created
- [ ] Application token generated
- [ ] Secrets retrievable via Python
- [ ] Integration tests passing
- [ ] No hardcoded credentials in code
- [ ] .vault-keys file secured
- [ ] .gitignore updated
- [ ] Documentation updated

## Rollback Procedure

If issues occur, rollback to non-TLS configuration:

```bash
# Stop services
podman-compose down

# Revert docker-compose.yml changes
git checkout docker-compose.yml

# Start with original configuration
podman-compose up -d

# Verify services
podman-compose ps
```

## Next Steps

After completing Week 1:

1. **Week 2:** Enhance monitoring with AlertManager
2. **Week 3-4:** Achieve 80% test coverage
3. **Week 5:** Test disaster recovery procedures
4. **Week 6:** Complete compliance documentation

## Support and Resources

- **Vault Documentation:** https://www.vaultproject.io/docs
- **TLS Best Practices:** https://ssl-config.mozilla.org/
- **JanusGraph Security:** https://docs.janusgraph.org/security/
- **Project Issues:** GitHub Issues

## Appendix

### A. File Changes Summary

**Modified Files:**
- `docker-compose.yml` - TLS enabled by default
- `.env.example` - TLS environment variables
- `.gitignore` - Vault keys excluded
- `requirements.txt` - hvac library added

**Created Files:**
- `config/vault/config.hcl` - Vault configuration
- `scripts/security/init_vault.sh` - Vault initialization
- `config/certs/*` - TLS certificates (generated)
- `.vault-keys` - Vault unseal keys (generated, not in git)

### B. Environment Variables

```bash
# TLS Configuration
JANUSGRAPH_USE_SSL=true
JANUSGRAPH_KEYSTORE_PASSWORD=changeit
JANUSGRAPH_TRUSTSTORE_PASSWORD=changeit
HCD_KEYSTORE_PASSWORD=changeit
HCD_TRUSTSTORE_PASSWORD=changeit

# Vault Configuration
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=<your-app-token>
```

### C. Port Reference

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| HCD | 9042 | CQL | Non-TLS (backward compat) |
| HCD | 9142 | CQL+TLS | Encrypted CQL |
| HCD | 7001 | TLS | Inter-node encryption |
| JanusGraph | 8182 | HTTPS | Gremlin WebSocket with TLS |
| Vault | 8200 | HTTP | Vault API (internal network) |

---

**Document Owner:** Security Team  
**Last Updated:** 2026-01-28  
**Next Review:** Weekly during implementation