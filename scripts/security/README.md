# Security Scripts - HCD + JanusGraph Banking Platform

This directory contains security automation scripts for credential rotation, certificate management, and Vault integration.

---

## Quick Start

### 1. Initial Setup

```bash
# Generate SSL/TLS certificates
./generate_certificates.sh

# Initialize Vault
./init_vault.sh

# Migrate credentials to Vault
python migrate_credentials_to_vault.py

# Setup Vault policies
./setup_vault_policies.sh
```

### 2. Credential Rotation

```bash
# Manual rotation (single service)
python credential_rotation_framework.py rotate --service janusgraph

# Manual rotation (all services)
python credential_rotation_framework.py rotate --service all

# Verify service health
python credential_rotation_framework.py verify --service opensearch
```

### 3. Automated Rotation

```bash
# Install systemd timer (requires root)
cd rotation-scheduling
sudo ./setup_rotation_scheduling.sh

# Check timer status
sudo systemctl status credential-rotation.timer

# View rotation logs
sudo journalctl -u credential-rotation.service -f
```

---

## Scripts Overview

### Core Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `generate_certificates.sh` | Generate SSL/TLS certificates | `./generate_certificates.sh` |
| `init_vault.sh` | Initialize HashiCorp Vault | `./init_vault.sh` |
| `migrate_credentials_to_vault.py` | Migrate credentials to Vault | `python migrate_credentials_to_vault.py` |
| `setup_vault_policies.sh` | Configure Vault access policies | `./setup_vault_policies.sh` |
| `vault_access.sh` | Source for Vault environment variables | `source ./vault_access.sh` |
| `fix_vault_policy.sh` | Fix Vault policy issues | `./fix_vault_policy.sh` |

### Credential Rotation

| Script | Purpose | Usage |
|--------|---------|-------|
| `credential_rotation_framework.py` | Main rotation framework | `python credential_rotation_framework.py rotate --service all` |
| `rotation-scheduling/credential-rotation.service` | Systemd service unit | Installed by setup script |
| `rotation-scheduling/credential-rotation.timer` | Systemd timer unit | Installed by setup script |
| `rotation-scheduling/setup_rotation_scheduling.sh` | Install rotation scheduling | `sudo ./setup_rotation_scheduling.sh` |

---

## Credential Rotation Framework

### Features

- ✅ **Zero-downtime rotation** - Services remain available
- ✅ **Vault integration** - Secure credential storage
- ✅ **Health checks** - Pre/post-rotation validation
- ✅ **Automatic rollback** - Reverts on failure
- ✅ **Audit logging** - All rotations logged

### Supported Services

1. **JanusGraph/HCD** - Database passwords
2. **OpenSearch** - Admin passwords
3. **Grafana** - Admin passwords
4. **Pulsar** - Authentication tokens
5. **SSL/TLS Certificates** - Certificate rotation

### Rotation Schedule

- **Frequency:** Monthly (1st day of month at 2 AM)
- **Randomization:** Up to 1 hour delay
- **Persistence:** Runs if system was down

### Manual Rotation

```bash
# Rotate single service
python credential_rotation_framework.py rotate --service janusgraph \
  --vault-addr http://localhost:8200 \
  --vault-token $VAULT_APP_TOKEN

# Rotate all services
python credential_rotation_framework.py rotate --service all

# Verify service health
python credential_rotation_framework.py verify --service opensearch

# Check rotation status
python credential_rotation_framework.py status
```

### Automated Rotation

```bash
# Install systemd timer
cd rotation-scheduling
sudo ./setup_rotation_scheduling.sh

# Enable timer
sudo systemctl enable credential-rotation.timer
sudo systemctl start credential-rotation.timer

# Check next run
sudo systemctl list-timers credential-rotation.timer

# View logs
sudo journalctl -u credential-rotation.service -f

# Disable timer
sudo systemctl disable credential-rotation.timer
sudo systemctl stop credential-rotation.timer
```

---

## Vault Integration

### Vault Agent

Vault agent automatically injects credentials into containers:

```bash
# Deploy with Vault agent
cd config/compose
podman-compose -f docker-compose.full.yml -f docker-compose.vault-agent.yml up -d

# Check Vault agent logs
podman logs janusgraph-demo_vault-agent-janusgraph_1

# Verify credential injection
podman exec janusgraph-demo_janusgraph_1 cat /vault/secrets/janusgraph-credentials.properties
```

### Vault Templates

Templates render credentials from Vault:

- `config/vault/templates/janusgraph-credentials.tpl`
- `config/vault/templates/opensearch-credentials.tpl`
- `config/vault/templates/grafana-credentials.tpl`
- `config/vault/templates/pulsar-credentials.tpl`

### Vault Policies

Access policies control who can read/write secrets:

