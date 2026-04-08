# REST API Examples Guide

**Version:** 1.0.0  
**Last Updated:** 2026-04-08  
**Base URL:** `http://localhost:8000`

This guide provides practical examples for all REST API endpoints with request/response samples, error handling, and best practices.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Health & Status](#health--status)
3. [UBO Discovery](#ubo-discovery)
4. [AML Detection](#aml-detection)
5. [Fraud Detection](#fraud-detection)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Best Practices](#best-practices)

---

## Authentication

### JWT Token Authentication

All API endpoints (except health checks) require JWT authentication.

**Request Header:**
```bash
Authorization: Bearer <your-jwt-token>
```

**Example: Get Token**
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "analyst@example.com",
    "password": "your-secure-password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Using Token in Requests:**
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/ubo/discover
```

---

## Health & Status

### Check API Health

**Endpoint:** `GET /healthz`

**Example:**
```bash
curl http://localhost:8000/healthz
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-08T10:30:00Z",
  "version": "1.0.0"
}
```

### Check Readiness

**Endpoint:** `GET /readyz`

Verifies all dependencies (JanusGraph, OpenSearch, Pulsar) are ready.

**Example:**
```bash
curl http://localhost:8000/readyz
```

**Response (Ready):**
```json
{
  "status": "ready",
  "checks": {
    "janusgraph": "ok",
    "opensearch": "ok",
    "pulsar": "ok"
  }
}
```

**Response (Not Ready):**
```json
{
  "status": "not_ready",
  "checks": {
    "janusgraph": "ok",
    "opensearch": "failed",
    "pulsar": "ok"
  },
  "error": "OpenSearch connection failed"
}
```

### Get System Stats

**Endpoint:** `GET /api/v1/stats`

**Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/stats
```

**Response:**
```json
{
  "graph": {
    "vertex_count": 15234,
    "edge_count": 45678,
    "person_count": 5000,
    "company_count": 1000,
    "account_count": 8000,
    "transaction_count": 1234
  },
  "cache": {
    "size": 856,
    "max_size": 1000,
    "hits": 12456,
    "misses": 3421,
    "hit_ratio": 0.7845,
    "evictions": 234
  },
  "uptime_seconds": 86400
}
```

---

## UBO Discovery

### Discover Ultimate Beneficial Owners

**Endpoint:** `POST /api/v1/ubo/discover`

Identifies individuals with significant ownership (default: 25%+) through direct and indirect ownership chains.

**Request Body:**
```json
{
  "company_id": "COMP-00001",
  "ownership_threshold": 25.0,
  "include_indirect": true,
  "max_depth": 5
}
```

**Parameters:**
- `company_id` (required): Company identifier
- `ownership_threshold` (optional): Minimum ownership % (default: 25.0)
- `include_indirect` (optional): Include indirect ownership (default: true)
- `max_depth` (optional): Maximum ownership chain depth (default: 5)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/ubo/discover \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "COMP-00001",
    "ownership_threshold": 25.0,
    "include_indirect": true,
    "max_depth": 5
  }'
```

**Response:**
```json
{
  "target_entity_id": "COMP-00001",
  "target_entity_name": "Acme Corporation Ltd",
  "ubos": [
    {
      "person_id": "PER-ABC123456789",
      "name": "John Smith",
      "ownership_percentage": 45.5,
      "ownership_type": "direct",
      "chain_length": 1
    },
    {
      "person_id": "PER-DEF987654321",
      "name": "Jane Doe",
      "ownership_percentage": 30.2,
      "ownership_type": "indirect",
      "chain_length": 2
    }
  ],
  "total_layers": 2,
  "has_circular_ownership": false,
  "high_risk_indicators": [],
  "risk_score": 0.0,
  "query_time_ms": 45.23
}
```

**High Risk Example:**
```json
{
  "target_entity_id": "COMP-00002",
  "target_entity_name": "Shell Company Inc",
  "ubos": [],
  "total_layers": 5,
  "has_circular_ownership": true,
  "high_risk_indicators": [
    "No beneficial owners identified above threshold",
    "Circular ownership detected",
    "Complex ownership structure (5+ layers)"
  ],
  "risk_score": 85.0,
  "query_time_ms": 123.45
}
```

### Get Ownership Network

**Endpoint:** `GET /api/v1/ubo/network/{company_id}`

Returns full ownership network for visualization.

**Query Parameters:**
- `max_depth` (optional): Maximum traversal depth (default: 3)
- `min_ownership` (optional): Minimum ownership % to include (default: 10.0)

**Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/api/v1/ubo/network/COMP-00001?max_depth=3&min_ownership=10.0"
```

**Response:**
```json
{
  "nodes": [
    {
      "id": "COMP-00001",
      "label": "Acme Corporation Ltd",
      "type": "company",
      "properties": {
        "jurisdiction": "US-DE",
        "incorporation_date": "2020-01-15"
      }
    },
    {
      "id": "PER-ABC123456789",
      "label": "John Smith",
      "type": "person",
      "properties": {
        "nationality": "US",
        "is_pep": false
      }
    }
  ],
  "edges": [
    {
      "source": "PER-ABC123456789",
      "target": "COMP-00001",
      "type": "owns",
      "properties": {
        "ownership_percentage": 45.5,
        "ownership_type": "direct"
      }
    }
  ],
  "total_nodes": 2,
  "total_edges": 1
}
```

---

## AML Detection

### Detect Structuring (Smurfing)

**Endpoint:** `POST /api/v1/aml/structuring`

Identifies accounts with multiple transactions just below reporting thresholds (potential CTR evasion).

**Request Body:**
```json
{
  "account_id": null,
  "threshold_amount": 10000.0,
  "time_window_days": 30,
  "min_transaction_count": 5,
  "offset": 0,
  "limit": 50
}
```

**Parameters:**
- `account_id` (optional): Specific account to analyze (null = all accounts)
- `threshold_amount` (optional): Reporting threshold (default: 10000.0)
- `time_window_days` (optional): Analysis period (default: 30)
- `min_transaction_count` (optional): Minimum transactions to flag (default: 5)
- `offset` (optional): Pagination offset (default: 0)
- `limit` (optional): Results per page (default: 50, max: 500)

**Example: Analyze All Accounts**
```bash
curl -X POST http://localhost:8000/api/v1/aml/structuring \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold_amount": 10000.0,
    "time_window_days": 30,
    "min_transaction_count": 5
  }'
```

**Example: Analyze Specific Account**
```bash
curl -X POST http://localhost:8000/api/v1/aml/structuring \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "ACC-12345",
    "threshold_amount": 10000.0,
    "time_window_days": 7,
    "min_transaction_count": 3
  }'
```

**Response:**
```json
{
  "alerts": [
    {
      "account_id": "ACC-12345",
      "account_holder": "John Smith",
      "total_amount": 48500.0,
      "transaction_count": 7,
      "time_window": "30 days",
      "risk_score": 75.5,
      "pattern_type": "potential_structuring"
    },
    {
      "account_id": "ACC-67890",
      "account_holder": "Jane Doe",
      "total_amount": 39200.0,
      "transaction_count": 5,
      "time_window": "30 days",
      "risk_score": 62.3,
      "pattern_type": "potential_structuring"
    }
  ],
  "total_alerts": 2,
  "analysis_period": "2026-03-09 to 2026-04-08",
  "query_time_ms": 234.56
}
```

**Risk Score Interpretation:**
- `0-30`: Low risk - May be legitimate business activity
- `31-60`: Medium risk - Warrants review
- `61-80`: High risk - Requires investigation
- `81-100`: Critical risk - Immediate action required

---

## Fraud Detection

### Detect Fraud Rings

**Endpoint:** `GET /api/v1/fraud/rings`

Identifies groups of individuals sharing addresses/phones with suspicious transaction patterns.

**Query Parameters:**
- `min_members` (optional): Minimum ring members (default: 3, range: 2-10)
- `include_accounts` (optional): Include account details (default: true)
- `offset` (optional): Pagination offset (default: 0)
- `limit` (optional): Results per page (default: 50, max: 500)

**Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/api/v1/fraud/rings?min_members=3&include_accounts=true&limit=10"
```

**Response:**
```json
{
  "rings": [
    {
      "shared_identifier": "123 Main St, New York, NY 10001",
      "identifier_type": "address",
      "members": [
        {
          "person_id": "PER-ABC123",
          "name": "John Smith",
          "accounts": ["ACC-11111", "ACC-22222"]
        },
        {
          "person_id": "PER-DEF456",
          "name": "Jane Doe",
          "accounts": ["ACC-33333"]
        },
        {
          "person_id": "PER-GHI789",
          "name": "Bob Johnson",
          "accounts": ["ACC-44444", "ACC-55555"]
        }
      ],
      "member_count": 3,
      "total_accounts": 5,
      "risk_indicators": [
        "Multiple accounts per member",
        "High transaction velocity",
        "Shared residential address"
      ],
      "risk_score": 68.5
    }
  ],
  "total_detected": 1,
  "offset": 0,
  "limit": 10
}
```

---

## Error Handling

### Standard Error Response

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 400,
  "error_type": "ValidationError",
  "timestamp": "2026-04-08T10:30:00Z"
}
```

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid parameters or malformed JSON |
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | Company/account/person not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | Graph database connection failed |

### Error Examples

**400 Bad Request:**
```json
{
  "detail": "ownership_threshold must be between 0 and 100",
  "status_code": 400,
  "error_type": "ValidationError"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Invalid or expired token",
  "status_code": 401,
  "error_type": "AuthenticationError"
}
```

**404 Not Found:**
```json
{
  "detail": "Company not found: COMP-99999",
  "status_code": 404,
  "error_type": "NotFoundError"
}
```

**429 Rate Limit:**
```json
{
  "detail": "Rate limit exceeded: 100 requests per minute",
  "status_code": 429,
  "error_type": "RateLimitError",
  "retry_after": 45
}
```

**502 Bad Gateway:**
```json
{
  "detail": "Graph database traversal failed",
  "status_code": 502,
  "error_type": "DatabaseError"
}
```

---

## Rate Limiting

### Default Limits

- **Default:** 100 requests per minute per IP
- **Authenticated:** 500 requests per minute per user
- **Burst:** 20 requests per second

### Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1712574000
```

### Handling Rate Limits

**Example: Retry with Exponential Backoff**
```python
import time
import requests

def api_call_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            wait_time = min(retry_after, 2 ** attempt * 10)
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
            continue
            
        return response
    
    raise Exception("Max retries exceeded")
```

---

## Best Practices

### 1. Always Use HTTPS in Production

```bash
# ❌ Development only
curl http://localhost:8000/api/v1/ubo/discover

# ✅ Production
curl https://api.example.com/api/v1/ubo/discover
```

### 2. Store Tokens Securely

```python
# ❌ Don't hardcode tokens
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# ✅ Use environment variables
import os
TOKEN = os.getenv('API_TOKEN')
```

### 3. Implement Proper Error Handling

```python
import requests

try:
    response = requests.post(
        'http://localhost:8000/api/v1/ubo/discover',
        headers={'Authorization': f'Bearer {token}'},
        json={'company_id': 'COMP-00001'},
        timeout=30
    )
    response.raise_for_status()
    data = response.json()
except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e.response.status_code}")
    print(e.response.json())
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

### 4. Use Pagination for Large Results

```python
def fetch_all_alerts(base_url, token, page_size=50):
    all_alerts = []
    offset = 0
    
    while True:
        response = requests.post(
            f'{base_url}/api/v1/aml/structuring',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'threshold_amount': 10000.0,
                'offset': offset,
                'limit': page_size
            }
        )
        data = response.json()
        
        all_alerts.extend(data['alerts'])
        
        if len(data['alerts']) < page_size:
            break
            
        offset += page_size
    
    return all_alerts
```

### 5. Cache Responses When Appropriate

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def get_company_ubos(company_id, cache_key):
    # cache_key includes timestamp to control cache duration
    response = requests.post(
        'http://localhost:8000/api/v1/ubo/discover',
        headers={'Authorization': f'Bearer {token}'},
        json={'company_id': company_id}
    )
    return response.json()

# Use with 5-minute cache
cache_key = int(time.time() / 300)  # Changes every 5 minutes
ubos = get_company_ubos('COMP-00001', cache_key)
```

### 6. Monitor Query Performance

```python
import time

start = time.time()
response = requests.post(url, headers=headers, json=payload)
elapsed = (time.time() - start) * 1000

print(f"Request took {elapsed:.2f}ms")
print(f"Server processing: {response.json()['query_time_ms']:.2f}ms")
print(f"Network overhead: {elapsed - response.json()['query_time_ms']:.2f}ms")
```

### 7. Validate Input Before Sending

```python
def validate_ubo_request(company_id, threshold):
    if not company_id or not company_id.startswith('COMP-'):
        raise ValueError("Invalid company_id format")
    
    if not 0 <= threshold <= 100:
        raise ValueError("threshold must be between 0 and 100")
    
    return True

# Use validation
try:
    validate_ubo_request('COMP-00001', 25.0)
    response = requests.post(...)
except ValueError as e:
    print(f"Validation error: {e}")
```

---

## Complete Python Example

```python
#!/usr/bin/env python3
"""Complete example: Detect high-risk companies with structuring patterns."""

import os
import requests
from typing import List, Dict

class BankingAPIClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def discover_ubos(self, company_id: str) -> Dict:
        """Discover ultimate beneficial owners."""
        response = requests.post(
            f'{self.base_url}/api/v1/ubo/discover',
            headers=self.headers,
            json={'company_id': company_id},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def detect_structuring(self, account_id: str = None) -> List[Dict]:
        """Detect structuring patterns."""
        response = requests.post(
            f'{self.base_url}/api/v1/aml/structuring',
            headers=self.headers,
            json={
                'account_id': account_id,
                'threshold_amount': 10000.0,
                'min_transaction_count': 5
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()['alerts']
    
    def analyze_company_risk(self, company_id: str) -> Dict:
        """Complete risk analysis for a company."""
        # Get UBO information
        ubo_data = self.discover_ubos(company_id)
        
        # Check for high-risk indicators
        risk_factors = []
        risk_score = ubo_data['risk_score']
        
        if not ubo_data['ubos']:
            risk_factors.append('No identifiable beneficial owners')
            risk_score += 20
        
        if ubo_data['has_circular_ownership']:
            risk_factors.append('Circular ownership structure')
            risk_score += 15
        
        if ubo_data['total_layers'] > 3:
            risk_factors.append(f'Complex structure ({ubo_data["total_layers"]} layers)')
            risk_score += 10
        
        return {
            'company_id': company_id,
            'company_name': ubo_data['target_entity_name'],
            'risk_score': min(risk_score, 100),
            'risk_factors': risk_factors,
            'ubos': ubo_data['ubos'],
            'requires_investigation': risk_score > 60
        }

# Usage
if __name__ == '__main__':
    client = BankingAPIClient(
        base_url='http://localhost:8000',
        token=os.getenv('API_TOKEN')
    )
    
    # Analyze company
    result = client.analyze_company_risk('COMP-00001')
    
    print(f"Company: {result['company_name']}")
    print(f"Risk Score: {result['risk_score']}/100")
    print(f"Investigation Required: {result['requires_investigation']}")
    
    if result['risk_factors']:
        print("\nRisk Factors:")
        for factor in result['risk_factors']:
            print(f"  - {factor}")
    
    if result['ubos']:
        print(f"\nBeneficial Owners ({len(result['ubos'])}):")
        for ubo in result['ubos']:
            print(f"  - {ubo['name']}: {ubo['ownership_percentage']:.1f}%")
```

---

## Related Documentation

- [API Models Reference](./models.md) - Request/response model schemas
- [Authentication Guide](./authentication.md) - Detailed auth setup
- [GraphRepository API](../banking/guides/api-reference.md) - Python API reference
- [Deployment Guide](../QUICKSTART.md) - Setup and deployment

---

**Last Updated:** 2026-04-08  
**API Version:** 1.0.0  
**Maintainer:** Platform Engineering Team