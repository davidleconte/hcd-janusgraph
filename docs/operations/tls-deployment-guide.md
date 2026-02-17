# TLS/SSL Deployment Guide

**Created**: 2026-01-28
**Author**: Security Audit Team
**Version**: 1.0
**Status**: Production Ready

## Overview

This guide provides step-by-step instructions for deploying the HCD + JanusGraph stack with TLS/SSL encryption enabled on all services.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Certificate Generation](#certificate-generation)
3. [Configuration](#configuration)
4. [Deployment](#deployment)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Security Best Practices](#security-best-practices)

---

## Prerequisites

### Required Tools

- Docker or Podman
- OpenSSL 1.1.1+
- Java keytool (JDK 11+)
- Bash 4.0+

### Environment Setup

1. **Copy environment template**:

   ```bash
   cp .env.example .env
   chmod 600 .env
   ```

2. **Set TLS passwords** in `.env`:

   ```bash
   # Generate strong passwords
   openssl rand -base64 32

   # Update .env with generated passwords
   HCD_KEYSTORE_PASSWORD=<generated-password>
   HCD_TRUSTSTORE_PASSWORD=<generated-password>
   JANUSGRAPH_KEYSTORE_PASSWORD=<generated-password>
   JANUSGRAPH_TRUSTSTORE_PASSWORD=<generated-password>
   ```

3. **Configure certificate details** in `.env`:

   ```bash
   TLS_COUNTRY=US
   TLS_STATE=California
   TLS_CITY=San Francisco
   TLS_ORGANIZATION=YourOrganization
   TLS_ORGANIZATIONAL_UNIT=IT
   TLS_COMMON_NAME=localhost
   TLS_VALIDITY_DAYS=365
   ```

---

## Certificate Generation

### Step 1: Generate All Certificates

Run the automated certificate generation script:

```bash
./scripts/security/generate_certificates.sh
```

This script will:

- Create a Root CA certificate
- Generate service certificates for:
  - HCD (Cassandra)
  - JanusGraph
  - Grafana
  - Prometheus
  - OpenSearch
- Create Java keystores and truststores
- Set appropriate permissions

### Step 2: Verify Certificate Generation

Check that all certificates were created:

```bash
ls -la config/certs/

# Expected output:
# ca.key, ca.crt                    # Root CA
# hcd-server.key, hcd-server.crt    # HCD certificates
# janusgraph-server.key, .crt       # JanusGraph certificates
# *.keystore.jks, *.truststore.jks  # Java keystores
# grafana.key, grafana.crt          # Grafana certificates
# prometheus.key, prometheus.crt    # Prometheus certificates
```

### Step 3: Verify Certificate Details

```bash
# Check Root CA
openssl x509 -in config/certs/ca.crt -text -noout

# Check HCD certificate
openssl x509 -in config/certs/hcd-server.crt -text -noout

# Check JanusGraph certificate
openssl x509 -in config/certs/janusgraph-server.crt -text -noout

# Verify keystore contents
keytool -list -v -keystore config/certs/hcd-server.keystore.jks \
  -storepass "${HCD_KEYSTORE_PASSWORD}"
```

---

## Configuration

### HCD (Cassandra) TLS Configuration

The TLS configuration is in `config/janusgraph/cassandra-tls.yaml`:

**Key Settings**:

- Client-to-node encryption: **enabled**
- Node-to-node encryption: **all**
- TLS protocol: **TLSv1.2**
- Client authentication: **optional**

**Ports**:

- Standard CQL: `9042` (disabled in TLS mode)
- TLS CQL: `9142` (enabled)
- Inter-node: `7000` (disabled in TLS mode)
- TLS inter-node: `7001` (enabled)

### JanusGraph TLS Configuration

The TLS configuration is in `config/janusgraph/janusgraph-server-tls.yaml`:

**Key Settings**:

- WebSocket TLS: **enabled**
- TLS protocol: **TLSv1.2**
- Client authentication: **optional**
- Keystore/Truststore: **JKS format**

**Backend Connection**:

- Uses TLS to connect to HCD on port `9142`
- Configuration in `config/janusgraph/janusgraph-hcd-tls.properties`

### Monitoring Stack TLS Configuration

**Grafana**:

- HTTPS enabled on port `3443`
- Certificate: `config/certs/grafana.crt`
- Key: `config/certs/grafana.key`

**Prometheus**:

- HTTPS enabled on port `9443`
- Web config: `config/monitoring/prometheus-web-config.yml`
- Certificate: `config/certs/prometheus.crt`

---

## Deployment

### Option 1: Deploy with TLS (Recommended)

Deploy the full stack with TLS encryption:

```bash
# Generate certificates first
./scripts/security/generate_certificates.sh

# Deploy with TLS overlay
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo -f docker-compose.yml -f docker-compose.tls.yml up -d

# Or with Podman
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo -f docker-compose.yml -f docker-compose.tls.yml up -d
```

### Option 2: Deploy Without TLS (Development Only)

For development/testing without TLS:

```bash
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo up -d
```

**⚠️ WARNING**: Never use non-TLS deployment in production!

### Deployment with Full Stack

Deploy with monitoring and logging:

```bash
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo \
  -f docker-compose.yml \
  -f docker-compose.tls.yml \
  -f docker-compose.logging.yml \
  -f docker-compose.full.yml \
  up -d
```

---

## Verification

### Step 1: Check Service Health

```bash
# Check all services are running
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo ps

# Expected status: All services "Up" and "healthy"
```

### Step 2: Verify TLS Connections

**HCD (Cassandra)**:

```bash
# Test TLS connection with cqlsh
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo exec hcd cqlsh \
  --ssl \
  -u cassandra \
  -p "${HCD_PASSWORD}" \
  hcd 9142

# Should connect successfully
```

**JanusGraph**:

```bash
# Test TLS WebSocket connection
curl -k https://localhost:18182?gremlin=g.V().count()

# Should return: {"result":{"data":[0],"meta":{}}}
```

**Grafana**:

```bash
# Test HTTPS connection
curl -k https://localhost:3443/api/health

# Should return: {"database":"ok","version":"..."}
```

**Prometheus**:

```bash
# Test HTTP connection
curl http://localhost:9090/-/healthy

# Should return: Prometheus is Healthy.
```

### Step 3: Verify Certificate Chain

```bash
# Verify HCD certificate chain
openssl s_client -connect localhost:9142 -showcerts

# Verify JanusGraph certificate chain
openssl s_client -connect localhost:18182 -showcerts

# Check for:
# - Certificate chain validation
# - TLS version (TLSv1.2 or TLSv1.3)
# - Cipher suite
```

### Step 4: Test Client Connections

**Python Client**:

```python
from gremlin_python.driver import client, serializer
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

# Connect with TLS
connection = DriverRemoteConnection(
    'wss://localhost:18182/gremlin',
    'g',
    username='admin',
    password='your-password',
    ssl_options={
        'cert_reqs': ssl.CERT_REQUIRED,
        'ca_certs': 'config/certs/ca.crt'
    }
)

# Test query
g = traversal().with_remote(connection)
count = g.V().count().next()
print(f"Vertex count: {count}")
```

**Java Client**:

```java
Cluster cluster = Cluster.build()
    .addContactPoint("localhost")
    .port(8182)
    .enableSsl(true)
    .sslContext(createSSLContext())
    .credentials("admin", "your-password")
    .create();

Client client = cluster.connect();
ResultSet results = client.submit("g.V().count()");
```

---

## Troubleshooting

### Common Issues

#### 1. Certificate Verification Failed

**Symptom**: `SSL certificate problem: unable to get local issuer certificate`

**Solution**:

```bash
# Regenerate certificates
rm -rf config/certs/*
./scripts/security/generate_certificates.sh

# Restart services
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo -f docker-compose.yml -f docker-compose.tls.yml restart
```

#### 2. Connection Refused

**Symptom**: `Connection refused` or `Connection timeout`

**Solution**:

```bash
# Check service logs
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo logs hcd
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo logs janusgraph

# Verify ports are listening
netstat -tlnp | grep -E '9142|8182'

# Check firewall rules
sudo iptables -L -n | grep -E '9142|8182'
```

#### 3. Keystore Password Mismatch

**Symptom**: `Keystore was tampered with, or password was incorrect`

**Solution**:

```bash
# Verify password in .env matches keystore
keytool -list -keystore config/certs/hcd-server.keystore.jks \
  -storepass "${HCD_KEYSTORE_PASSWORD}"

# If mismatch, regenerate keystores with correct password
```

#### 4. Certificate Expired

**Symptom**: `Certificate has expired`

**Solution**:

```bash
# Check certificate expiration
openssl x509 -in config/certs/hcd-server.crt -noout -dates

# Regenerate certificates
./scripts/security/generate_certificates.sh

# Restart services
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo -f docker-compose.yml -f docker-compose.tls.yml restart
```

### Debug Mode

Enable debug logging for TLS troubleshooting:

**HCD**:

```bash
# Add to docker-compose.tls.yml
environment:
  - JVM_OPTS=-Djavax.net.debug=ssl:handshake:verbose
```

**JanusGraph**:

```bash
# Add to docker-compose.tls.yml
environment:
  - JAVA_OPTIONS=-Djavax.net.debug=ssl:handshake:verbose
```

### Log Analysis

```bash
# Check TLS handshake logs
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo logs hcd | grep -i "ssl\|tls"
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo logs janusgraph | grep -i "ssl\|tls"

# Check certificate loading
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo logs hcd | grep -i "keystore\|truststore"
```

---

## Security Best Practices

### 1. Certificate Management

- **Rotate certificates every 90 days** (recommended) or annually (minimum)
- **Use strong passwords** for keystores (32+ characters)
- **Store private keys securely** with restricted permissions (600)
- **Never commit certificates** to version control
- **Use separate certificates** for each environment (dev/staging/prod)

### 2. TLS Configuration

- **Use TLS 1.2 or higher** (TLS 1.0/1.1 are deprecated)
- **Disable weak cipher suites** (RC4, DES, 3DES)
- **Enable Perfect Forward Secrecy** (ECDHE cipher suites)
- **Use strong key sizes** (RSA 2048+ bits, ECDSA 256+ bits)
- **Enable HSTS** for web interfaces

### 3. Certificate Validation

- **Enable certificate validation** in all clients
- **Verify hostname** matches certificate CN/SAN
- **Check certificate expiration** regularly
- **Monitor certificate chain** for revocations

### 4. Access Control

- **Restrict certificate access** to authorized users only
- **Use mutual TLS** (mTLS) for service-to-service communication
- **Implement certificate pinning** for critical connections
- **Audit certificate usage** regularly

### 5. Monitoring

- **Monitor TLS handshake failures**
- **Alert on certificate expiration** (30 days before)
- **Track cipher suite usage**
- **Log all TLS errors**

### 6. Compliance

- **PCI DSS**: TLS 1.2+ required
- **HIPAA**: Encryption in transit required
- **GDPR**: Data protection in transit required
- **SOC 2**: Encryption controls required

---

## Certificate Renewal

### Automated Renewal (Recommended)

Create a cron job for automatic certificate renewal:

```bash
# Edit crontab
crontab -e

# Add renewal job (runs monthly)
0 0 1 * * /path/to/scripts/security/renew_certificates.sh
```

### Manual Renewal

```bash
# 1. Backup existing certificates
cp -r config/certs config/certs.backup.$(date +%Y%m%d)

# 2. Generate new certificates
./scripts/security/generate_certificates.sh

# 3. Restart services with zero downtime
PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo -f docker-compose.yml -f docker-compose.tls.yml \
  up -d --force-recreate --no-deps hcd janusgraph

# 4. Verify new certificates
openssl x509 -in config/certs/hcd-server.crt -noout -dates
```

---

## Performance Considerations

### TLS Overhead

- **CPU**: 5-10% increase for TLS encryption/decryption
- **Latency**: 1-2ms additional latency per request
- **Throughput**: 5-15% reduction in maximum throughput

### Optimization Tips

1. **Use hardware acceleration** (AES-NI on modern CPUs)
2. **Enable TLS session resumption**
3. **Use ECDSA certificates** (faster than RSA)
4. **Tune cipher suites** for performance vs security
5. **Monitor TLS metrics** and adjust as needed

---

## Additional Resources

### Documentation

- [JanusGraph Security](https://docs.janusgraph.org/security/)
- [Cassandra TLS/SSL](https://cassandra.apache.org/doc/latest/operating/security.html)
- [OpenSSL Documentation](https://www.openssl.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)

### Tools

- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/)
- [testssl.sh](https://testssl.sh/)
- [nmap SSL scripts](https://nmap.org/nsedoc/scripts/ssl-enum-ciphers.html)

### Support

For issues or questions:

1. Check logs: `PODMAN_CONNECTION=podman-wxd podman-compose -p janusgraph-demo logs <service>`
2. Review troubleshooting section above
3. Consult service-specific documentation
4. Contact security team

---

## Appendix

### A. Certificate File Structure

```
config/certs/
├── ca.key                              # Root CA private key
├── ca.crt                              # Root CA certificate
├── hcd-server.key                      # HCD private key
├── hcd-server.crt                      # HCD certificate
├── hcd-server.keystore.jks             # HCD Java keystore
├── hcd-server.truststore.jks           # HCD Java truststore
├── janusgraph-server.key               # JanusGraph private key
├── janusgraph-server.crt               # JanusGraph certificate
├── janusgraph-server.keystore.jks      # JanusGraph Java keystore
├── janusgraph-server.truststore.jks    # JanusGraph Java truststore
├── grafana.key                         # Grafana private key
├── grafana.crt                         # Grafana certificate
├── prometheus.key                      # Prometheus private key
└── prometheus.crt                      # Prometheus certificate
```

### B. Port Reference

| Service | Non-TLS Port | TLS Port | Protocol |
|---------|--------------|----------|----------|
| HCD CQL | 9042 | 9142 | CQL |
| HCD Inter-node | 7000 | 7001 | Gossip |
| JanusGraph | 8182 | 8182 | WebSocket |
| Grafana | 3000 | 3443 | HTTPS |
| Prometheus | 9090 | 9443 | HTTPS |

### C. Environment Variables Reference

```bash
# Keystore passwords
HCD_KEYSTORE_PASSWORD=<strong-password>
HCD_TRUSTSTORE_PASSWORD=<strong-password>
JANUSGRAPH_KEYSTORE_PASSWORD=<strong-password>
JANUSGRAPH_TRUSTSTORE_PASSWORD=<strong-password>

# Certificate details
TLS_COUNTRY=US
TLS_STATE=California
TLS_CITY=San Francisco
TLS_ORGANIZATION=YourOrganization
TLS_ORGANIZATIONAL_UNIT=IT
TLS_COMMON_NAME=localhost
TLS_VALIDITY_DAYS=365

# TLS ports
HCD_CQL_TLS_PORT=9142
JANUSGRAPH_GREMLIN_TLS_PORT=8182
GRAFANA_HTTPS_PORT=3443
PROMETHEUS_HTTPS_PORT=9443
```

---

**Document Version**: 1.0
**Last Updated**: 2026-01-28
**Next Review**: 2026-04-28
