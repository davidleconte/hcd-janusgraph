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