- `config/vault/policies/admin-policy.hcl` - Full access
- `config/vault/policies/janusgraph-api-policy.hcl` - API access
- `config/vault/policies/monitoring-policy.hcl` - Monitoring access

---

## Certificate Management

### Generate Certificates

```bash
# Generate all certificates
./generate_certificates.sh

# Certificates created in config/security/certs/
# - ca.pem (CA certificate)
# - server.pem (Server certificate)
# - server-key.pem (Server private key)
# - client.pem (Client certificate)
# - client-key.pem (Client private key)
```

### Certificate Rotation

```bash
# Rotate certificates
python credential_rotation_framework.py rotate --service certificates

# Certificates backed up to config/security/certs/backup_<timestamp>/
# Services automatically restarted with new certificates
```

### Certificate Expiry

Certificates are valid for 1 year. Monitor expiry:

```bash
# Check certificate expiry
openssl x509 -in config/security/certs/server.pem -noout -enddate

# Alert if expiring soon (< 30 days)
# (Automated via Prometheus alert rules)
```

---

## Troubleshooting

### Rotation Failures

**Issue:** Credential rotation fails

```bash
# Check Vault connectivity
curl http://localhost:8200/v1/sys/health

# Check service health
python credential_rotation_framework.py verify --service janusgraph

# Check rotation logs
tail -f /var/log/credential-rotation.log

# Manual rollback
vault kv get janusgraph/admin_backup_<timestamp>
```

**Issue:** Service won't start after rotation

```bash
# Check service logs
podman logs janusgraph-demo_janusgraph_1

# Verify credentials in Vault
vault kv get janusgraph/admin

# Restart service
podman-compose restart janusgraph
```

### Vault Issues

**Issue:** Vault sealed

```bash
# Check Vault status
vault status

# Unseal Vault
vault operator unseal

# Initialize if needed
./init_vault.sh
```

**Issue:** Vault authentication failed

```bash
# Check token
echo $VAULT_APP_TOKEN

# Re-authenticate
source ./vault_access.sh

# Verify authentication
vault token lookup
```

### Certificate Issues

**Issue:** Certificate validation failed

```bash
# Verify certificate
openssl verify -CAfile config/security/certs/ca.pem config/security/certs/server.pem

# Check certificate details
openssl x509 -in config/security/certs/server.pem -text -noout

# Regenerate if needed
./generate_certificates.sh
```

---

## Security Best Practices

### Credential Management

1. **Never commit credentials** - Use Vault for all secrets
2. **Rotate regularly** - Monthly minimum, weekly recommended
3. **Use strong passwords** - 32+ characters, high entropy
4. **Audit access** - Review Vault audit logs regularly
5. **Limit access** - Use least privilege principle

### Certificate Management

1. **Use strong keys** - 2048-bit RSA minimum, 4096-bit recommended
2. **Rotate annually** - Before expiry
3. **Monitor expiry** - Alert 30 days before expiry
4. **Secure private keys** - Restrict file permissions (600)
5. **Use CA certificates** - Don't use self-signed in production

### Vault Security

1. **Seal Vault** - When not in use
2. **Backup unseal keys** - Store securely offline
3. **Enable audit logging** - Track all Vault access
4. **Use AppRole** - For service authentication
5. **Rotate tokens** - Regularly rotate Vault tokens

---

## Monitoring

### Prometheus Metrics

```python
# Credential rotation metrics
credential_rotation_total{service="janusgraph",result="success"}
credential_rotation_duration_seconds{service="janusgraph"}
credential_rotation_last_success_timestamp{service="janusgraph"}

# Certificate metrics
certificate_expiry_days{service="janusgraph"}
certificate_rotation_total{result="success"}
```

### Grafana Dashboard

View security metrics in Grafana:

- **URL:** http://localhost:3001
- **Dashboard:** Security Monitoring
- **Panels:**
  - Credential rotation status
  - Certificate expiry
  - Vault access logs
  - Security events

### Alert Rules

```yaml
# Rotation failure
- alert: CredentialRotationFailed
  expr: credential_rotation_total{result="failed"} > 0
  severity: critical

# Rotation overdue
- alert: CredentialRotationOverdue
  expr: time() - credential_rotation_last_success_timestamp > 2678400
  severity: warning

# Certificate expiring
- alert: CertificateExpiringSoon
  expr: certificate_expiry_days < 30
  severity: warning
```

---

## References

### Documentation

- [Phase 2 Security Hardening Complete](../../docs/implementation/PHASE2_SECURITY_HARDENING_COMPLETE.md)
- [Security Remediation Plan](../../SECURITY_REMEDIATION_PLAN_2026-02-11.md)
- [Vault Configuration](../../config/vault/)

### External Resources

- [HashiCorp Vault](https://www.vaultproject.io/)
- [OWASP Security Guidelines](https://owasp.org/)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)

---

**Last Updated:** 2026-02-11  
**Version:** 1.0  
**Status:** Production Ready