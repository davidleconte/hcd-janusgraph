# AML Detection Guide

**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)  
**Contact:** +33614126117

## Overview

Anti-Money Laundering (AML) detection using graph-based pattern analysis.

## Detection Patterns

### Structuring (Smurfing)

Multiple transactions just below reporting thresholds.

```python
from banking.aml import StructuringDetector

detector = StructuringDetector(threshold=10000)
alerts = detector.detect(transactions)
```

### Layering

Complex transaction chains to obscure fund origins.

```gremlin
g.V().has('type', 'account')
  .repeat(out('transfers_to'))
  .times(3)
  .path()
```

### Integration

Large deposits followed by legitimate business transactions.

## Risk Scoring

| Factor | Weight | Description |
|--------|--------|-------------|
| Transaction velocity | 0.3 | Unusual transaction frequency |
| Amount patterns | 0.25 | Threshold avoidance |
| Geographic risk | 0.2 | High-risk jurisdictions |
| Network centrality | 0.25 | Hub in suspicious network |

## Regulatory Compliance

- **BSA/AML**: Bank Secrecy Act compliance
- **SAR Filing**: Suspicious Activity Report generation
- **CTR Reporting**: Currency Transaction Reports
