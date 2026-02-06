# Authentication Setup Guide

**Date:** 2026-01-28  
**Version:** 1.0  
**Status:** Active

## Overview

All services in the HCD + JanusGraph banking compliance system require authentication. This guide explains how to configure credentials securely.

## Quick Start

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Generate secure passwords:
   ```bash
   # Generate 32-character random password
   openssl rand -base64 32
   ```

3. Update `.env` with your credentials:
   ```bash
   JANUSGRAPH_USERNAME=admin
   JANUSGRAPH_PASSWORD=your_secure_password_here
   
   OPENSEARCH_USERNAME=admin
   OPENSEARCH_PASSWORD=your_secure_password_here
   ```

4. Verify `.env` is in `.gitignore`:
   ```bash
   grep "^\.env$" .gitignore || echo ".env" >> .gitignore
   ```

## Password Requirements

**Minimum Requirements:**
- Length: 16 characters
- Complexity: Mix of uppercase, lowercase, numbers, symbols
- No dictionary words
- No personal information
- Unique per service

**Recommended:**
- Length: 32+ characters
- Generated randomly
- Stored in password manager
- Rotated every 90 days

## Service-Specific Configuration

### JanusGraph

```python
from src.python.client.janusgraph_client import JanusGraphClient

# Option 1: From environment variables (recommended)
client = JanusGraphClient(
    host="localhost",
    port=8182
    # Credentials loaded from JANUSGRAPH_USERNAME and JANUSGRAPH_PASSWORD
)

# Option 2: Explicit credentials (not recommended)
client = JanusGraphClient(
    host="localhost",
    port=8182,
    username="admin",
    password="secure_password"
)
```

### OpenSearch

```python
from src.python.utils.vector_search import VectorSearchClient

# From environment variables (recommended)
client = VectorSearchClient(
    host="localhost",
    port=9200
    # Credentials loaded from OPENSEARCH_USERNAME and OPENSEARCH_PASSWORD
)
```

## Production Deployment

### 1. Use Secrets Management

**AWS Secrets Manager:**
```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Load credentials
secrets = get_secret('banking-compliance/prod')
os.environ['JANUSGRAPH_USERNAME'] = secrets['janusgraph_username']
os.environ['JANUSGRAPH_PASSWORD'] = secrets['janusgraph_password']
```

**HashiCorp Vault:**
```python
import hvac

client = hvac.Client(url='https://vault.example.com')
client.auth.approle.login(role_id='...', secret_id='...')

secrets = client.secrets.kv.v2.read_secret_version(path='banking-compliance/prod')
os.environ['JANUSGRAPH_USERNAME'] = secrets['data']['data']['janusgraph_username']
```

### 2. Credential Rotation

```bash
# Rotate credentials every 90 days
# 1. Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)

# 2. Update service
# 3. Update .env or secrets manager
# 4. Restart services
# 5. Verify connectivity
```

### 3. Audit Logging

Enable authentication audit logs:
```python
import logging

# Configure audit logger
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)

# Log authentication attempts
audit_logger.info(f"Authentication attempt: user={username}, success={success}")
```

## Troubleshooting

### Authentication Failed

```
Error: Authentication required: username and password must be provided
```

**Solution:**
1. Check `.env` file exists
2. Verify credentials are set
3. Ensure no typos in variable names
4. Check environment variables are loaded

### Connection Refused

```
Error: Failed to connect to wss://localhost:8182/gremlin
```

**Solution:**
1. Verify service is running
2. Check firewall rules
3. Verify SSL/TLS configuration
4. Check credentials are correct

## Security Best Practices

1. **Never commit credentials to version control**
2. **Use environment variables or secrets management**
3. **Rotate credentials regularly (90 days)**
4. **Use strong, unique passwords per service**
5. **Enable audit logging**
6. **Monitor failed authentication attempts**
7. **Use principle of least privilege**
8. **Encrypt credentials at rest**
9. **Use SSL/TLS for all connections**
10. **Implement rate limiting**

## Compliance

### GDPR/CCPA
- Credentials are PII - handle accordingly
- Implement data retention policies
- Enable audit trails
- Support data deletion requests

### PCI DSS
- Strong authentication required
- Encrypt credentials in transit and at rest
- Regular security audits
- Access control and monitoring

### SOC 2
- Document authentication procedures
- Implement change management
- Regular access reviews
- Incident response procedures

## Related Documentation

- [SSL/TLS Configuration Guide](SSL_TLS_GUIDE.md)
- [Security Best Practices](SECURITY_BEST_PRACTICES.md)
- [Deployment Guide](../DEPLOYMENT.md)

---

*Made with Bob ✨*