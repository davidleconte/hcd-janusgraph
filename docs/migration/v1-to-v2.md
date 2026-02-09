# Migration Guide: v1.x to v2.0

This guide helps you migrate from HCD JanusGraph API v1.x to v2.0.

## Overview

Version 2.0 introduces significant security and performance improvements, including:

- JWT-based authentication (BREAKING)
- Enhanced RBAC with MFA support
- Query caching and profiling
- Distributed tracing
- Standardized error responses (BREAKING)

**Estimated Migration Time**: 2-4 hours for typical applications

---

## Breaking Changes

### 1. Authentication System

#### What Changed

- **Removed**: Basic authentication
- **Added**: JWT token-based authentication
- **Required**: All API calls must include `Authorization` header

#### Before (v1.x)

```python
import requests

response = requests.get(
    'http://localhost:8080/graph/vertices',
    auth=('username', 'password')  # Basic auth
)
```

#### After (v2.0)

```python
import requests

# Step 1: Authenticate and get token
auth_response = requests.post(
    'https://localhost:8443/auth/login',
    json={
        'username': 'username',
        'password': 'password'
    }
)
token = auth_response.json()['access_token']

# Step 2: Use token in subsequent requests
response = requests.get(
    'https://localhost:8443/graph/vertices',
    headers={'Authorization': f'Bearer {token}'}
)
```

#### Migration Steps

1. **Update Authentication Flow**:

   ```python
   class JanusGraphClient:
       def __init__(self, base_url, username, password):
           self.base_url = base_url
           self.username = username
           self.password = password
           self.access_token = None
           self.refresh_token = None

       def authenticate(self):
           """Get JWT tokens"""
           response = requests.post(
               f'{self.base_url}/auth/login',
               json={
                   'username': self.username,
                   'password': self.password
               }
           )
           data = response.json()
           self.access_token = data['access_token']
           self.refresh_token = data['refresh_token']

       def refresh_access_token(self):
           """Refresh expired access token"""
           response = requests.post(
               f'{self.base_url}/auth/refresh',
               json={'refresh_token': self.refresh_token}
           )
           data = response.json()
           self.access_token = data['access_token']

       def _get_headers(self):
           """Get headers with auth token"""
           return {'Authorization': f'Bearer {self.access_token}'}

       def query(self, gremlin_query):
           """Execute query with authentication"""
           try:
               response = requests.post(
                   f'{self.base_url}/query',
                   headers=self._get_headers(),
                   json={'query': gremlin_query}
               )
               return response.json()
           except requests.exceptions.HTTPError as e:
               if e.response.status_code == 401:
                   # Token expired, refresh and retry
                   self.refresh_access_token()
                   return self.query(gremlin_query)
               raise
   ```

2. **Store Tokens Securely**:
   - **DO NOT** store tokens in localStorage (XSS risk)
   - Use HTTP-only cookies for web applications
   - Use secure storage (Keychain/Keystore) for mobile apps
   - Use environment variables or secret managers for services

3. **Handle Token Expiration**:

   ```python
   def make_request_with_retry(self, method, endpoint, **kwargs):
       """Make request with automatic token refresh"""
       try:
           response = method(endpoint, **kwargs)
           response.raise_for_status()
           return response
       except requests.exceptions.HTTPError as e:
           if e.response.status_code == 401:
               # Token expired, refresh and retry
               self.refresh_access_token()
               kwargs['headers'] = self._get_headers()
               response = method(endpoint, **kwargs)
               response.raise_for_status()
               return response
           raise
   ```

---

### 2. Error Response Format

#### What Changed

- Standardized error response structure
- Added trace IDs for debugging
- More detailed error information

#### Before (v1.x)

```json
{
  "error": "Invalid query syntax"
}
```

#### After (v2.0)

```json
{
  "error": {
    "code": "INVALID_QUERY_SYNTAX",
    "message": "Invalid query syntax at line 1, column 5",
    "details": {
      "line": 1,
      "column": 5,
      "query": "g.V(.count()"
    },
    "trace_id": "abc123def456"
  }
}
```

#### Migration Steps

