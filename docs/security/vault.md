# HashiCorp Vault Integration

**Author:** David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
**Contact:**

## Overview

HashiCorp Vault provides centralized secrets management.

## Initialization

```bash
./scripts/security/init_vault.sh
```

## Accessing Secrets

```bash
# Source access script
source ./scripts/security/vault_access.sh

# Get secret
podman exec -e VAULT_TOKEN=$VAULT_APP_TOKEN vault-server \
    vault kv get janusgraph/admin
```

## Secret Paths

| Path | Description |
|------|-------------|
| `janusgraph/admin` | JanusGraph admin credentials |
| `opensearch/admin` | OpenSearch admin credentials |
| `pulsar/admin` | Pulsar admin credentials |

## Python Integration

```python
import hvac

client = hvac.Client(url='http://localhost:8200')
client.token = os.environ['VAULT_TOKEN']

secret = client.secrets.kv.v2.read_secret_version(
    path='janusgraph/admin'
)
password = secret['data']['data']['password']
```
