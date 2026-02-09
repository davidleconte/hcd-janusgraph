# Week 1 Implementation Troubleshooting Guide

**Date:** 2026-01-28
**Version:** 1.0
**Status:** Active

## Common Issues and Solutions

### Issue 1: Container Name Already in Use

**Error:**

```
Error: creating container storage: the container name "hcd-server" is already in use
```

**Cause:** Previous containers still exist from earlier runs.

**Solution:**

```bash
# Stop all running containers
podman-compose down

# Remove all containers (including stopped ones)
podman ps -a | grep hcd-janusgraph | awk '{print $1}' | xargs podman rm -f

# Remove the pod if it exists
podman pod rm -f hcd-janusgraph_default 2>/dev/null || true

# Clean up volumes (CAUTION: This deletes data)
podman volume prune -f

# Start fresh
podman-compose up -d
```

### Issue 2: Vault Permission Denied

**Error:**

```
failed to persist keyring: mkdir /vault/data/core: permission denied
```

**Cause:** Podman runs rootless and Vault needs write permissions to /vault/data.

**Solution Applied:**
The docker-compose.full.yml has been updated with:

- `user: "0:0"` - Run Vault as root
- `:Z` suffix on volumes - SELinux context for Podman
- `SKIP_SETCAP=true` - Skip capability setting

**If issue persists:**

```bash
# Stop Vault
podman stop vault-server
podman rm vault-server

# Remove and recreate volume with proper permissions
podman volume rm hcd-janusgraph_vault-data
podman volume create hcd-janusgraph_vault-data

# Restart Vault
cd config/compose
podman-compose -f docker-compose.full.yml up -d vault

# Check logs
podman logs vault-server
```

### Issue 3: Certificate Bundle Creation Failed

**Error:**

```
cat: /path/to/config/certs/*/*-cert.pem: No such file or directory
```

**Cause:** Incorrect glob pattern in certificate generation script.

**Solution Applied:**
Script updated to use correct pattern and ignore errors:

```bash
cat "$CERT_DIR"/*/*.pem > "$CERT_DIR/all-certs-bundle.pem" 2>/dev/null || true
```

**Manual fix if needed:**

```bash
# Create bundle manually
cd config/certs
cat janusgraph/janusgraph-cert.pem \
    hcd/hcd-cert.pem \
    opensearch/opensearch-cert.pem \
    grafana/grafana-cert.pem \
    > all-certs-bundle.pem
```

### Issue 4: Podman-Compose Not Found

**Error:**

```
command not found: podman-compose
```

**Solution:**

```bash
# Install podman-compose
pip3 install podman-compose

# Verify installation
podman-compose --version

# Alternative: Use podman directly with compose files
podman play kube docker-compose.yml
```

### Issue 5: Port Already in Use

**Error:**

```
Error: cannot listen on the TCP port: listen tcp :8200: bind: address already in use
```

**Solution:**

```bash
# Find process using the port
lsof -i :8200

# Kill the process (replace PID)
kill -9 <PID>

# Or use a different port in docker-compose.full.yml
# Change: "8200:8200" to "8201:8200"
```

### Issue 6: TLS Handshake Failures

**Error:**

```
SSL routines:ssl3_get_record:wrong version number
```

**Cause:** Trying to connect with HTTPS to HTTP endpoint or vice versa.

**Solution:**

```bash
# Check if service is actually using TLS
podman logs janusgraph-server | grep -i tls
podman logs hcd-server | grep -i ssl

# Test with correct protocol
curl -k https://localhost:8182  # For TLS
curl http://localhost:8182      # For non-TLS

# Verify certificate configuration
podman exec janusgraph-server ls -la /etc/janusgraph/certs/
```

### Issue 7: Vault Unsealing Fails

**Error:**

```
Error unsealing: Error making API request
```

**Solution:**

