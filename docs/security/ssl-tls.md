# SSL/TLS Configuration

**Author:** David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
**Contact:**

## Overview

SSL/TLS encryption secures all communication between services.

## Certificate Generation

```bash
./scripts/security/generate_certificates.sh
```

This creates:

- CA certificate
- Server certificates for each service
- Client certificates for applications

## Configuration

### JanusGraph

```properties
# config/janusgraph/janusgraph-server.properties
gremlin.server.ssl.enabled=true
gremlin.server.ssl.keyCertChainFile=/etc/ssl/server.crt
gremlin.server.ssl.keyFile=/etc/ssl/server.key
```

### OpenSearch

```yaml
# config/opensearch/opensearch.yml
plugins.security.ssl.http.enabled: true
plugins.security.ssl.http.pemcert_filepath: server.crt
plugins.security.ssl.http.pemkey_filepath: server.key
```

## Development Mode

For local development, SSL can be disabled:

```bash
export JANUSGRAPH_USE_SSL=false
export OPENSEARCH_USE_SSL=false
```
