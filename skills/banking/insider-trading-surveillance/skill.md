# Insider Trading Surveillance

**Skill Type:** Banking Domain - Market Surveillance  
**Complexity:** Advanced  
**Estimated Time:** 4-8 hours per investigation  
**Prerequisites:** Understanding of securities regulations, insider trading patterns, MNPI concepts

## Overview

This skill guides compliance analysts through insider trading surveillance - detecting and investigating suspicious trading activity that may involve Material Non-Public Information (MNPI). Insider trading is illegal under SEC Rule 10b-5 and can result in criminal prosecution.

### Key Concepts

**Material Non-Public Information (MNPI):** Information that could influence an investor's decision and is not publicly available.

**Insider:** Person with access to MNPI (executives, directors, employees, advisors).

**Tippee:** Person who receives MNPI from an insider.

**Corporate Events:** Earnings, M&A, product launches, regulatory actions.

**Detection Methods:**
1. Timing Analysis (trades before announcements)
2. Coordinated Trading (multiple related parties)
3. Communication Analysis (contact before trades)
4. Network Analysis (relationship mapping)
5. Volume Anomalies (unusual trading volume)
6. Asymmetric Information (consistent profitable trades)

## Workflow Steps

### Step 1: Monitor Corporate Events

**Objective:** Track corporate events that could involve MNPI.

```python
from banking.analytics.detect_insider_trading import InsiderTradingDetector
from src.python.client.janusgraph_client import JanusGraphClient

# Initialize detector
graph_client = JanusGraphClient()
detector = InsiderTradingDetector(graph_client)

# Monitor corporate events
events = detector.get_corporate_events(
    lookback_days=30,
    event_types=['EARNINGS', 'MERGER', 'ACQUISITION', 'PRODUCT_LAUNCH']
)

print(f"Monitoring {len(events)} corporate events")
```

---

### Step 2: Detect Timing Anomalies

**Objective:** Identify trades occurring suspiciously close to corporate announcements.

```python
def detect_timing_anomalies(company_id: str, event_date: datetime, window_days: int = 30) -> list:
    """Detect suspicious trading before corporate event."""
    
    # Define suspicious window (e.g., 30 days before announcement)
    window_start = event_date - timedelta(days=window_days)
    
    # Get trades in suspicious window
    suspicious_trades = graph_client.execute(f"""
        g.V().has('Company', 'companyId', '{company_id}')
            .in('SECURITY_OF')
            .inE('TRADE')
            .has('timestamp', gte({window_start.timestamp()}))
            .has('timestamp', lt({event_date.timestamp()}))
            .project('trader', 'amount', 'timestamp', 'days_before')
            .by(outV().values('customerId'))
            .by(values('amount'))
            .by(values('timestamp'))
            .by(values('timestamp').map({{it.get() - {event_date.timestamp()}}}.abs().div(86400)))
    """)
    
    # Score by proximity to event
    for trade in suspicious_trades:
        days_before = trade['days_before']
        
        if days_before <= 7:
            trade['timing_score'] = 1.0  # Very suspicious
        elif days_before <= 14:
            trade['timing_score'] = 0.75
        elif days_before <= 21:
            trade['timing_score'] = 0.50
        else:
            trade['timing_score'] = 0.25
    
    return [t for t in suspicious_trades if t['timing_score'] >= 0.50]

# Detect timing anomalies
event_date = datetime(2026, 2, 15)
timing_alerts = detect_timing_anomalies('company-123', event_date)
print(f"Found {len(timing_alerts)} timing anomalies")
```

---

### Step 3: Analyze Coordinated Trading

**Objective:** Detect multiple related parties trading around same time.

```python
def detect_coordinated_trading(company_id: str, event_date: datetime) -> dict:
    """Detect coordinated trading among related parties."""
    
    window_start = event_date - timedelta(days=30)
    
    # Get all traders in window
    traders = graph_client.execute(f"""
        g.V().has('Company', 'companyId', '{company_id}')
            .in('SECURITY_OF')
            .inE('TRADE')
            .has('timestamp', gte({window_start.timestamp()}))
            .has('timestamp', lt({event_date.timestamp()}))
            .outV()
            .dedup()
            .values('customerId')
    """)
    
    # Find relationships between traders
    coordinated_groups = []
    
    for i, trader1 in enumerate(traders):
        for trader2 in traders[i+1:]:
            # Check if traders are related
            relationship = graph_client.execute(f"""
                g.V().has('Person', 'customerId', '{trader1}')
                    .both('FAMILY_MEMBER', 'BUSINESS_ASSOCIATE', 'FRIEND')
                    .has('customerId', '{trader2}')
                    .path()
            """)
            
            if relationship:
                # Get their trades
                trader1_trades = get_trades(trader1, company_id, window_start, event_date)
                trader2_trades = get_trades(trader2, company_id, window_start, event_date)
                
                # Check temporal proximity
                time_diff = abs(
                    trader1_trades[0]['timestamp'] - trader2_trades[0]['timestamp']
                ).total_seconds() / 86400  # days
                
                if time_diff <= 7:  # Within 7 days
                    coordinated_groups.append({
                        'traders': [trader1, trader2],
                        'relationship': relationship[0].labels(),
                        'time_diff_days': time_diff,
                        'coordination_score': 1.0 - (time_diff / 7)
                    })
    
    return {
        'groups_found': len(coordinated_groups),
        'groups': coordinated_groups
    }

coordination = detect_coordinated_trading('company-123', event_date)
print(f"Coordinated groups: {coordination['groups_found']}")
```

