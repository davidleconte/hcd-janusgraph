# Graph Visualization Tools

**Date:** 2026-02-04
**Status:** Active

This guide covers graph visualization options for the HCD + JanusGraph stack.

---

## Available Tools

### 1. JanusGraph Visualizer (Included)

**Status:** Included in docker-compose stack
**Port:** 3000
**License:** Open Source

The JanusGraph Visualizer is bundled with the project and starts automatically with the full stack deployment.

**Pros:**

- No additional installation required
- Embedded in Docker stack
- Works offline

**Cons:**

- May show as "unhealthy" (cosmetic issue)
- Limited features compared to commercial tools
- Runs in container (slower than native apps)

**Access:**

```bash
open http://localhost:3000
```

---

### 2. GraphExp (Included)

**Status:** Included in docker-compose stack
**Port:** 8183
**License:** Open Source

GraphExp is another open-source graph explorer included in the stack.

**Access:**

```bash
open http://localhost:8183
```

---

### 3. G.V() (Recommended for Development)

**Status:** External tool (download separately)
**License:** Commercial (free trial available)
**Website:** [gdotv.com](https://gdotv.com/janusgraph-visualization-tool/)

G.V() is a professional Gremlin graph visualization tool with native support for JanusGraph.

**Pros:**

- ✅ Native macOS Apple Silicon support (M1/M2/M3)
- ✅ Advanced query editor with autocomplete
- ✅ Full schema exploration
- ✅ Fast native performance (no container overhead)
- ✅ Polished UI for daily development
- ✅ Query history and saved queries

**Cons:**

- Requires separate download
- Commercial license for full features
- Not embedded in stack (external dependency)

#### Installation (macOS Apple Silicon)

1. Download from [gdotv.com/gremlin-graph-visualization-tool](https://gdotv.com/gremlin-graph-visualization-tool/)
2. Choose **macOS Apple Silicon** version
3. Install the application

#### Connection Configuration

```
Connection URL: ws://localhost:18182/gremlin
Traversal Source: g
SSL/TLS: Disabled (for local development)
```

**Note:** The port `18182` is the externally mapped port from the podman/docker compose configuration.

#### Sample Queries to Test

```groovy
// Count all vertices
g.V().count()

// List vertex labels
g.V().label().dedup()

// List edge labels
g.E().label().dedup()

// Find persons
g.V().hasLabel('Person').limit(10)

// Find transactions
g.V().hasLabel('Transaction').limit(10)
```

---

## Recommended Setup

| Use Case | Tool |
|----------|------|
| Daily development | G.V() (native, fast) |
| Demos/workshops | JanusGraph Visualizer (embedded) |
| Quick exploration | GraphExp (embedded) |
| CI/CD testing | Gremlin CLI (headless) |

---

## Troubleshooting

### G.V() Connection Issues

**Problem:** Cannot connect to `ws://localhost:18182/gremlin`

**Solutions:**

1. Verify JanusGraph is running: `podman ps | grep janusgraph`
2. Check port mapping: `podman port janusgraph-demo_janusgraph-server_1`
3. Ensure `JANUSGRAPH_USE_SSL=false` for local development

### JanusGraph Visualizer Shows Unhealthy

**Problem:** Container shows as "unhealthy" in `podman ps`

**Solution:** This is a known cosmetic issue. The visualizer may still work - try accessing `http://localhost:3000`. The healthcheck is overly strict.

---

## See Also

- [JanusGraph Documentation](https://docs.janusgraph.org/)
- [Gremlin Language Reference](https://tinkerpop.apache.org/gremlin.html)
- [G.V() User Guide](https://gdotv.com/docs/)
