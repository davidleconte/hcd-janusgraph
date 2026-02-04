# AML (Anti-Money Laundering) Module

This directory contains the Anti-Money Laundering detection and analysis modules for the banking compliance platform.

## Contents

### Core Modules

**enhanced_structuring_detection.py**
- Advanced structuring pattern detection
- Multi-account analysis
- Temporal pattern recognition
- Risk scoring algorithms

**sanctions_screening.py**
- Real-time sanctions list screening
- Entity matching with fuzzy logic
- Vector-based similarity search
- Compliance reporting

## Features

### Structuring Detection
- Identifies suspicious transaction patterns
- Detects smurfing and layering activities
- Analyzes velocity and frequency patterns
- Generates risk scores and alerts

### Sanctions Screening
- Screens against OFAC, UN, EU sanctions lists
- Performs entity name matching
- Checks beneficial ownership
- Generates compliance reports

## Detection Methods (2026-02-04 Update)

### EnhancedStructuringDetector

The `EnhancedStructuringDetector` class provides three complementary detection methods:

#### 1. Graph Pattern Detection (`detect_graph_patterns`)
- **Method:** Gremlin traversal queries
- **Detects:** Rapid sequences, amount splitting across accounts
- **Output:** StructuringPattern objects with `detection_method='graph'`

#### 2. Semantic Pattern Detection (`detect_semantic_patterns`) ✅ NEW
- **Method:** Vector embeddings + similarity clustering
- **Parameters:**
  - `min_similarity` (default: 0.85) - Minimum cosine similarity for clustering
  - `k` (default: 20) - k-NN retrieval size
  - `time_window_hours` (default: 72) - Analysis window
  - `min_cluster_size` (default: 3) - Minimum transactions per cluster
- **Process:**
  1. Query near-threshold transactions ($5k-$10k) from JanusGraph
  2. Generate embeddings for transaction descriptions
  3. Compute pairwise similarity matrix
  4. Cluster semantically similar transactions
  5. Flag clusters where total exceeds $10k threshold
- **Output:** StructuringPattern objects with `detection_method='vector'`

#### 3. Hybrid Detection (`detect_hybrid_patterns`)
- **Method:** Combines graph and semantic detection
- **Process:** Runs both methods, deduplicates, merges results
- **Output:** Combined list of unique patterns

### Detection Thresholds
| Constant | Value | Description |
|----------|-------|-------------|
| STRUCTURING_THRESHOLD | $10,000 | CTR reporting threshold |
| RAPID_SEQUENCE_HOURS | 24 | Time window for rapid sequences |
| MIN_TRANSACTIONS | 3 | Minimum transactions for pattern |
| SEMANTIC_SIMILARITY_THRESHOLD | 0.85 | Description similarity threshold |

### Usage Example
```python
from banking.aml.enhanced_structuring_detection import EnhancedStructuringDetector

detector = EnhancedStructuringDetector(
    janusgraph_host='localhost',
    janusgraph_port=8182,
    opensearch_host='localhost',
    opensearch_port=9200
)

# Semantic pattern detection
semantic_patterns = detector.detect_semantic_patterns(
    min_similarity=0.85,
    time_window_hours=72,
    min_cluster_size=3
)

# Hybrid detection (recommended)
all_patterns = detector.detect_hybrid_patterns(
    time_window_hours=24,
    min_transactions=3,
    threshold_amount=10000.0
)

for pattern in all_patterns:
    print(f"Pattern {pattern.pattern_id}: {pattern.transaction_count} txns, ${pattern.total_amount:.2f}")
```

## Usage

### Basic Structuring Detection
```python
from banking.aml.enhanced_structuring_detection import StructuringDetector

detector = StructuringDetector(graph_client, opensearch_client)
results = detector.detect_structuring(
    account_id="ACC123",
    time_window_days=30,
    threshold=10000
)
```

### Sanctions Screening
```python
from banking.aml.sanctions_screening import SanctionsScreener

screener = SanctionsScreener(opensearch_client)
matches = screener.screen_entity(
    name="John Doe",
    entity_type="person",
    threshold=0.85
)
```

## Documentation

- **User Guide:** [`../docs/banking/guides/USER_GUIDE.md`](../docs/banking/guides/USER_GUIDE.md)
- **API Reference:** [`../docs/banking/guides/API_REFERENCE.md`](../docs/banking/guides/API_REFERENCE.md)
- **Setup Guide:** [`../docs/banking/setup/01_AML_PHASE1_SETUP.md`](../docs/banking/setup/01_AML_PHASE1_SETUP.md)

## Related Modules

- **Fraud Detection:** [`../fraud/`](../fraud/)
- **Data Generators:** [`../data_generators/`](../data_generators/)
- **Notebooks:** [`../notebooks/`](../notebooks/)

## Dependencies

- JanusGraph client
- OpenSearch 3.4.0+
- Python 3.11+
- sentence-transformers (for vector embeddings)

## Testing

Run AML module tests:
```bash
cd banking/data_generators/tests
pytest test_patterns/ -v
```

---

**Last Updated:** 2026-01-28  
**Status:** Production Ready