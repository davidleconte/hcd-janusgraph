# API Documentation

## Overview

This directory contains comprehensive API documentation for the HCD JanusGraph project. The documentation covers REST APIs, Gremlin query language, integration guides, and code examples.

## Documentation Structure

### 1. [OpenAPI Specification](./openapi.yaml)
**Format:** YAML  
**Purpose:** Complete REST API specification following OpenAPI 3.0.3 standard

**Contents:**
- Health check endpoints
- Vertex CRUD operations
- Edge CRUD operations
- Query execution (Gremlin & Cypher)
- Schema management
- Metrics and monitoring
- Authentication & authorization
- Error handling specifications
- Rate limiting details

**Use Cases:**
- Generate API clients in multiple languages
- API testing and validation
- Interactive API documentation (Swagger UI)
- Contract testing

**Tools:**
```bash
# View in Swagger UI
docker run -p 8080:8080 -e SWAGGER_JSON=/docs/openapi.yaml \
  -v $(pwd)/docs/api:/docs swaggerapi/swagger-ui

# Generate Python client
openapi-generator-cli generate -i openapi.yaml -g python -o ./client

# Validate specification
swagger-cli validate openapi.yaml
```

---

### 2. [Gremlin API Reference](./gremlin-api.md)
**Format:** Markdown  
**Purpose:** Comprehensive guide to Gremlin graph traversal language

**Contents:**
- Connection setup (Python, Java, Node.js)
- Basic traversals (vertices, edges, counts)
- CRUD operations with examples
- Filtering and predicates
- Aggregation and statistics
- Path traversals and algorithms
- Advanced patterns (recommendations, PageRank, community detection)
- Performance optimization techniques
- Best practices and common pitfalls

**Sections:**
1. **Connection** - Establishing connections to JanusGraph
2. **Basic Traversals** - Fundamental graph operations
3. **Vertex Operations** - Create, read, update, delete vertices
4. **Edge Operations** - Manage relationships between vertices
5. **Filtering** - Query filtering with predicates
6. **Aggregation** - Group, count, and statistical operations
7. **Path Traversals** - Finding paths and cycles
8. **Advanced Patterns** - Real-world graph algorithms
9. **Performance Optimization** - Query optimization strategies
10. **Best Practices** - Production-ready code patterns

**Code Examples:**
- 50+ working code examples
- Python, Groovy, and raw Gremlin syntax
- Real-world use cases (social networks, recommendations)

---

### 3. [Integration Guide](./integration-guide.md)
**Format:** Markdown  
**Purpose:** Practical integration examples and patterns

**Contents:**
- Quick start guide
- Authentication methods (API keys, JWT, WebSocket)
- Complete Python integration example (social network)
- Error handling patterns
- Performance optimization (connection pooling, batching)
- Production best practices
- Configuration management
- Health checks and monitoring
- Graceful shutdown patterns

**Featured Example:**
Complete `SocialNetworkGraph` class demonstrating:
- Connection management
- User creation and management
- Friendship relationships
- Friend recommendations
- Mutual friend discovery
- Error handling and logging

**Production Patterns:**
- Connection pooling
- Batch operations
- Query optimization
- Configuration management
- Health checks
- Monitoring and metrics
- Graceful shutdown

---

## Quick Start

### 1. REST API

```bash
# Health check
curl http://localhost:8182/health

# Create vertex
curl -X POST http://localhost:8182/v1/vertices \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "label": "person",
    "properties": {
      "name": "John Doe",
      "age": 30
    }
  }'

# Execute Gremlin query
curl -X POST http://localhost:8182/v1/queries/gremlin \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "gremlin": "g.V().count()",
    "bindings": {}
  }'
```

### 2. Python Gremlin Client

```python
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal

# Connect
connection = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
g = traversal().withRemote(connection)

# Query
count = g.V().count().next()
print(f"Vertex count: {count}")

# Create vertex
person = g.addV('person') \
    .property('name', 'Alice') \
    .property('age', 28) \
    .next()

# Close
connection.close()
```

### 3. Using the Integration Library

```python
from docs.api.examples import SocialNetworkGraph

graph = SocialNetworkGraph()
try:
    graph.connect()
    
    # Create users
    alice_id = graph.create_user('Alice', 28, 'alice@example.com', 'NYC')
    bob_id = graph.create_user('Bob', 32, 'bob@example.com', 'NYC')
    
    # Create friendship
    graph.create_friendship(alice_id, bob_id, 2020)
    
    # Find friends
    friends = graph.find_friends(alice_id)
    print(f"Alice's friends: {friends}")
    
finally:
    graph.disconnect()
```

---

## API Endpoints Summary

### Health & Status
- `GET /health` - Health check
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe
- `GET /metrics` - System metrics

### Vertices
- `GET /vertices` - List vertices
- `POST /vertices` - Create vertex
- `GET /vertices/{id}` - Get vertex
- `PUT /vertices/{id}` - Update vertex
- `DELETE /vertices/{id}` - Delete vertex

### Edges
- `GET /edges` - List edges
- `POST /edges` - Create edge
- `GET /edges/{id}` - Get edge
- `DELETE /edges/{id}` - Delete edge

