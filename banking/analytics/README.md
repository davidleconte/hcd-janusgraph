# Banking Analytics Module

**Version:** 1.0.0  
**Last Updated:** 2026-02-20  
**Status:** Production Ready

## Overview

The Banking Analytics module provides advanced graph-based analytics for detecting financial crimes and suspicious patterns including insider trading, trade-based money laundering (TBML), and AML structuring. Built on JanusGraph, it leverages graph traversal algorithms to identify complex multi-hop patterns that traditional analytics miss.

## Features

### Insider Trading Detection (`detect_insider_trading.py`)

Advanced detection of insider trading patterns using 6 detection methods:

1. **Timing Correlation Analysis** - Trades suspiciously timed before corporate announcements
2. **Coordinated Trading Detection** - Multiple traders acting together in short time windows
3. **Communication-Based Detection** - Suspicious communications preceding trades
4. **Network Analysis** - Trading by individuals connected to company insiders
5. **Abnormal Volume Detection** - Unusual trading volumes before events
6. **Information Asymmetry Detection** - Trades indicating non-public information

**Key Capabilities:**
- Pre-announcement window analysis (14 days default)
- Coordination time window detection (4 hours default)
- MNPI (Material Non-Public Information) keyword detection
- PEP (Politically Exposed Persons) involvement tracking
- Risk scoring with severity classification

### Trade-Based Money Laundering Detection (`detect_tbml.py`)

Detects sophisticated TBML schemes using 5 detection methods:

1. **Carousel Fraud Detection** - Circular trading loops (A → B → C → A)
2. **Over-Invoicing Detection** - Inflated prices to move money out
3. **Under-Invoicing Detection** - Deflated prices to avoid customs/taxes
4. **Phantom Shipments** - Goods that don't exist
5. **Shell Company Networks** - Networks of suspicious entities

**Key Capabilities:**
- Multi-hop circular loop detection (2-5 hops)
- Price deviation analysis (20% threshold)
- Shell company scoring (incorporation date, employee count, transaction volume)
- High-risk jurisdiction identification
- Network clustering algorithms

### AML Structuring Detection (`aml_structuring_detector.py`)

Detects money laundering structuring patterns (smurfing):

1. **CTR Threshold Analysis** - Transactions just under $10,000 reporting threshold
2. **High-Volume Account Detection** - Accounts with excessive transaction counts
3. **Rapid Succession Deposits** - Multiple deposits in short time periods
4. **Transaction Chain Analysis** - Money moving through multiple accounts (layering)

**Key Capabilities:**
- CTR threshold monitoring ($10,000)
- Structuring threshold detection ($9,500)
- Multi-hop transaction chain analysis
- Risk scoring and SAR (Suspicious Activity Report) recommendations

## Installation

```bash
# Install dependencies
uv pip install -r requirements.txt

# Verify JanusGraph connection
python -c "from gremlin_python.driver import client; c = client.Client('ws://localhost:18182/gremlin', 'g'); print('Connected:', c.submit('g.V().count()').all().result())"
```

## Quick Start

### Insider Trading Detection

```python
from banking.analytics.detect_insider_trading import InsiderTradingDetector, CorporateEvent
from datetime import datetime, timezone

# Initialize detector
detector = InsiderTradingDetector(url="ws://localhost:18182/gremlin")

# Define corporate events (optional - can auto-detect)
events = [
    CorporateEvent(
        event_id="EVT-001",
        company_id="COMP-123",
        symbol="ACME",
        event_type="earnings",
        announcement_date=datetime(2026, 2, 15, tzinfo=timezone.utc),
        impact="positive",
        price_change_percent=15.5
    )
]

# Run full scan
report = detector.run_full_scan()

print(f"Total Alerts: {report['total_alerts']}")
print(f"Timing Alerts: {report['alerts_by_type']['timing']}")
print(f"Coordinated Alerts: {report['alerts_by_type']['coordinated']}")
print(f"Communication Alerts: {report['alerts_by_type']['communication']}")
print(f"Network Alerts: {report['alerts_by_type']['network']}")
print(f"Total Value at Risk: ${report['total_value_at_risk']:,.2f}")
print(f"Unique Traders Flagged: {report['unique_traders']}")

# Access individual alerts
for alert in report['alerts']:
    if alert['severity'] == 'critical':
        print(f"\nCritical Alert: {alert['alert_id']}")
        print(f"Type: {alert['type']}")
        print(f"Risk Score: {alert['risk_score']:.2f}")
        print(f"Traders: {', '.join(alert['traders'])}")
        print(f"Indicators: {', '.join(alert['indicators'])}")
```

### TBML Detection

