# Frequently Asked Questions (FAQ)

**Last Updated:** 2026-02-06
**Owner:** Documentation Team

---

## Table of Contents

1. [Setup & Installation](#setup--installation)
2. [JanusGraph & Gremlin](#janusgraph--gremlin)
3. [OpenSearch & Vector Search](#opensearch--vector-search)
4. [Streaming & Pulsar](#streaming--pulsar)
5. [Testing](#testing)
6. [Security](#security)
7. [Performance](#performance)
8. [Notebooks](#notebooks)

---

## Setup & Installation

### Q: How do I set up the development environment?

**A:** Use the conda environment:

```bash
conda env create -f environment.yml
conda activate janusgraph-analysis
```

The environment includes all dependencies and pre-configured environment variables.

### Q: Why do I need to run podman-compose from config/compose?

**A:** The compose files use relative paths for Dockerfiles. Running from the wrong directory causes path resolution errors:

```bash
# CORRECT
cd config/compose
FULL_STACK_FILE=<full-stack-compose-file>
podman-compose -p janusgraph-demo -f "$FULL_STACK_FILE" up -d

# WRONG - will fail with "Dockerfile not found"
FULL_STACK_FILE=config/compose/<full-stack-compose-file>
podman-compose -p janusgraph-demo -f "$FULL_STACK_FILE" up -d
```

### Q: How do I check if all services are running?

**A:** Use the preflight check script:

```bash
./scripts/validation/preflight_check.sh
```

Or manually:

```bash
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

## JanusGraph & Gremlin

### Q: What port does JanusGraph use?

**A:** Port `18182` (mapped from container's 8182). This is configured in the conda environment:

```bash
echo $JANUSGRAPH_PORT  # Should show: 18182
```

### Q: How do I connect to JanusGraph from Python?

**A:**

```python
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal

connection = DriverRemoteConnection('ws://localhost:18182/gremlin', 'g')
g = traversal().with_remote(connection)

# Verify connection
count = g.V().count().next()
print(f"Vertices: {count}")
```

### Q: Why does my Gremlin query timeout?

**A:** Complex traversals may exceed the default timeout. Solutions:

1. **Optimize the query**: Use indexes, limit traversal depth
2. **Increase timeout**: Set `scriptEvaluationTimeout` in JanusGraph config
3. **Use pagination**: `.range(0, 100)` instead of fetching all results

See [Troubleshooting Guide](banking/guides/troubleshooting-guide.md) for query optimization tips.

### Q: Does this project support OLAP queries?

**A:** Yes, but via **OpenSearch aggregations**, not Spark GraphComputer. This provides sub-second response times for slice/dice/drill-down/roll-up/pivot operations.

See [Advanced Analytics OLAP Guide](banking/guides/advanced-analytics-olap-guide.md) for details.

---

## OpenSearch & Vector Search

### Q: How do I disable SSL for local development?

**A:** The conda environment has this pre-configured:

```bash
echo $OPENSEARCH_USE_SSL  # Should show: false
```

### Q: How do I perform semantic search?

**A:**

```python
from opensearchpy import OpenSearch

client = OpenSearch(hosts=[{'host': 'localhost', 'port': 9200}], use_ssl=False)

# Vector search query
query = {
    "size": 10,
    "query": {
        "knn": {
            "embedding": {
                "vector": [0.1, 0.2, ...],  # Your embedding
                "k": 10
            }
        }
    }
}

response = client.search(index="sanctions_list", body=query)
```

### Q: What embedding model does this project use?

**A:** `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). It's lightweight and suitable for name matching.

---

## Streaming & Pulsar

### Q: How do I access Pulsar admin CLI?

**A:**

```bash
# List topics
podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-admin topics list public/banking

# Check topic stats
podman exec janusgraph-demo_pulsar-cli_1 bin/pulsar-admin topics stats persistent://public/banking/persons-events
```

### Q: What topics are available?

**A:** The banking namespace includes:

- `persons-events`
- `accounts-events`
- `transactions-events`
- `companies-events`
- `communications-events`
- `dlq` (Dead Letter Queue)

### Q: How do I test streaming without Pulsar?

**A:** Use mock producer:

```python
config = StreamingConfig(
    seed=42,
    person_count=100,
    use_mock_producer=True  # No actual Pulsar connection
)
```

---

## Testing

### Q: How do I run all tests?

**A:**

```bash
conda activate janusgraph-analysis
pytest tests/ -v --cov=src --cov=banking
```

### Q: Why do integration tests skip?

**A:** Integration tests use `pytest.skip()` when services aren't running. Deploy services first:

```bash
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
sleep 90  # Wait for services
pytest tests/integration/ -v
```

### Q: How do I run data generator tests?

**A:**

```bash
cd banking/data_generators/tests
./run_tests.sh [smoke|unit|integration|performance|coverage]
```

---

## Security

### Q: How do I change default passwords?

**A:** Edit `.env` and replace all placeholder values:

```bash
# .env
JANUSGRAPH_PASSWORD=YOUR_SECURE_PASSWORD_HERE  # CHANGE THIS
HCD_KEYSTORE_PASSWORD=your_strong_password     # CHANGE THIS
```

### Q: How do I access Vault secrets?

**A:**

```bash
source ./scripts/security/vault_access.sh
podman exec -e VAULT_TOKEN=$VAULT_APP_TOKEN vault-server vault kv get janusgraph/admin
```

### Q: Are SSL certificates pre-generated?

**A:** No. Generate them for your environment:

```bash
./scripts/security/generate_certificates.sh
```

---

## Performance

### Q: How do I monitor query performance?

**A:**

- **Grafana**: <http://localhost:3001> (admin/admin)
- **Prometheus**: <http://localhost:9090>
- **JanusGraph metrics**: <http://localhost:8000/metrics>

### Q: Why is my query slow?

**A:** Common causes:

1. **Missing indexes**: Check if properties are indexed
2. **Full graph scan**: Avoid `g.V()` without filters
3. **Large result sets**: Use `.limit()` or `.range()`

See [Troubleshooting Guide](banking/guides/troubleshooting-guide.md).

---

## Notebooks

### Q: Which kernel should I use?

**A:** "JanusGraph Analysis (Python 3.11)" - registered automatically with the conda environment.

### Q: Why does Notebook 08 (UBO) timeout?

**A:** Complex ownership traversals require manual execution or longer timeouts. Run interactively for best experience.

### Q: How do I run all notebooks programmatically?

**A:**

```bash
for nb in banking/notebooks/*.ipynb; do
    jupyter nbconvert --to notebook --execute "$nb" --ExecutePreprocessor.timeout=300
done
```

---

## Still Have Questions?

- Check [docs/INDEX.md](INDEX.md) for comprehensive documentation navigation
- Review [AGENTS.md](../AGENTS.md) for detailed project patterns
- Open an issue on GitHub for unresolved questions

---

*Last Updated: 2026-02-06*

### Q: What is the required specification for a new `podman-wxd` machine for this project?

**A:** Use this minimum profile:

- `--cpus 4`
- `--memory 8192`
- `--disk-size 50`
- Active connection exported through `PODMAN_CONNECTION`
- Deployment namespace `janusgraph-demo`

Fresh-machine bootstrap is mandatory:

```bash
podman machine list
podman system connection list
export PODMAN_CONNECTION=<active-connection>
podman build -t localhost/hcd:1.2.3 -f docker/hcd/Dockerfile .
cd config/compose && COMPOSE_PROJECT_NAME=janusgraph-demo bash ../../scripts/deployment/deploy_full_stack.sh
```

Reference: `docs/implementation/audits/codex-podman-wxd-fresh-machine-enforcement-matrix-2026-02-17.md`

### Q: Is the full deployment + notebook proof run now fully enforceable from docs?

**A:** Yes. The complete R-01..R-18 remediation chain is now mapped and enforced through setup, deployment, verification, operations, and scripts documentation.