---

### Step 4: Analyze Communication Patterns

**Objective:** Detect communications between insiders and traders before trades.

```python
def analyze_communication_patterns(trader_id: str, company_id: str, trade_date: datetime) -> dict:
    """Analyze communications before trade."""
    
    # Look for communications 30 days before trade
    comm_window_start = trade_date - timedelta(days=30)
    
    # Get company insiders
    insiders = graph_client.execute(f"""
        g.V().has('Company', 'companyId', '{company_id}')
            .in('EMPLOYEE_OF', 'DIRECTOR_OF', 'OFFICER_OF')
            .values('customerId')
    """)
    
    # Check for communications with insiders
    suspicious_comms = []
    
    for insider in insiders:
        communications = graph_client.execute(f"""
            g.V().has('Person', 'customerId', '{trader_id}')
                .bothE('COMMUNICATED_WITH')
                .has('timestamp', gte({comm_window_start.timestamp()}))
                .has('timestamp', lt({trade_date.timestamp()}))
                .where(otherV().has('customerId', '{insider}'))
                .project('type', 'timestamp', 'days_before_trade')
                .by(values('type'))
                .by(values('timestamp'))
                .by(values('timestamp').map({{({trade_date.timestamp()} - it.get()) / 86400}}))
        """)
        
        if communications:
            for comm in communications:
                days_before = comm['days_before_trade']
                
                # Score by proximity to trade
                if days_before <= 3:
                    comm_score = 1.0
                elif days_before <= 7:
                    comm_score = 0.75
                elif days_before <= 14:
                    comm_score = 0.50
                else:
                    comm_score = 0.25
                
                suspicious_comms.append({
                    'insider': insider,
                    'type': comm['type'],
                    'days_before_trade': days_before,
                    'score': comm_score
                })
    
    return {
        'communications_found': len(suspicious_comms),
        'communications': suspicious_comms,
        'max_score': max([c['score'] for c in suspicious_comms]) if suspicious_comms else 0
    }

comms = analyze_communication_patterns(trader_id, 'company-123', trade_date)
print(f"Suspicious communications: {comms['communications_found']}")
```

---

### Step 5: Calculate Insider Trading Risk Score

**Objective:** Aggregate all detection methods into comprehensive risk score.

```python
def calculate_insider_trading_risk(
    timing_score: float,
    coordination_score: float,
    communication_score: float,
    volume_score: float,
    profit_score: float,
    network_score: float
) -> dict:
    """Calculate comprehensive insider trading risk score."""
    
    # Weighted scoring
    weights = {
        'timing': 0.25,
        'coordination': 0.20,
        'communication': 0.20,
        'volume': 0.15,
        'profit': 0.10,
        'network': 0.10
    }
    
    total_score = (
        timing_score * weights['timing'] +
        coordination_score * weights['coordination'] +
        communication_score * weights['communication'] +
        volume_score * weights['volume'] +
        profit_score * weights['profit'] +
        network_score * weights['network']
    )
    
    # Risk classification
    if total_score >= 0.80:
        risk_level = 'CRITICAL'
        action = 'IMMEDIATE_INVESTIGATION'
    elif total_score >= 0.65:
        risk_level = 'HIGH'
        action = 'PRIORITY_INVESTIGATION'
    elif total_score >= 0.50:
        risk_level = 'MEDIUM'
        action = 'STANDARD_INVESTIGATION'
    else:
        risk_level = 'LOW'
        action = 'MONITOR'
    
    return {
        'total_score': total_score,
        'risk_level': risk_level,
        'recommended_action': action,
        'component_scores': {
            'timing': timing_score,
            'coordination': coordination_score,
            'communication': communication_score,
            'volume': volume_score,
            'profit': profit_score,
            'network': network_score
        }
    }

risk = calculate_insider_trading_risk(
    timing_score=0.90,
    coordination_score=0.75,
    communication_score=0.85,
    volume_score=0.60,
    profit_score=0.70,
    network_score=0.65
)

print(f"Risk Score: {risk['total_score']:.2f}")
print(f"Risk Level: {risk['risk_level']}")
print(f"Action: {risk['recommended_action']}")
```