1. **Update Error Handling**:

   ```python
   # Before (v1.x)
   try:
       response = client.query(query)
   except Exception as e:
       print(f"Error: {e}")

   # After (v2.0)
   try:
       response = client.query(query)
   except requests.exceptions.HTTPError as e:
       error_data = e.response.json()
       error = error_data.get('error', {})
       print(f"Error [{error.get('code')}]: {error.get('message')}")
       print(f"Trace ID: {error.get('trace_id')}")
       if 'details' in error:
           print(f"Details: {error['details']}")
   ```

2. **Log Trace IDs**:

   ```python
   import logging

   logger = logging.getLogger(__name__)

   try:
       response = client.query(query)
   except requests.exceptions.HTTPError as e:
       error = e.response.json().get('error', {})
       logger.error(
           f"Query failed: {error.get('message')}",
           extra={
               'trace_id': error.get('trace_id'),
               'error_code': error.get('code'),
               'error_details': error.get('details')
           }
       )
   ```

---

### 3. HTTPS Required

#### What Changed

- HTTP endpoints removed
- All communication must use HTTPS
- TLS 1.2+ required

#### Migration Steps

1. **Update Base URLs**:

   ```python
   # Before
   BASE_URL = 'http://localhost:8080'

   # After
   BASE_URL = 'https://localhost:8443'
   ```

2. **Configure TLS Certificates**:

   ```python
   import requests

   # For development with self-signed certificates
   response = requests.get(
       'https://localhost:8443/health',
       verify='/path/to/ca-cert.pem'  # Or False for dev only
   )

   # For production
   response = requests.get(
       'https://api.example.com/health',
       verify=True  # Always verify in production
   )
   ```

---

### 4. Pagination Changes

#### What Changed

- Standardized pagination format
- Added total count and page information

#### Before (v1.x)

```json
{
  "vertices": [...],
  "has_more": true
}
```

#### After (v2.0)

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 100,
    "total_pages": 10,
    "total_items": 1000,
    "has_next": true,
    "has_previous": false
  }
}
```

#### Migration Steps

```python
# Before (v1.x)
def get_all_vertices(client):
    all_vertices = []
    page = 1
    while True:
        response = client.get(f'/graph/vertices?page={page}')
        all_vertices.extend(response['vertices'])
        if not response['has_more']:
            break
        page += 1
    return all_vertices

# After (v2.0)
def get_all_vertices(client):
    all_vertices = []
    page = 1
    while True:
        response = client.get(f'/graph/vertices?page={page}')
        all_vertices.extend(response['data'])
        if not response['pagination']['has_next']:
            break
        page += 1
    return all_vertices
```

---

## New Features to Adopt

### 1. Query Caching

Take advantage of automatic query caching:

```python
# Queries are automatically cached
response = client.query("g.V().count()")

# Check cache status
cache_status = response.headers.get('X-Cache-Status')  # HIT or MISS

# Force cache refresh
response = client.query(
    "g.V().count()",
    headers={'X-Cache-Control': 'no-cache'}
)
```

### 2. Rate Limiting

Monitor rate limits:

```python
response = client.query("g.V().count()")

# Check rate limit headers
limit = response.headers.get('X-RateLimit-Limit')
remaining = response.headers.get('X-RateLimit-Remaining')
reset = response.headers.get('X-RateLimit-Reset')

print(f"Rate limit: {remaining}/{limit} remaining")
print(f"Resets at: {reset}")

# Handle rate limiting
if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 60))
    print(f"Rate limited. Retry after {retry_after} seconds")
    time.sleep(retry_after)
```

### 3. Distributed Tracing

Include trace context in requests:

```python
import uuid

# Generate trace ID
trace_id = str(uuid.uuid4())

# Include in request
response = client.query(
    "g.V().count()",
    headers={'X-Trace-Id': trace_id}
)

# Use trace ID for debugging
print(f"Request trace ID: {trace_id}")
```

### 4. Multi-Factor Authentication

Enable MFA for enhanced security:

```python
# Enroll in MFA
response = client.post('/auth/mfa/enroll')
qr_code = response.json()['qr_code']
backup_codes = response.json()['backup_codes']

