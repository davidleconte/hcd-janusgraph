# Configuration Guide

**Author:** David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
**Contact:**

## Environment Variables

### JanusGraph

| Variable | Default | Description |
|----------|---------|-------------|
| `JANUSGRAPH_PORT` | 18182 | Gremlin server port |
| `JANUSGRAPH_HOST` | localhost | Server hostname |
| `JANUSGRAPH_USE_SSL` | false | Enable SSL/TLS |

### OpenSearch

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENSEARCH_HOST` | localhost | OpenSearch hostname |
| `OPENSEARCH_PORT` | 9200 | OpenSearch port |
| `OPENSEARCH_USE_SSL` | false | Enable SSL/TLS |

### Pulsar

| Variable | Default | Description |
|----------|---------|-------------|
| `PULSAR_URL` | pulsar://localhost:6650 | Broker URL |

## Configuration Files

- `.env` - Environment variables
- `.env.example` - Template with defaults
- `config/janusgraph/` - JanusGraph configs
- `config/compose/` - Docker Compose files

## Security Configuration

See [Security Guide](../security/overview.md) for SSL/TLS and Vault setup.