```python
from banking.analytics.detect_tbml import TBMLDetector

# Initialize detector
detector = TBMLDetector(url="ws://localhost:18182/gremlin")

# Run full scan
report = detector.run_full_scan()

print(f"Total Alerts: {report['total_alerts']}")
print(f"Carousel Fraud: {report['alerts_by_type']['carousel']}")
print(f"Over-Invoicing: {report['alerts_by_type']['over_invoicing']}")
print(f"Under-Invoicing: {report['alerts_by_type']['under_invoicing']}")
print(f"Shell Networks: {report['alerts_by_type']['shell_network']}")
print(f"Total Value at Risk: ${report['total_value_at_risk']:,.2f}")

# Access alerts by severity
critical_alerts = [a for a in report['alerts'] if a['severity'] == 'critical']
print(f"\nCritical Alerts: {len(critical_alerts)}")
for alert in critical_alerts:
    print(f"  - {alert['type']}: {alert['entities']}")
```

### AML Structuring Detection

```python
from banking.analytics.aml_structuring_detector import AMLStructuringDetector

# Initialize detector
detector = AMLStructuringDetector(url="ws://localhost:18182/gremlin")

# Run full analysis
findings = detector.run_full_analysis()

# Access findings
print(f"Structuring Patterns: {len(findings['structuring_patterns'])}")
print(f"High-Risk Accounts: {len(findings['high_risk_accounts'])}")

# Review structuring patterns
for pattern in findings['structuring_patterns']:
    print(f"\nAccount: {pattern['account_id']}")
    print(f"Suspicious Transactions: {pattern['suspicious_tx_count']}")
    print(f"Risk Level: {pattern['risk_level']}")
    print(f"Recommendation: {pattern['recommendation']}")
```

## Advanced Usage

### Custom Detection Thresholds

```python
from banking.analytics.detect_insider_trading import InsiderTradingDetector

detector = InsiderTradingDetector()

# Customize detection parameters
detector.PRE_ANNOUNCEMENT_WINDOW_DAYS = 21  # Extend to 3 weeks
detector.COORDINATION_TIME_WINDOW_HOURS = 2  # Tighten to 2 hours
detector.MIN_SUSPICIOUS_TRADES = 5  # Require more trades
detector.VOLUME_SPIKE_THRESHOLD = 3.0  # 3x average volume

# Run with custom thresholds
report = detector.run_full_scan()
```

### Individual Detection Methods

```python
from banking.analytics.detect_insider_trading import InsiderTradingDetector

detector = InsiderTradingDetector()
detector.connect()

try:
    # Run specific detection methods
    timing_alerts = detector.detect_timing_patterns()
    coordinated_alerts = detector.detect_coordinated_trading()
    communication_alerts = detector.detect_suspicious_communications()
    network_alerts = detector.detect_network_patterns()
    
    # Generate custom report
    report = detector.generate_report()
finally:
    detector.close()
```

### Price Anomaly Analysis

```python
from banking.analytics.detect_tbml import TBMLDetector

detector = TBMLDetector()
detector.connect()

try:
    # Provide market prices for comparison
    market_prices = {
        "GOLD-1KG": 50000.0,
        "ELECTRONICS-SERVER": 5000.0,
        "LUXURY-WATCH": 10000.0
    }
    
    # Detect invoice manipulation
    anomalies, alerts = detector.detect_invoice_manipulation(market_prices)
    
    print(f"Price Anomalies: {len(anomalies)}")
    for anomaly in anomalies:
        print(f"Transaction: {anomaly.transaction_id}")
        print(f"Declared: ${anomaly.declared_price:,.2f}")
        print(f"Market: ${anomaly.market_price:,.2f}")
        print(f"Deviation: {anomaly.deviation_percent:.1f}%")
        print(f"Direction: {anomaly.direction}-invoicing")
        print()
finally:
    detector.close()
```

### Carousel Fraud with Custom Depth

```python
from banking.analytics.detect_tbml import TBMLDetector

detector = TBMLDetector()
detector.connect()

try:
    # Search for deeper circular loops
    alerts = detector.detect_carousel_fraud(max_depth=5)
    
    for alert in alerts:
        print(f"Loop Depth: {alert.details['depth']}")
        print(f"Companies: {' → '.join(alert.entities)}")
        print(f"Total Value: ${alert.total_value:,.2f}")
        print(f"Risk Score: {alert.risk_score:.2f}")
        print()
finally:
    detector.close()
```

## Detection Algorithms

### Insider Trading - Timing Correlation

**Algorithm:**
1. Query high-value trades (top 200 by value)
2. Group trades by symbol
3. For each corporate event:
   - Find trades in pre-announcement window (14 days)
   - Check if trade direction matches event impact
   - Calculate risk score based on:
     - Number of trades (≥10: +0.2, ≥5: +0.1)
     - Total value (≥$500K: +0.2, ≥$100K: +0.1)
     - Price impact (≥20%: +0.2, ≥10%: +0.1)
     - PEP involvement (+0.2)