### Queries
- `POST /queries/gremlin` - Execute Gremlin query
- `POST /queries/cypher` - Execute Cypher query

### Schema
- `GET /schema` - Get schema
- `GET /schema/vertex-labels` - List vertex labels
- `POST /schema/vertex-labels` - Create vertex label
- `GET /schema/edge-labels` - List edge labels
- `POST /schema/edge-labels` - Create edge label

---

## Authentication

All API endpoints (except health checks) require authentication using one of:

### 1. API Key
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8182/v1/vertices
```

### 2. JWT Bearer Token
```bash
curl -H "Authorization: Bearer your-jwt-token" http://localhost:8182/v1/vertices
```

### 3. WebSocket Authentication
```python
from gremlin_python.driver import client

gremlin_client = client.Client(
    'wss://api.example.com:8182/gremlin',
    'g',
    username='your-username',
    password='your-password'
)
```

---

## Rate Limiting

- **Per API Key:** 1000 requests/hour
- **Per IP Address:** 100 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1640000000
```

---

## Error Handling

All errors follow RFC 7807 Problem Details format:

```json
{
  "type": "https://api.example.com/errors/not-found",
  "title": "Vertex Not Found",
  "status": 404,
  "detail": "Vertex with ID '12345' does not exist",
  "instance": "/v1/vertices/12345",
  "traceId": "abc123def456"
}
```

Common status codes:
- `200` - Success
- `201` - Created
- `204` - No Content
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## Code Examples

### Python Examples
See [Integration Guide](./integration-guide.md) for:
- Social network implementation
- Error handling patterns
- Connection pooling
- Batch operations
- Production best practices

### Gremlin Examples
See [Gremlin API Reference](./gremlin-api.md) for:
- Basic CRUD operations
- Complex traversals
- Graph algorithms
- Performance optimization
- 50+ working examples

---

## Tools and Utilities

### API Testing
```bash
# Using curl
curl -X GET http://localhost:8182/health

# Using httpie
http GET http://localhost:8182/v1/vertices X-API-Key:your-key

# Using Postman
# Import openapi.yaml into Postman for interactive testing
```

### Code Generation
```bash
# Generate Python client
openapi-generator-cli generate -i openapi.yaml -g python

# Generate Java client
openapi-generator-cli generate -i openapi.yaml -g java

# Generate TypeScript client
openapi-generator-cli generate -i openapi.yaml -g typescript-axios
```

### Documentation Viewing
```bash
# Swagger UI
docker run -p 8080:8080 -e SWAGGER_JSON=/docs/openapi.yaml \
  -v $(pwd)/docs/api:/docs swaggerapi/swagger-ui

# ReDoc
docker run -p 8080:80 -e SPEC_URL=/docs/openapi.yaml \
  -v $(pwd)/docs/api:/docs redocly/redoc

# Access at http://localhost:8080
```

---

## Performance Guidelines

### Query Optimization
1. Use indexed properties in `has()` steps
2. Limit results early in traversals
3. Use batch operations for bulk inserts
4. Leverage connection pooling
5. Profile queries with `.profile()`

### Best Practices
1. Always close connections
2. Use context managers
3. Handle errors gracefully
4. Implement retry logic
5. Monitor query performance
6. Use parameterized queries
7. Implement health checks

---

## Monitoring and Observability

### Metrics Available
- Vertex/edge counts
- Query execution times
- Error rates
- Connection pool statistics
- System resource usage

### Distributed Tracing
All API calls include trace IDs for distributed tracing:
- Jaeger UI: http://localhost:16686
- Trace ID in response headers: `X-Trace-Id`
- Trace ID in error responses: `traceId` field

### Logging
Structured logs include:
- Request ID
- Trace ID
- User ID
- Query execution time
- Error details

---

## Support and Resources

### Documentation
- [Architecture Documentation](../architecture/README.md)
- Deployment Guide (see Getting Started)
- Troubleshooting (see [Operations Runbook](../operations/operations-runbook.md))
- `SECURITY.md` (root) - Security guidelines

### External Resources
- [JanusGraph Documentation](https://docs.janusgraph.org/)
- [Apache TinkerPop](https://tinkerpop.apache.org/)
- [Gremlin Recipes](https://tinkerpop.apache.org/docs/current/recipes/)
- [OpenAPI Specification](https://swagger.io/specification/)

### Community
- GitHub Issues: [Project Repository]
- Email: support@example.com
- Slack: [Community Slack]
- Stack Overflow: Tag `janusgraph`

---

## Version History

### v1.0.0 (Current)
- Initial API release
- REST endpoints for CRUD operations
- Gremlin query execution
- Schema management
- Authentication and rate limiting
- Comprehensive documentation

### Upcoming Features
- GraphQL API support
- Bulk import/export endpoints
- Advanced analytics endpoints
- Real-time subscriptions
- Enhanced monitoring

---

## License

This documentation is part of the HCD JanusGraph project and is licensed under the Apache License 2.0.

---

**Last Updated:** 2026-01-28  
**API Version:** 1.0.0  
**Documentation Version:** 1.0.0