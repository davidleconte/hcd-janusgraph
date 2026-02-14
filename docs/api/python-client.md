# Python Client

**Author:** David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
**Contact:**

## Installation

```bash
uv pip install -e ".[dev]"
```

## JanusGraph Client

```python
from src.python.client import JanusGraphClient

client = JanusGraphClient(
    host="localhost",
    port=18182,
    use_ssl=False
)

# Query vertices
result = client.execute("g.V().count()")
print(f"Vertex count: {result}")
```

## OpenSearch Client

```python
from opensearchpy import OpenSearch

client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    use_ssl=False
)

# Search
response = client.search(
    index="entities",
    body={"query": {"match_all": {}}}
)
```

## Data Generators

```python
from banking.data_generators.orchestration import MasterOrchestrator

orchestrator = MasterOrchestrator(seed=42)
data = orchestrator.generate_all()

# Access generated data
persons = data.persons
companies = data.companies
transactions = data.transactions
```

## Streaming Client

```python
from banking.streaming import StreamingOrchestrator, StreamingConfig

config = StreamingConfig(
    seed=42,
    person_count=100,
    pulsar_url="pulsar://localhost:6650"
)

with StreamingOrchestrator(config) as orchestrator:
    stats = orchestrator.generate_all()
```
