# Fraud Detection Module

This directory contains the fraud detection and prevention modules for the banking compliance platform.

## Contents

### Core Modules

**fraud_detection.py**
- Real-time fraud detection
- Pattern-based fraud identification
- Machine learning fraud models
- Risk scoring and alerting

## Features

### Fraud Detection Capabilities
- **Transaction Fraud:** Unusual transaction patterns, velocity checks
- **Account Takeover:** Suspicious login patterns, device fingerprinting
- **Identity Fraud:** Synthetic identity detection, document verification
- **Card Fraud:** Card-not-present fraud, card testing detection
- **Network Fraud:** Fraud ring detection, collusion analysis

### Risk Scoring
- Multi-factor risk assessment
- Real-time scoring engine
- Adaptive thresholds
- Historical pattern analysis

## Usage

### Basic Fraud Detection
```python
from banking.fraud.fraud_detection import FraudDetector

detector = FraudDetector(graph_client, opensearch_client)
result = detector.detect_fraud(
    transaction_id="TXN123",
    check_types=["velocity", "pattern", "network"]
)

if result.is_fraudulent:
    print(f"Fraud detected! Risk score: {result.risk_score}")
    print(f"Reasons: {result.reasons}")
```

### Fraud Ring Detection
```python
from banking.fraud.fraud_detection import FraudDetector

detector = FraudDetector(graph_client, opensearch_client)
rings = detector.detect_fraud_rings(
    min_ring_size=3,
    confidence_threshold=0.8
)
```

## Detection Methods

### Pattern-Based Detection
- Velocity checks (transaction frequency)
- Amount anomalies (unusual transaction sizes)
- Geographic anomalies (location changes)
- Behavioral changes (spending patterns)

### Network-Based Detection
- Fraud ring identification
- Collusion detection
- Shared entity analysis
- Graph-based pattern matching

### ML-Based Detection
- Anomaly detection models
- Classification models
- Ensemble methods
- Real-time scoring

## Documentation

- **User Guide:** [`../docs/banking/guides/USER_GUIDE.md`](../docs/banking/guides/USER_GUIDE.md)
- **API Reference:** [`../docs/banking/guides/API_REFERENCE.md`](../docs/banking/guides/API_REFERENCE.md)
- **Fraud Detection Demo:** [`../notebooks/03_Fraud_Detection_Demo.ipynb`](../notebooks/03_Fraud_Detection_Demo.ipynb)

## Related Modules

- **AML Detection:** [`../aml/`](../aml/)
- **Data Generators:** [`../data_generators/`](../data_generators/)
- **Pattern Generators:** [`../data_generators/patterns/`](../data_generators/patterns/)

## Dependencies

- JanusGraph client
- OpenSearch 3.4.0+
- Python 3.11+
- scikit-learn (for ML models)
- sentence-transformers (for embeddings)

## Testing

Run fraud detection tests:
```bash
cd banking/data_generators/tests
pytest test_patterns/test_fraud_ring_pattern_generator.py -v
```

## Configuration

Fraud detection thresholds can be configured in the detector initialization:

```python
detector = FraudDetector(
    graph_client=graph_client,
    opensearch_client=opensearch_client,
    velocity_threshold=5,  # Max transactions per hour
    amount_threshold=10000,  # Unusual amount threshold
    risk_threshold=0.7  # Alert threshold
)
```

---

**Last Updated:** 2026-01-28  
**Status:** Production Ready