```bash
# Check Vault status
podman exec vault-server vault status

# If sealed, unseal with keys from .vault-keys
export VAULT_UNSEAL_KEY_1=<key-from-file>
export VAULT_UNSEAL_KEY_2=<key-from-file>
export VAULT_UNSEAL_KEY_3=<key-from-file>

podman exec vault-server vault operator unseal $VAULT_UNSEAL_KEY_1
podman exec vault-server vault operator unseal $VAULT_UNSEAL_KEY_2
podman exec vault-server vault operator unseal $VAULT_UNSEAL_KEY_3

# Verify unsealed
podman exec vault-server vault status
```

### Issue 8: Cannot Connect to Services

**Error:**

```
curl: (7) Failed to connect to localhost port 8182: Connection refused
```

**Solution:**

```bash
# Check if containers are running
podman-compose ps

# Check container logs
podman logs janusgraph-server
podman logs hcd-server
podman logs vault-server

# Check if ports are exposed
podman port janusgraph-server
podman port vault-server

# Test from inside container
podman exec janusgraph-server curl -k https://localhost:8182
```

### Issue 9: Keystore Password Incorrect

**Error:**

```
keytool error: java.io.IOException: Keystore was tampered with, or password was incorrect
```

**Solution:**

```bash
# Check password in .env file
cat .env | grep KEYSTORE_PASSWORD

# Default password is 'changeit'
# Verify keystore with correct password
keytool -list \
  -keystore config/certs/janusgraph/janusgraph-server.keystore.jks \
  -storepass changeit

# If password is wrong, regenerate certificates
./scripts/security/generate_certificates.sh
```

### Issue 10: SELinux Denials (Linux only)

**Error:**

```
Permission denied (SELinux)
```

**Solution:**

```bash
# Check SELinux status
getenforce

# Temporarily set to permissive (for testing)
sudo setenforce 0

# Or add :Z to all volume mounts in docker-compose files
# Example: - vault-data:/vault/data:Z

# Check audit logs
sudo ausearch -m avc -ts recent
```

## Complete Cleanup and Restart

If all else fails, perform a complete cleanup:

```bash
# 1. Stop everything
podman-compose down
cd config/compose
podman-compose -f docker-compose.full.yml down

# 2. Remove all containers
podman ps -a | grep hcd-janusgraph | awk '{print $1}' | xargs podman rm -f

# 3. Remove pods
podman pod ls | grep hcd-janusgraph | awk '{print $1}' | xargs podman pod rm -f

# 4. Remove volumes (CAUTION: Deletes all data)
podman volume ls | grep hcd-janusgraph | awk '{print $2}' | xargs podman volume rm -f

# 5. Remove networks
podman network ls | grep hcd-janusgraph | awk '{print $1}' | xargs podman network rm

# 6. Clean up certificates
rm -rf config/certs/*

# 7. Start fresh
cd /path/to/project
./scripts/security/generate_certificates.sh
podman-compose up -d
cd config/compose
podman-compose -f docker-compose.full.yml up -d vault
cd ../..
./scripts/security/init_vault.sh
```

## Verification Commands

After fixing issues, verify everything works:

```bash
# 1. Check all containers are running
podman-compose ps
podman ps | grep vault

# 2. Check Vault status
podman exec vault-server vault status

# 3. Test TLS connections
curl -k https://localhost:8182?gremlin=g.V().count()

# 4. Test Vault access
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=<your-token>
podman exec -e VAULT_TOKEN=$VAULT_TOKEN vault-server vault kv list janusgraph/

# 5. Check logs for errors
podman logs janusgraph-server | tail -50
podman logs hcd-server | tail -50
podman logs vault-server | tail -50
```

## Getting Help

If issues persist:

1. **Check logs:** `podman logs <container-name>`
2. **Check container status:** `podman inspect <container-name>`
3. **Check network:** `podman network inspect hcd-janusgraph-network`
4. **Check volumes:** `podman volume inspect <volume-name>`
5. **Review documentation:** See WEEK1_SECURITY_IMPLEMENTATION.md

## Known Limitations

1. **Podman on macOS:** May have different behavior than Linux
2. **SELinux:** Required on RHEL/CentOS, use :Z suffix on volumes
3. **Rootless Podman:** Some operations require root privileges
4. **Certificate expiration:** Certificates expire in 365 days

---

**Document Owner:** DevOps Team
**Last Updated:** 2026-01-28
**Next Review:** As issues arise
