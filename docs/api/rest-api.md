# REST API Reference

**Version:** 1.0.0
**Last Updated:** 2026-04-08
**Base URL:** `http://localhost:8000`

> **📚 For detailed examples and code samples, see [REST API Examples Guide](./REST_API_EXAMPLES.md)**

> **🔧 Auto-generated docs:** Run `./scripts/docs/generate_api_docs.sh` for full Python API documentation.

---

## Quick Links

- **[REST API Examples Guide](./REST_API_EXAMPLES.md)** - Comprehensive examples with curl, Python, error handling
- **[Authentication Guide](./authentication.md)** - JWT token setup and management
- **[GraphRepository API](../banking/guides/api-reference.md)** - Python API reference
- **[OpenAPI Spec](./openapi.yaml)** - Machine-readable API specification

---

## Overview

FastAPI-based REST API providing banking compliance and analytics capabilities:

- **UBO Discovery** - Ultimate Beneficial Owner identification
- **AML Detection** - Anti-Money Laundering pattern detection
- **Fraud Detection** - Fraud ring identification
- **Health Monitoring** - System health and statistics

**Key Features:**
- JWT authentication with role-based access control
- Rate limiting (100 req/min default, 500 req/min authenticated)
- Comprehensive error handling with detailed messages
- Query performance metrics in every response
- OpenAPI/Swagger documentation at `/docs`

---

## Base URL

```
http://localhost:8000/api/v1
```

**Production:** Use HTTPS and proper domain
```
https://api.example.com/api/v1
```

---

## Quick Start

### 1. Get Authentication Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "analyst@example.com", "password": "your-password"}'
```

### 2. Use Token in Requests

```bash
export TOKEN="your-jwt-token-here"

curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/stats
```

### 3. Explore Interactive Docs

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

---

## Endpoints Summary

### Health & Status

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/healthz` | Health check | No |
| GET | `/readyz` | Readiness check | No |
| GET | `/api/v1/stats` | System statistics | Yes |

### UBO Discovery

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/ubo/discover` | Discover beneficial owners | Yes |
| GET | `/api/v1/ubo/network/{company_id}` | Get ownership network | Yes |

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/ubo/discover \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"company_id": "COMP-00001", "ownership_threshold": 25.0}'
```

See [REST API Examples](./REST_API_EXAMPLES.md#ubo-discovery) for detailed examples.

### AML Detection

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/aml/structuring` | Detect structuring patterns | Yes |

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/aml/structuring \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"threshold_amount": 10000.0, "time_window_days": 30}'
```

See [REST API Examples](./REST_API_EXAMPLES.md#aml-detection) for detailed examples.

### Fraud Detection

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/fraud/rings` | Detect fraud rings | Yes |

**Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/api/v1/fraud/rings?min_members=3"
```

See [REST API Examples](./REST_API_EXAMPLES.md#fraud-detection) for detailed examples.

---

## Authentication

All API endpoints (except health checks) require JWT authentication.

**Header Format:**
```
Authorization: Bearer <your-jwt-token>
```

**Token Expiration:** 1 hour (3600 seconds)

See [REST API Examples - Authentication](./REST_API_EXAMPLES.md#authentication) for complete guide.

---

## Response Format

### Success Response

```json
{
  "target_entity_id": "COMP-00001",
  "target_entity_name": "Acme Corporation",
  "ubos": [...],
  "query_time_ms": 45.23
}
```

### Error Response

```json
{
  "detail": "Company not found: COMP-99999",
  "status_code": 404,
  "error_type": "NotFoundError",
  "timestamp": "2026-04-08T10:30:00Z"
}
```

See [REST API Examples - Error Handling](./REST_API_EXAMPLES.md#error-handling) for all error codes.

---

## Rate Limiting

- **Default:** 100 requests per minute per IP
- **Authenticated:** 500 requests per minute per user
- **Burst:** 20 requests per second

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1712574000
```

See [REST API Examples - Rate Limiting](./REST_API_EXAMPLES.md#rate-limiting) for handling strategies.

---

## Best Practices

1. **Always use HTTPS in production**
2. **Store tokens securely** (environment variables, not hardcoded)
3. **Implement proper error handling** with retries
4. **Use pagination** for large result sets
5. **Cache responses** when appropriate
6. **Monitor query performance** using `query_time_ms`
7. **Validate input** before sending requests

See [REST API Examples - Best Practices](./REST_API_EXAMPLES.md#best-practices) for detailed guidance.

---

## Complete Examples

For comprehensive examples including:
- Full request/response samples
- Error handling patterns
- Python client implementation
- Pagination strategies
- Performance monitoring

**See:** [REST API Examples Guide](./REST_API_EXAMPLES.md)

---

## Related Documentation

- **[REST API Examples](./REST_API_EXAMPLES.md)** - Comprehensive examples and code samples
- **[GraphRepository API](../banking/guides/api-reference.md)** - Python API reference
- **[Deployment Guide](../QUICKSTART.md)** - Setup and deployment
- **[Architecture Docs](../architecture/)** - System architecture

---

**Last Updated:** 2026-04-08
**API Version:** 1.0.0
**Maintainer:** Platform Engineering Team
