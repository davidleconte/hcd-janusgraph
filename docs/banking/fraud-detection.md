# Fraud Detection Guide

**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)  
**Contact:** +33614126117

## Overview

Real-time fraud detection using graph analytics and pattern matching.

## Detection Methods

### Graph-Based Detection

```python
from banking.fraud import FraudDetector

detector = FraudDetector()
alerts = detector.analyze_transactions(transactions)
```

### Pattern Types

| Pattern | Description | Risk Level |
|---------|-------------|------------|
| Velocity | Rapid transaction burst | High |
| Geographic | Impossible travel | Critical |
| Amount | Unusual amounts | Medium |
| Network | Fraud ring membership | Critical |

## Fraud Indicators

### Account Takeover

```gremlin
g.V().has('account', 'id', accountId)
  .inE('logged_in_from')
  .has('timestamp', gt(since))
  .outV()
  .groupCount()
```

### Money Mule Networks

```gremlin
g.V().has('type', 'account')
  .where(out('transfers_to').count().is(gt(10)))
  .where(in('transfers_to').count().is(lt(2)))
```

## Alert Management

```python
alert = FraudAlert(
    account_id="12345",
    alert_type="velocity",
    severity="high",
    details={"transactions": 50, "period": "1h"}
)
alert.submit()
```