# Save backup codes securely
print("Backup codes:", backup_codes)

# Login with MFA
auth_response = client.post('/auth/login', json={
    'username': 'user',
    'password': 'pass',
    'mfa_token': '123456'  # From authenticator app
})
```

---

## Migration Checklist

### Pre-Migration

- [ ] Review breaking changes
- [ ] Identify affected code
- [ ] Set up v2.0 test environment
- [ ] Back up existing data
- [ ] Plan rollback strategy

### Code Changes

- [ ] Update authentication to JWT
- [ ] Update error handling
- [ ] Change HTTP to HTTPS
- [ ] Update pagination logic
- [ ] Add token refresh logic
- [ ] Update base URLs

### Testing

- [ ] Test authentication flow
- [ ] Test token refresh
- [ ] Test error handling
- [ ] Test pagination
- [ ] Test rate limiting
- [ ] Load testing
- [ ] Security testing

### Deployment

- [ ] Deploy to staging
- [ ] Run integration tests
- [ ] Monitor for issues
- [ ] Deploy to production
- [ ] Monitor metrics
- [ ] Update documentation

### Post-Migration

- [ ] Verify all features working
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Gather user feedback
- [ ] Document lessons learned

---

## Common Issues and Solutions

### Issue 1: 401 Unauthorized

**Symptom**: All requests return 401 Unauthorized

**Solution**:

```python
# Ensure token is included in headers
headers = {'Authorization': f'Bearer {access_token}'}

# Check token expiration
import jwt
decoded = jwt.decode(access_token, options={"verify_signature": False})
print(f"Token expires at: {decoded['exp']}")

# Refresh if expired
if time.time() > decoded['exp']:
    client.refresh_access_token()
```

### Issue 2: SSL Certificate Errors

**Symptom**: SSL verification fails

**Solution**:

```python
# For development (NOT for production)
import urllib3
urllib3.disable_warnings()
response = requests.get(url, verify=False)

# For production - use proper certificates
response = requests.get(url, verify='/path/to/ca-bundle.crt')
```

### Issue 3: Rate Limiting

**Symptom**: 429 Too Many Requests

**Solution**:

```python
import time
from functools import wraps

def retry_on_rate_limit(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:
                        retry_after = int(e.response.headers.get('Retry-After', 60))
                        if attempt < max_retries - 1:
                            time.sleep(retry_after)
                            continue
                    raise
        return wrapper
    return decorator

@retry_on_rate_limit()
def make_query(query):
    return client.query(query)
```

---

## Performance Optimization

### Enable Caching

```python
# Cache frequently used queries
common_queries = [
    "g.V().count()",
    "g.E().count()",
    "g.V().hasLabel('user').count()"
]

# Warm cache on startup
for query in common_queries:
    client.query(query)
```

### Batch Operations

```python
# Instead of multiple single operations
for vertex_data in vertices:
    client.create_vertex(vertex_data)  # Slow

# Use batch operations
client.create_vertices_batch(vertices)  # Fast
```

### Connection Pooling

```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.3)
adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
session.mount('https://', adapter)

# Use session for all requests
response = session.get(url, headers=headers)
```

---

## Support

### Getting Help

- **Documentation**: [docs/api/](../api/)
- **Migration Issues**: [GitHub Issues](https://github.com/your-org/hcd-janusgraph/issues)
- **Email**: <support@example.com>
- **Slack**: #janusgraph-migration

### Reporting Problems

When reporting migration issues, include:

1. v1.x version you're migrating from
2. Error messages and stack traces
3. Code snippets showing the issue
4. Steps to reproduce
5. Expected vs actual behavior

---

## Timeline

### Recommended Migration Schedule

- **Week 1**: Review changes, update test environment
- **Week 2**: Update code, run tests
- **Week 3**: Deploy to staging, integration testing
- **Week 4**: Production deployment, monitoring

### Support Timeline

- **v1.x Support**: Security fixes only until 2026-06-01
- **v2.0 Support**: Full support, current version
- **Migration Assistance**: Available until 2026-04-01

---

**Last Updated**: 2026-01-28
**Version**: 2.0.0