4. Generate alert if risk score ≥ 0.6

**Performance:** <500ms for 200 trades

### TBML - Carousel Fraud

**Algorithm:**
1. For each depth (2-5 hops):
   - Build dynamic Gremlin query for circular paths
   - Find companies where: A → B → ... → A
   - Extract transaction chains and company names
2. Calculate risk score:
   - Base: 0.5
   - Depth factor: +0.1 per hop
   - Company count: +0.05 per company
   - Value factor: >$500K: +0.2, >$100K: +0.1
3. Generate alert if total value ≥ $50,000

**Performance:** <2s for depth 3, <5s for depth 5

### AML - Structuring Detection

**Algorithm:**
1. Query all transactions
2. Calculate distribution by amount ranges
3. Identify transactions in suspicious range ($9,000-$9,999)
4. For each account:
   - Count transactions in suspicious range
   - Flag if count ≥ 2 (structuring threshold)
5. Generate SAR recommendation for flagged accounts

**Performance:** <1s for 10,000 transactions

## Configuration

### Detection Thresholds

```python
# Insider Trading
PRE_ANNOUNCEMENT_WINDOW_DAYS = 14
POST_ANNOUNCEMENT_WINDOW_DAYS = 3
VOLUME_SPIKE_THRESHOLD = 2.5
PRICE_MOVEMENT_THRESHOLD = 0.05  # 5%
COORDINATION_TIME_WINDOW_HOURS = 4
MIN_SUSPICIOUS_TRADES = 3
COMMUNICATION_WINDOW_HOURS = 48

# TBML
PRICE_DEVIATION_THRESHOLD = 0.20  # 20%
CIRCULAR_LOOP_MAX_DEPTH = 5
MIN_LOOP_VALUE = 50000.0
SHELL_COMPANY_INDICATORS = {
    "low_employees": 5,
    "recent_incorporation_days": 180,
    "high_transaction_volume_ratio": 10.0
}

# AML Structuring
CTR_THRESHOLD = 10000.0
STRUCTURING_THRESHOLD = 9500.0
SUSPICIOUS_TX_COUNT = 3
```

### Environment Variables

```bash
# JanusGraph connection
export JANUSGRAPH_URL="ws://localhost:18182/gremlin"

# Detection sensitivity
export INSIDER_TRADING_SENSITIVITY="high"  # low, medium, high
export TBML_MAX_DEPTH="4"
export AML_CTR_THRESHOLD="10000"
```

## Performance Benchmarks

| Detection Method | Dataset Size | Execution Time | Memory Usage |
|-----------------|--------------|----------------|--------------|
| Insider Trading (Timing) | 200 trades | <500ms | <50MB |
| Insider Trading (Coordinated) | 500 trades | <1s | <100MB |
| Insider Trading (Communication) | 100 comm + 100 trades | <800ms | <75MB |
| Insider Trading (Network) | 100 relationships | <1.2s | <80MB |
| TBML (Carousel, depth 3) | 1000 companies | <2s | <150MB |
| TBML (Carousel, depth 5) | 1000 companies | <5s | <200MB |
| TBML (Invoice Manipulation) | 500 transactions | <1s | <100MB |
| TBML (Shell Networks) | 200 companies | <1.5s | <120MB |
| AML (Structuring) | 10,000 transactions | <1s | <80MB |
| AML (Transaction Chains) | 5,000 accounts | <2s | <150MB |

**Test Environment:** 4 CPU cores, 8GB RAM, JanusGraph 1.0.0, HCD 1.2.3

## Testing

```bash
# Run analytics module tests
pytest banking/analytics/tests/ -v

# Run with coverage
pytest banking/analytics/tests/ --cov=banking/analytics --cov-report=html

# Run specific detector tests
pytest banking/analytics/tests/test_insider_trading.py -v
pytest banking/analytics/tests/test_tbml.py -v
pytest banking/analytics/tests/test_aml_structuring.py -v

# Run property-based tests
pytest banking/analytics/tests/test_property_based.py -v
```

## Integration with Notebooks

The analytics module is used in production notebooks:

- **Notebook 08:** Insider Trading Detection (Corporate Banking)
- **Notebook 09:** TBML Detection (Corporate Banking)
- **Notebook 02:** AML Structuring Detection (Retail Banking)

See [`banking/notebooks/README.md`](../notebooks/README.md) for details.

## Compliance & Reporting

### SAR (Suspicious Activity Report) Generation