---

### Step 6: Document Investigation

**Objective:** Create comprehensive investigation report for SEC filing.

```python
def generate_investigation_report(
    trader_id: str,
    company_id: str,
    event_date: datetime,
    risk_assessment: dict,
    evidence: dict
) -> dict:
    """Generate insider trading investigation report."""
    
    report = {
        'report_id': f"IT-{trader_id}-{datetime.now().strftime('%Y%m%d')}",
        'investigation_date': datetime.now().isoformat(),
        'analyst': get_current_user(),
        
        'subject': {
            'trader_id': trader_id,
            'trader_name': get_trader_name(trader_id),
            'relationship_to_company': get_relationship(trader_id, company_id)
        },
        
        'corporate_event': {
            'company_id': company_id,
            'company_name': get_company_name(company_id),
            'event_type': evidence['event_type'],
            'event_date': event_date.isoformat(),
            'announcement_date': evidence['announcement_date']
        },
        
        'trading_activity': {
            'trade_date': evidence['trade_date'],
            'days_before_announcement': evidence['days_before'],
            'trade_amount': evidence['trade_amount'],
            'profit_loss': evidence.get('profit_loss', 0)
        },
        
        'risk_assessment': risk_assessment,
        
        'evidence': {
            'timing_evidence': evidence.get('timing', []),
            'coordination_evidence': evidence.get('coordination', []),
            'communication_evidence': evidence.get('communications', []),
            'network_evidence': evidence.get('network', [])
        },
        
        'recommendation': {
            'action': risk_assessment['recommended_action'],
            'sec_referral': risk_assessment['risk_level'] in ['CRITICAL', 'HIGH'],
            'account_restrictions': risk_assessment['risk_level'] == 'CRITICAL'
        }
    }
    
    return report

report = generate_investigation_report(
    trader_id, company_id, event_date, risk, evidence
)
```

---

## Real-World Examples

### Example 1: Classic Insider Trading

**Scenario:** Executive trades before merger announcement

```
Trader: John Smith (CFO of Company A)
Event: Merger announcement
Trade Date: 2026-01-15
Announcement: 2026-02-01 (17 days later)
Trade: Sold 50,000 shares at $45
Post-Announcement Price: $32 (28% drop)
Profit: $650,000

Risk Factors:
- Timing Score: 0.95 (17 days before)
- Communication: N/A (insider)
- Profit: $650,000 (significant)
- Network: Executive position

Outcome: CRITICAL risk, SEC referral
```

---

### Example 2: Tippee Trading

**Scenario:** Friend of executive trades before earnings

```
Trader: Jane Doe (no company relationship)
Insider: Mike Johnson (CEO, friend of Jane)
Event: Negative earnings surprise
Communication: Phone call 3 days before trade
Trade Date: 2026-01-20
Announcement: 2026-01-25 (5 days later)
Trade: Sold 10,000 shares at $60
Post-Announcement Price: $48 (20% drop)
Profit: $120,000

Risk Factors:
- Timing Score: 1.0 (5 days before)
- Communication Score: 1.0 (3 days before trade)
- Coordination: Friend relationship
- Profit: $120,000

Outcome: CRITICAL risk, SEC referral
```

---

## Performance Metrics

| Metric | Target |
|--------|--------|
| Detection Rate | >90% |
| False Positive Rate | <15% |
| Investigation Time | <8 hours |
| SEC Referral Time | <48 hours |

---

## Integration

```python
from banking.compliance.audit_logger import get_audit_logger

# Log investigation
audit_logger = get_audit_logger()
audit_logger.log_compliance_event(
    event_type='INSIDER_TRADING_INVESTIGATION',
    user=get_current_user(),
    resource=f"trader:{trader_id}",
    metadata={
        'risk_score': risk['total_score'],
        'risk_level': risk['risk_level'],
        'sec_referral': report['recommendation']['sec_referral']
    }
)
```

---

## Templates

See [`templates/investigation-report.md`](templates/investigation-report.md) for investigation template.

---

**Last Updated:** 2026-02-20  
**Version:** 1.0  
**Maintained By:** Market Surveillance Team