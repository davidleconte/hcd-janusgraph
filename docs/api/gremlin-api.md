# Gremlin Query API Reference

## Overview

This document provides comprehensive documentation for the Gremlin query API in the HCD JanusGraph project. Gremlin is a graph traversal language that allows you to query and manipulate graph data.

## Table of Contents

1. [Connection](#connection)
2. [Basic Traversals](#basic-traversals)
3. [Vertex Operations](#vertex-operations)
4. [Edge Operations](#edge-operations)
5. [Filtering](#filtering)
6. [Aggregation](#aggregation)
7. [Path Traversals](#path-traversals)
8. [Advanced Patterns](#advanced-patterns)
9. [Performance Optimization](#performance-optimization)
10. [Best Practices](#best-practices)

---

## Connection

### Python Client

```python
from gremlin_python.driver import client, serializer
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

# Connect to JanusGraph
connection = DriverRemoteConnection(
    'ws://localhost:18182/gremlin',
    'g'
)

# Create traversal source
g = traversal().with_remote(connection)

# Execute queries
results = g.V().limit(10).toList()

# Close connection
connection.close()
```

### Using Client API

```python
# Alternative: Using client API for raw Gremlin strings
gremlin_client = client.Client(
    'ws://localhost:18182/gremlin',
    'g',
    message_serializer=serializer.GraphSONSerializersV3d0()
)

# Execute Gremlin query
result = gremlin_client.submit("g.V().count()").all().result()

# Close client
gremlin_client.close()
```

---

## Basic Traversals

### Count Vertices

```python
# Count all vertices
count = g.V().count().next()

# Count vertices by label
person_count = g.V().hasLabel('person').count().next()
```

**Gremlin String:**

```groovy
g.V().count()
g.V().hasLabel('person').count()
```

### Count Edges

```python
# Count all edges
edge_count = g.E().count().next()

# Count edges by label
knows_count = g.E().hasLabel('knows').count().next()
```

**Gremlin String:**

```groovy
g.E().count()
g.E().hasLabel('knows').count()
```

### Get All Vertices

```python
# Get first 100 vertices
vertices = g.V().limit(100).toList()

# Get vertices with properties
vertices = g.V().limit(10).valueMap(True).toList()
```

**Gremlin String:**

```groovy
g.V().limit(100)
g.V().limit(10).valueMap(true)
```

---

## Vertex Operations

### Create Vertex

```python
# Create a person vertex
person = g.addV('person') \
    .property('name', 'John Doe') \
    .property('age', 30) \
    .property('email', 'john@example.com') \
    .next()

# Get vertex ID
vertex_id = person.id
```

**Gremlin String:**

```groovy
g.addV('person')
    .property('name', 'John Doe')
    .property('age', 30)
    .property('email', 'john@example.com')
```

### Read Vertex

```python
# Get vertex by ID
vertex = g.V(vertex_id).next()

# Get vertex with all properties
vertex_props = g.V(vertex_id).valueMap(True).next()

# Get specific properties
name = g.V(vertex_id).values('name').next()
```

**Gremlin String:**

```groovy
g.V(vertex_id)
g.V(vertex_id).valueMap(true)
g.V(vertex_id).values('name')
```

### Update Vertex

```python
# Update single property
g.V(vertex_id).property('age', 31).iterate()

# Update multiple properties
g.V(vertex_id) \
    .property('age', 31) \
    .property('city', 'New York') \
    .iterate()

# Add property to list (multi-cardinality)
g.V(vertex_id).property(list, 'phone', '+1234567890').iterate()
```

**Gremlin String:**

```groovy
g.V(vertex_id).property('age', 31)
g.V(vertex_id)
    .property('age', 31)
    .property('city', 'New York')
g.V(vertex_id).property(list, 'phone', '+1234567890')
```

### Delete Vertex

```python
# Delete vertex and all its edges
g.V(vertex_id).drop().iterate()

# Delete all vertices with a label
g.V().hasLabel('temp').drop().iterate()
```

**Gremlin String:**

```groovy
g.V(vertex_id).drop()
g.V().hasLabel('temp').drop()
```

---

## Edge Operations

### Create Edge

```python
# Create edge between two vertices
edge = g.V(person1_id).addE('knows') \
    .to(g.V(person2_id)) \
    .property('since', 2020) \
    .property('weight', 0.8) \
    .next()

# Alternative: Using from/to
edge = g.addE('knows') \
    .from_(g.V(person1_id)) \
    .to(g.V(person2_id)) \
    .property('since', 2020) \
    .next()
```

**Gremlin String:**

```groovy
g.V(person1_id).addE('knows')
    .to(V(person2_id))
    .property('since', 2020)
    .property('weight', 0.8)

g.addE('knows')
    .from(V(person1_id))
    .to(V(person2_id))
    .property('since', 2020)
```

### Read Edge

```python
# Get edge by ID
edge = g.E(edge_id).next()

# Get edge with properties
edge_props = g.E(edge_id).valueMap(True).next()

# Get outgoing edges from vertex
out_edges = g.V(vertex_id).outE().toList()

# Get incoming edges to vertex
in_edges = g.V(vertex_id).inE().toList()

# Get all edges (both directions)
all_edges = g.V(vertex_id).bothE().toList()
```

**Gremlin String:**

```groovy
g.E(edge_id)
g.E(edge_id).valueMap(true)
g.V(vertex_id).outE()
g.V(vertex_id).inE()
g.V(vertex_id).bothE()
```

### Update Edge

```python
# Update edge property
g.E(edge_id).property('weight', 0.9).iterate()
```

**Gremlin String:**

```groovy
g.E(edge_id).property('weight', 0.9)
```

### Delete Edge

```python
# Delete specific edge
g.E(edge_id).drop().iterate()

# Delete all edges of a type
g.E().hasLabel('temp_relation').drop().iterate()

# Delete edges between two vertices
g.V(person1_id).outE('knows').where(inV().hasId(person2_id)).drop().iterate()
```

**Gremlin String:**

```groovy
g.E(edge_id).drop()
g.E().hasLabel('temp_relation').drop()
g.V(person1_id).outE('knows').where(inV().hasId(person2_id)).drop()
```

---

## Filtering

### Has Step

```python
# Filter by property existence
persons = g.V().has('email').toList()

# Filter by property value
johns = g.V().has('name', 'John').toList()

# Filter by label and property
adults = g.V().hasLabel('person').has('age', gt(18)).toList()

# Multiple conditions
results = g.V().hasLabel('person') \
    .has('age', between(25, 35)) \
    .has('city', 'New York') \
    .toList()
```

**Gremlin String:**

```groovy
g.V().has('email')
g.V().has('name', 'John')
g.V().hasLabel('person').has('age', gt(18))
g.V().hasLabel('person')
    .has('age', between(25, 35))
    .has('city', 'New York')
```

### Predicates

```python
from gremlin_python.process.traversal import P

# Comparison predicates
g.V().has('age', P.gt(30)).toList()          # Greater than
g.V().has('age', P.gte(30)).toList()         # Greater than or equal
g.V().has('age', P.lt(30)).toList()          # Less than
g.V().has('age', P.lte(30)).toList()         # Less than or equal
g.V().has('age', P.eq(30)).toList()          # Equal
g.V().has('age', P.neq(30)).toList()         # Not equal

# Range predicates
g.V().has('age', P.between(25, 35)).toList() # Between (exclusive)
g.V().has('age', P.inside(25, 35)).toList()  # Inside (exclusive)
g.V().has('age', P.outside(25, 35)).toList() # Outside

# Collection predicates
g.V().has('name', P.within(['John', 'Jane', 'Bob'])).toList()
g.V().has('name', P.without(['Admin', 'System'])).toList()

# String predicates
g.V().has('name', P.startingWith('J')).toList()
g.V().has('name', P.endingWith('son')).toList()
g.V().has('name', P.containing('oh')).toList()

# Logical predicates
g.V().has('age', P.gt(25).and_(P.lt(35))).toList()
g.V().has('status', P.eq('active').or_(P.eq('pending'))).toList()
```

**Gremlin String:**

```groovy
g.V().has('age', gt(30))
g.V().has('age', between(25, 35))
g.V().has('name', within('John', 'Jane', 'Bob'))
g.V().has('name', startingWith('J'))
g.V().has('age', gt(25).and(lt(35)))
```

### Where Step

```python
# Filter based on traversal
results = g.V().hasLabel('person') \
    .where(out('knows').has('name', 'John')) \
    .toList()

# Filter with by modulator
results = g.V().hasLabel('person').as_('a') \
    .out('knows').as_('b') \
    .where('a', P.neq('b')) \
    .select('a', 'b') \
    .toList()
```

**Gremlin String:**

```groovy
g.V().hasLabel('person')
    .where(out('knows').has('name', 'John'))

g.V().hasLabel('person').as('a')
    .out('knows').as('b')
    .where('a', neq('b'))
    .select('a', 'b')
```

---

## Aggregation

### Group

```python
# Group by property
age_groups = g.V().hasLabel('person') \
    .group().by('age').by(count()) \
    .next()

# Group with value extraction
city_names = g.V().hasLabel('person') \
    .group().by('city').by(values('name').fold()) \
    .next()
```

**Gremlin String:**

```groovy
g.V().hasLabel('person')
    .group().by('age').by(count())

g.V().hasLabel('person')
    .group().by('city').by(values('name').fold())
```

### GroupCount

```python
# Count occurrences
label_counts = g.V().groupCount().by(label).next()
age_distribution = g.V().hasLabel('person').groupCount().by('age').next()
```

**Gremlin String:**

```groovy
g.V().groupCount().by(label)
g.V().hasLabel('person').groupCount().by('age')
```

### Statistics

```python
# Sum
total_age = g.V().hasLabel('person').values('age').sum().next()

# Mean
avg_age = g.V().hasLabel('person').values('age').mean().next()

# Min/Max
min_age = g.V().hasLabel('person').values('age').min().next()
max_age = g.V().hasLabel('person').values('age').max().next()
```

**Gremlin String:**

```groovy
g.V().hasLabel('person').values('age').sum()
g.V().hasLabel('person').values('age').mean()
g.V().hasLabel('person').values('age').min()
g.V().hasLabel('person').values('age').max()
```

---

## Path Traversals

### Simple Paths

```python
# Find paths between two vertices
paths = g.V(start_id).repeat(out().simplePath()) \
    .until(hasId(end_id)) \
    .path() \
    .limit(10) \
    .toList()

# Find shortest path
shortest = g.V(start_id).repeat(out().simplePath()) \
    .until(hasId(end_id)) \
    .path() \
    .limit(1) \
    .next()
```

**Gremlin String:**

```groovy
g.V(start_id).repeat(out().simplePath())
    .until(hasId(end_id))
    .path()
    .limit(10)
```

### Path with Filtering

```python
# Find paths with specific edge types
paths = g.V(start_id) \
    .repeat(outE('knows', 'works_with').inV().simplePath()) \
    .until(hasId(end_id)) \
    .path() \
    .toList()
```

**Gremlin String:**

```groovy
g.V(start_id)
    .repeat(outE('knows', 'works_with').inV().simplePath())
    .until(hasId(end_id))
    .path()
```

### Cycle Detection

```python
# Find cycles
cycles = g.V().as_('start') \
    .repeat(out().simplePath()) \
    .times(3) \
    .where(out().as_('start')) \
    .path() \
    .toList()
```

**Gremlin String:**

```groovy
g.V().as('start')
    .repeat(out().simplePath())
    .times(3)
    .where(out().as('start'))
    .path()
```

---

## Advanced Patterns

### Recommendation Engine

```python
# Friend-of-friend recommendations
recommendations = g.V(user_id) \
    .out('knows').aggregate('friends') \
    .out('knows') \
    .where(P.neq(user_id)) \
    .where(P.without('friends')) \
    .groupCount() \
    .order(local).by(values, desc) \
    .limit(local, 10) \
    .next()
```

**Gremlin String:**

```groovy
g.V(user_id)
    .out('knows').aggregate('friends')
    .out('knows')
    .where(neq(user_id))
    .where(without('friends'))
    .groupCount()
    .order(local).by(values, desc)
    .limit(local, 10)
```

### PageRank

```python
# Calculate PageRank
pagerank = g.V().pageRank().by('pagerank').toList()

# Get top ranked vertices
top_ranked = g.V().order().by('pagerank', desc).limit(10).toList()
```

**Gremlin String:**

```groovy
g.V().pageRank().by('pagerank')
g.V().order().by('pagerank', desc).limit(10)
```

### Community Detection

```python
# Connected components
components = g.V().connectedComponent().by('component').toList()

# Group by component
communities = g.V().groupCount().by('component').next()
```

**Gremlin String:**

```groovy
g.V().connectedComponent().by('component')
g.V().groupCount().by('component')
```

### Pattern Matching

```python
# Find triangles (3-node cycles)
triangles = g.V().as_('a') \
    .out().as_('b') \
    .out().as_('c') \
    .out().as_('a') \
    .select('a', 'b', 'c') \
    .dedup() \
    .toList()
```

**Gremlin String:**

```groovy
g.V().as('a')
    .out().as('b')
    .out().as('c')
    .out().as('a')
    .select('a', 'b', 'c')
    .dedup()
```

---

## Performance Optimization

### Indexing

```python
# Use indexed properties for filtering
# Ensure properties used in has() are indexed
results = g.V().has('email', 'john@example.com').toList()  # Fast with index
```

### Limit Early

```python
# Bad: Limit after expensive operations
bad = g.V().out().out().out().limit(10).toList()

# Good: Limit early when possible
good = g.V().limit(100).out().out().out().limit(10).toList()
```

### Batch Operations

```python
# Bad: Multiple individual operations
for item in items:
    g.addV('person').property('name', item).iterate()

# Good: Batch in single traversal
g.inject(items).unfold() \
    .addV('person').property('name', __) \
    .iterate()
```

### Use Barriers

```python
# Use barrier() to force evaluation
results = g.V().out().barrier().out().toList()
```

---

## Best Practices

### 1. Always Close Connections

```python
try:
    connection = DriverRemoteConnection('ws://localhost:18182/gremlin', 'g')
    g = traversal().with_remote(connection)
    # Your queries here
finally:
    connection.close()
```

### 2. Use Context Managers

```python
from contextlib import contextmanager

@contextmanager
def graph_connection():
    connection = DriverRemoteConnection('ws://localhost:18182/gremlin', 'g')
    try:
        yield traversal().with_remote(connection)
    finally:
        connection.close()

# Usage
with graph_connection() as g:
    results = g.V().limit(10).toList()
```

### 3. Handle Errors

```python
from gremlin_python.driver.protocol import GremlinServerError

try:
    result = g.V(invalid_id).next()
except GremlinServerError as e:
    print(f"Query error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 4. Use Parameterized Queries

```python
# Bad: String concatenation (SQL injection risk)
name = user_input
results = g.V().has('name', name).toList()  # Safe in Python API

# For raw Gremlin strings, use bindings
query = "g.V().has('name', username)"
bindings = {'username': user_input}
result = client.submit(query, bindings).all().result()
```

### 5. Profile Queries

```python
# Profile query execution
profile = g.V().out().out().profile().next()
print(profile)
```

### 6. Use Explain

```python
# Explain query execution plan
explain = g.V().has('name', 'John').out('knows').explain()
print(explain)
```

---

## Common Patterns

### Find Mutual Friends

```python
mutual_friends = g.V(user1_id).out('knows').as_('friend') \
    .where(__.in_('knows').hasId(user2_id)) \
    .select('friend') \
    .toList()
```

### Degree Centrality

```python
# Out-degree
out_degree = g.V(vertex_id).outE().count().next()

# In-degree
in_degree = g.V(vertex_id).inE().count().next()

# Total degree
total_degree = g.V(vertex_id).bothE().count().next()
```

### Subgraph Extraction

```python
# Extract subgraph around vertex
subgraph = g.V(vertex_id) \
    .repeat(bothE().otherV().simplePath()) \
    .times(2) \
    .path() \
    .toList()
```

---

## References

- [Apache TinkerPop Documentation](https://tinkerpop.apache.org/docs/current/reference/)
- [Gremlin Recipes](https://tinkerpop.apache.org/docs/current/recipes/)
- [JanusGraph Documentation](https://docs.janusgraph.org/)
- [Gremlin Python Documentation](https://tinkerpop.apache.org/docs/current/reference/#gremlin-python)

---

## Support

For issues or questions:

- GitHub Issues: [Project Repository]
- Email: <support@example.com>
- Documentation: [Project Wiki]