```python
from banking.analytics.aml_structuring_detector import AMLStructuringDetector

detector = AMLStructuringDetector()
findings = detector.run_full_analysis()

# Generate SAR-ready report
report = detector.generate_report()

# Export for compliance review
with open("/reports/sar_candidates.txt", "w") as f:
    f.write(report)
```

### Regulatory Requirements

✅ **BSA/AML Compliance**
- CTR threshold monitoring ($10,000)
- SAR filing recommendations
- Structuring pattern detection
- Transaction chain analysis

✅ **SEC Insider Trading Rules**
- Pre-announcement trading detection
- Coordinated trading identification
- MNPI sharing detection
- Network relationship analysis

✅ **FATF TBML Guidelines**
- Carousel fraud detection
- Invoice manipulation detection
- Shell company identification
- High-risk jurisdiction monitoring

## Troubleshooting

### Issue: No alerts generated

```python
# Verify graph has data
from gremlin_python.driver import client

c = client.Client('ws://localhost:18182/gremlin', 'g')
vertex_count = c.submit('g.V().count()').all().result()[0]
edge_count = c.submit('g.E().count()').all().result()[0]

print(f"Vertices: {vertex_count}")
print(f"Edges: {edge_count}")

# Check for required labels
labels = c.submit('g.V().label().dedup()').all().result()
print(f"Labels: {labels}")

# Verify trade data exists
trade_count = c.submit("g.V().hasLabel('trade').count()").all().result()[0]
print(f"Trades: {trade_count}")
```

### Issue: Connection timeout

```bash
# Check JanusGraph is running
curl http://localhost:8182?gremlin=g.V().count()

# Verify WebSocket port
netstat -an | grep 18182

# Test connection
python -c "from gremlin_python.driver import client; c = client.Client('ws://localhost:18182/gremlin', 'g'); print(c.submit('g.V().count()').all().result())"
```

### Issue: Slow query performance

```python
# Enable query profiling
detector = InsiderTradingDetector()
detector.connect()

# Profile specific query
import time
start = time.time()
alerts = detector.detect_timing_patterns()
elapsed = time.time() - start
print(f"Timing detection: {elapsed:.2f}s")

# Check graph indices
indices = detector._query("mgmt = graph.openManagement(); mgmt.getGraphIndexes()")
print(f"Indices: {indices}")
```

## API Reference

### InsiderTradingDetector

```python
class InsiderTradingDetector:
    def __init__(self, url: str = "ws://localhost:18182/gremlin")
    def connect(self) -> None
    def close(self) -> None
    def detect_timing_patterns(self, corporate_events: Optional[List[CorporateEvent]] = None) -> List[InsiderTradingAlert]
    def detect_coordinated_trading(self) -> List[InsiderTradingAlert]
    def detect_suspicious_communications(self) -> List[InsiderTradingAlert]
    def detect_network_patterns(self) -> List[InsiderTradingAlert]
    def generate_report(self) -> Dict[str, Any]
    def run_full_scan(self) -> Dict[str, Any]
```

### TBMLDetector

```python
class TBMLDetector:
    def __init__(self, url: str = "ws://localhost:18182/gremlin")
    def connect(self) -> None
    def close(self) -> None
    def detect_carousel_fraud(self, max_depth: int = 4) -> List[TBMLAlert]
    def detect_invoice_manipulation(self, market_prices: Optional[Dict[str, float]] = None) -> Tuple[List[PriceAnomaly], List[TBMLAlert]]
    def detect_shell_company_networks(self) -> List[TBMLAlert]
    def generate_report(self) -> Dict[str, Any]
    def run_full_scan(self) -> Dict[str, Any]
```

### AMLStructuringDetector

```python
class AMLStructuringDetector:
    def __init__(self, url: str = "ws://localhost:18182/gremlin")
    def connect(self) -> None
    def close(self) -> None
    def analyze_transaction_amounts(self) -> Dict[str, Any]
    def identify_high_volume_accounts(self) -> List[Dict[str, Any]]
    def detect_structuring_patterns(self) -> List[Dict[str, Any]]
    def analyze_transaction_chains(self) -> List[Dict[str, Any]]
    def generate_report(self) -> str
    def run_full_analysis(self) -> Dict[str, Any]
```

## Related Documentation

- [Banking Domain Audit](../../docs/implementation/audits/banking-domain-audit-2026-02-20.md)
- [AML Detection](../aml/README.md)
- [Fraud Detection](../fraud/README.md)
- [Compliance Module](../compliance/README.md)
- [User Guide](../../docs/banking/guides/user-guide.md)

## Support

For issues or questions:
- GitHub Issues: [hcd-janusgraph/issues](https://github.com/davidleconte/hcd-janusgraph/issues)
- Documentation: [docs/banking/guides/user-guide.md](../../docs/banking/guides/user-guide.md)

## License

Copyright © 2026 IBM. All rights reserved.
