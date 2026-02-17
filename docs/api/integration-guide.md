# API Integration Guide

## Overview

This guide provides practical examples and best practices for integrating with the HCD JanusGraph API. It covers common use cases, code examples in multiple languages, and integration patterns.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Python Integration](#python-integration)
4. [Error Handling](#error-handling)
5. [Performance Optimization](#performance-optimization)
6. [Production Best Practices](#production-best-practices)

---

## Quick Start

### Prerequisites

- JanusGraph server running on `localhost:18182`
- Python 3.8+
- Network access to the graph database

### Installation

**Python:**

```bash
pip install gremlinpython requests
```

---

## Authentication

### API Key Authentication

```python
import requests

headers = {
    'X-API-Key': 'your-api-key-here',
    'Content-Type': 'application/json'
}

response = requests.get(
    'https://api.example.com/v1/health',
    headers=headers
)
```

### JWT Token Authentication

```python
import requests
import jwt
from datetime import datetime, timedelta

def generate_token(secret_key, user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, secret_key, algorithm='HS256')

token = generate_token('your-secret-key', 'user123')
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}
```

---

## Python Integration

### Complete Example: Social Network

```python
#!/usr/bin/env python3
"""Social Network Graph Example"""

from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.traversal import P
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SocialNetworkGraph:
    """Social network graph operations."""

    def __init__(self, host='localhost', port=8182):
        self.connection_url = f'ws://{host}:{port}/gremlin'
        self.connection = None
        self.g = None

    def connect(self):
        """Establish connection to graph database."""
        try:
            self.connection = DriverRemoteConnection(
                self.connection_url, 'g'
            )
            self.g = traversal().with_remote(self.connection)
            logger.info("Connected to JanusGraph")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise

    def disconnect(self):
        """Close connection."""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from JanusGraph")

    def create_user(self, name, age, email, city):
        """Create a new user vertex."""
        try:
            user = self.g.addV('user') \
                .property('name', name) \
                .property('age', age) \
                .property('email', email) \
                .property('city', city) \
                .next()
            logger.info(f"Created user: {name}")
            return user.id
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise

    def create_friendship(self, user1_id, user2_id, since):
        """Create friendship edge between users."""
        try:
            edge = self.g.V(user1_id).addE('knows') \
                .to(self.g.V(user2_id)) \
                .property('since', since) \
                .next()
            logger.info(f"Created friendship: {user1_id} -> {user2_id}")
            return edge.id
        except Exception as e:
            logger.error(f"Failed to create friendship: {e}")
            raise

    def find_friends(self, user_id):
        """Find all friends of a user."""
        try:
            friends = self.g.V(user_id) \
                .out('knows') \
                .valueMap(True) \
                .toList()
            return friends
        except Exception as e:
            logger.error(f"Failed to find friends: {e}")
            raise

    def find_mutual_friends(self, user1_id, user2_id):
        """Find mutual friends between two users."""
        try:
            mutual = self.g.V(user1_id) \
                .out('knows').as_('friend') \
                .where(self.g.__.in_('knows').hasId(user2_id)) \
                .select('friend') \
                .valueMap(True) \
                .toList()
            return mutual
        except Exception as e:
            logger.error(f"Failed to find mutual friends: {e}")
            raise

    def recommend_friends(self, user_id, limit=5):
        """Recommend friends based on friend-of-friend."""
        try:
            recommendations = self.g.V(user_id) \
                .out('knows').aggregate('friends') \
                .out('knows') \
                .where(P.neq(user_id)) \
                .where(P.without('friends')) \
                .groupCount() \
                .order(self.g.__.local).by(self.g.__.values, self.g.__.desc) \
                .limit(self.g.__.local, limit) \
                .unfold() \
                .toList()
            return recommendations
        except Exception as e:
            logger.error(f"Failed to recommend friends: {e}")
            raise


# Usage Example
def main():
    graph = SocialNetworkGraph()

    try:
        graph.connect()

        # Create users
        alice_id = graph.create_user('Alice', 28, 'alice@example.com', 'NYC')
        bob_id = graph.create_user('Bob', 32, 'bob@example.com', 'NYC')
        charlie_id = graph.create_user('Charlie', 25, 'charlie@example.com', 'LA')

        # Create friendships
        graph.create_friendship(alice_id, bob_id, 2020)
        graph.create_friendship(bob_id, charlie_id, 2021)

        # Query friends
        alice_friends = graph.find_friends(alice_id)
        print(f"Alice's friends: {alice_friends}")

        # Find recommendations
        recommendations = graph.recommend_friends(alice_id)
        print(f"Friend recommendations for Alice: {recommendations}")

    finally:
        graph.disconnect()


if __name__ == '__main__':
    main()
```

---

## Error Handling

### Comprehensive Error Handling

```python
from gremlin_python.driver.protocol import GremlinServerError
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
import logging

logger = logging.getLogger(__name__)


class GraphOperationError(Exception):
    """Custom exception for graph operations."""
    pass


def safe_graph_operation(func):
    """Decorator for safe graph operations with retry logic."""
    def wrapper(*args, **kwargs):
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                return func(*args, **kwargs)
            except GremlinServerError as e:
                logger.error(f"Gremlin server error: {e}")
                if e.status_code == 500:
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.info(f"Retrying... ({retry_count}/{max_retries})")
                        continue
                raise GraphOperationError(f"Graph operation failed: {e}")
            except ConnectionError as e:
                logger.error(f"Connection error: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"Retrying connection... ({retry_count}/{max_retries})")
                    continue
                raise GraphOperationError(f"Connection failed after {max_retries} retries")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise GraphOperationError(f"Unexpected error: {e}")

        raise GraphOperationError(f"Operation failed after {max_retries} retries")

    return wrapper


@safe_graph_operation
def create_vertex_safe(g, label, properties):
    """Safely create a vertex with error handling."""
    vertex = g.addV(label)
    for key, value in properties.items():
        vertex = vertex.property(key, value)
    return vertex.next()
```

---

## Performance Optimization

### Connection Pooling

```python
from gremlin_python.driver import client, serializer
from contextlib import contextmanager


class GraphConnectionPool:
    """Connection pool for graph database."""

    def __init__(self, host='localhost', port=8182, pool_size=10):
        self.client = client.Client(
            f'ws://{host}:{port}/gremlin',
            'g',
            pool_size=pool_size,
            message_serializer=serializer.GraphSONSerializersV3d0()
        )

    @contextmanager
    def get_connection(self):
        """Get connection from pool."""
        try:
            yield self.client
        finally:
            pass  # Connection returned to pool automatically

    def close(self):
        """Close all connections."""
        self.client.close()


# Usage
pool = GraphConnectionPool(pool_size=20)

with pool.get_connection() as client:
    result = client.submit("g.V().count()").all().result()
    print(f"Vertex count: {result[0]}")

pool.close()
```

### Batch Operations

```python
def batch_create_vertices(g, vertices_data, batch_size=100):
    """Create vertices in batches for better performance."""
    results = []

    for i in range(0, len(vertices_data), batch_size):
        batch = vertices_data[i:i + batch_size]

        # Create batch traversal
        traversal = g
        for vertex_data in batch:
            traversal = traversal.addV(vertex_data['label'])
            for key, value in vertex_data['properties'].items():
                traversal = traversal.property(key, value)

        # Execute batch
        batch_results = traversal.toList()
        results.extend(batch_results)

    return results
```

### Query Optimization

```python
# Bad: Multiple round trips
def get_user_details_slow(g, user_id):
    user = g.V(user_id).next()
    friends = g.V(user_id).out('knows').toList()
    posts = g.V(user_id).out('posted').toList()
    return user, friends, posts


# Good: Single query with projections
def get_user_details_fast(g, user_id):
    result = g.V(user_id).project('user', 'friends', 'posts') \
        .by(valueMap(True)) \
        .by(out('knows').valueMap(True).fold()) \
        .by(out('posted').valueMap(True).fold()) \
        .next()
    return result
```

---

## Production Best Practices

### Configuration Management

```python
import os
from dataclasses import dataclass


@dataclass
class GraphConfig:
    """Graph database configuration."""
    host: str = os.getenv('GRAPH_HOST', 'localhost')
    port: int = int(os.getenv('GRAPH_PORT', '8182'))
    username: str = os.getenv('GRAPH_USERNAME', '')
    password: str = os.getenv('GRAPH_PASSWORD', '')
    pool_size: int = int(os.getenv('GRAPH_POOL_SIZE', '10'))
    timeout: int = int(os.getenv('GRAPH_TIMEOUT', '30'))
    use_ssl: bool = os.getenv('GRAPH_USE_SSL', 'false').lower() == 'true'


config = GraphConfig()
```

### Health Checks

```python
def check_graph_health(g):
    """Check if graph database is healthy."""
    try:
        # Simple query to test connectivity
        count = g.V().limit(1).count().next()
        return True, "Graph database is healthy"
    except Exception as e:
        return False, f"Graph database is unhealthy: {e}"


# Usage in health endpoint
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    is_healthy, message = check_graph_health(g)
    status_code = 200 if is_healthy else 503
    return jsonify({
        'status': 'healthy' if is_healthy else 'unhealthy',
        'message': message
    }), status_code
```

### Monitoring and Metrics

```python
import time
from functools import wraps


def track_query_time(func):
    """Decorator to track query execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    return wrapper


@track_query_time
def complex_query(g):
    """Example of tracked query."""
    return g.V().out().out().count().next()
```

### Graceful Shutdown

```python
import signal
import sys


class GraphApplication:
    """Application with graceful shutdown."""

    def __init__(self):
        self.connection = None
        self.running = True

        # Register signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum, frame):
        """Graceful shutdown handler."""
        logger.info("Shutting down gracefully...")
        self.running = False

        if self.connection:
            self.connection.close()
            logger.info("Connection closed")

        sys.exit(0)

    def run(self):
        """Main application loop."""
        self.connection = DriverRemoteConnection(
            'ws://localhost:18182/gremlin', 'g'
        )

        while self.running:
            # Application logic here
            time.sleep(1)


if __name__ == '__main__':
    app = GraphApplication()
    app.run()
```

---

## Additional Resources

- [OpenAPI Specification](./openapi.yaml)
- [Gremlin API Reference](./gremlin-api.md)
- [JanusGraph Documentation](https://docs.janusgraph.org/)
- [Apache TinkerPop](https://tinkerpop.apache.org/)

---

## Support

For issues or questions:

- GitHub Issues: [Project Repository]
- Email: <support@example.com>
- Documentation: [Project Wiki]
