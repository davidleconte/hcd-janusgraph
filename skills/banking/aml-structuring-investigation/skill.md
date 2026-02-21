# AML Structuring Investigation

**Skill Type:** Banking Domain - AML Compliance  
**Complexity:** Advanced  
**Estimated Time:** 3-6 hours per investigation  
**Prerequisites:** Understanding of BSA/AML regulations, CTR requirements, structuring patterns

## Overview

This skill guides AML analysts through the investigation of potential structuring (also known as "smurfing") - the practice of breaking up large transactions into smaller amounts to evade Currency Transaction Report (CTR) filing requirements. Structuring is a federal crime under 31 U.S.C. § 5324 and a key indicator of money laundering.

### Key Concepts

**Structuring:** The practice of conducting multiple transactions below the $10,000 CTR threshold to avoid reporting requirements.

**Currency Transaction Report (CTR):** Required for cash transactions exceeding $10,000 in a single day.

**Suspicious Activity Report (SAR):** Required when structuring is suspected, regardless of amount.

**Aggregation:** Combining related transactions to determine if CTR threshold is met.

**Lookback Period:** Typically 30 days for pattern analysis, but can extend to 90+ days.

### Regulatory Framework

- **Bank Secrecy Act (BSA):** 31 U.S.C. § 5311 et seq.
- **Anti-Structuring Statute:** 31 U.S.C. § 5324
- **FinCEN Regulations:** 31 CFR § 103
- **CTR Filing:** FinCEN Form 112
- **SAR Filing:** FinCEN Form 111

## Workflow Steps

### Step 1: Alert Reception and Initial Triage

**Objective:** Receive and validate structuring alert from transaction monitoring system.

**Alert Types:**
- Multiple deposits/withdrawals just below $10,000
- Frequent transactions in $9,000-$9,999 range
- Pattern of transactions across multiple accounts
- Rapid succession of transactions at different branches/ATMs
- Transactions split across multiple individuals (smurfing)

**Initial Assessment:**

```python
from banking.aml.aml_detection import AMLDetector
from src.python.client.janusgraph_client import JanusGraphClient

# Initialize clients
graph_client = JanusGraphClient()
aml_detector = AMLDetector(graph_client)

# Retrieve alert details
alert_id = "STR-2026-001234"
alert = aml_detector.get_alert(alert_id)

print(f"Alert ID: {alert['id']}")
print(f"Alert Type: {alert['type']}")
print(f"Customer: {alert['customer_name']} ({alert['customer_id']})")
print(f"Date Range: {alert['start_date']} to {alert['end_date']}")
print(f"Transaction Count: {alert['transaction_count']}")
print(f"Total Amount: ${alert['total_amount']:,.2f}")
print(f"Risk Score: {alert['risk_score']:.2f}")
```

**Triage Decision:**

```python
def triage_structuring_alert(alert: dict) -> str:
    """
    Determine investigation priority.
    
    Returns: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', or 'FALSE_POSITIVE'
    """
    # Critical indicators
    if alert['transaction_count'] >= 10 and alert['total_amount'] >= 50000:
        return 'CRITICAL'
    
    if alert['involves_multiple_accounts'] and alert['total_amount'] >= 30000:
        return 'CRITICAL'
    
    # High priority
    if alert['transaction_count'] >= 5 and alert['total_amount'] >= 25000:
        return 'HIGH'
    
    if alert['pattern_consistency'] > 0.8:  # Highly consistent pattern
        return 'HIGH'
    
    # Medium priority
    if alert['transaction_count'] >= 3:
        return 'MEDIUM'
    
    # Low priority or false positive
    if alert['transaction_count'] < 3 or alert['total_amount'] < 15000:
        return 'LOW'
    
    return 'MEDIUM'

priority = triage_structuring_alert(alert)
print(f"Investigation Priority: {priority}")
```

---

### Step 2: Gather Transaction History

**Objective:** Collect comprehensive transaction history for analysis.

```python
def gather_transaction_history(
    customer_id: str,
    lookback_days: int = 30
) -> list:
    """Gather transaction history for structuring analysis."""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    transactions = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .out('OWNS')
            .hasLabel('Account')
            .outE('TRANSACTION')
            .has('timestamp', gte({start_date.timestamp()}))
            .has('timestamp', lte({end_date.timestamp()}))
            .project('id', 'type', 'amount', 'timestamp', 'account', 'location')
            .by(id)
            .by(values('type'))
            .by(values('amount'))
            .by(values('timestamp'))
            .by(inV().values('accountNumber'))
            .by(values('location'))
            .order().by('timestamp', asc)
    """)
    
    return [
        {
            'id': t['id'],
            'type': t['type'],
            'amount': float(t['amount']),
            'timestamp': datetime.fromtimestamp(t['timestamp']),
            'account': t['account'],
            'location': t.get('location', 'Unknown')
        }
        for t in transactions
    ]

transactions = gather_transaction_history(alert['customer_id'])
print(f"Retrieved {len(transactions)} transactions")
```

---

### Step 3: Detect Structuring Patterns

**Objective:** Identify specific structuring patterns in transaction data.

#### Pattern 1: Classic Structuring (Just Below Threshold)

```python
def detect_classic_structuring(transactions: list, threshold: float = 10000.0) -> dict:
    """Detect transactions just below CTR threshold."""
    
    lower_bound = threshold * 0.90  # $9,000
    flagged_txns = []
    
    for txn in transactions:
        if lower_bound <= txn['amount'] < threshold:
            flagged_txns.append({
                'transaction': txn,
                'distance_from_threshold': threshold - txn['amount'],
                'percentage_of_threshold': (txn['amount'] / threshold) * 100
            })
    
    if flagged_txns:
        amounts = [t['transaction']['amount'] for t in flagged_txns]
        avg_amount = sum(amounts) / len(amounts)
        std_dev = (sum((x - avg_amount) ** 2 for x in amounts) / len(amounts)) ** 0.5
        
        return {
            'pattern_detected': True,
            'flagged_count': len(flagged_txns),
            'total_amount': sum(amounts),
            'average_amount': avg_amount,
            'std_deviation': std_dev,
            'consistency_score': 1 - (std_dev / avg_amount) if avg_amount > 0 else 0,
            'transactions': flagged_txns
        }
    
    return {'pattern_detected': False}

classic_pattern = detect_classic_structuring(transactions)

if classic_pattern['pattern_detected']:
    print(f"⚠️  Classic Structuring Pattern Detected")
    print(f"   Flagged Transactions: {classic_pattern['flagged_count']}")
    print(f"   Total Amount: ${classic_pattern['total_amount']:,.2f}")
    print(f"   Consistency Score: {classic_pattern['consistency_score']:.2%}")
```

#### Pattern 2: Temporal Clustering

```python
def detect_temporal_clustering(transactions: list, time_window_hours: int = 24) -> dict:
    """Detect multiple transactions within short time windows."""
    
    clusters = []
    time_window = timedelta(hours=time_window_hours)
    sorted_txns = sorted(transactions, key=lambda x: x['timestamp'])
    
    i = 0
    while i < len(sorted_txns):
        cluster_start = sorted_txns[i]['timestamp']
        cluster_end = cluster_start + time_window
        
        cluster_txns = []
        j = i
        while j < len(sorted_txns) and sorted_txns[j]['timestamp'] <= cluster_end:
            cluster_txns.append(sorted_txns[j])
            j += 1
        
        if len(cluster_txns) >= 2:
            cluster_total = sum(t['amount'] for t in cluster_txns)
            
            clusters.append({
                'start_time': cluster_start,
                'end_time': cluster_end,
                'transaction_count': len(cluster_txns),
                'total_amount': cluster_total,
                'exceeds_threshold': cluster_total >= 10000,
                'transactions': cluster_txns
            })
        
        i = j if j > i else i + 1
    
    significant_clusters = [
        c for c in clusters 
        if c['transaction_count'] >= 2 and c['total_amount'] >= 8000
    ]
    
    return {
        'pattern_detected': len(significant_clusters) > 0,
        'cluster_count': len(significant_clusters),
        'clusters': significant_clusters
    }

temporal_pattern = detect_temporal_clustering(transactions)

if temporal_pattern['pattern_detected']:
    print(f"⚠️  Temporal Clustering Detected")
    print(f"   Clusters: {temporal_pattern['cluster_count']}")
```

#### Pattern 3: Geographic Dispersion

```python
def detect_geographic_dispersion(transactions: list) -> dict:
    """Detect transactions across multiple locations."""
    
    from collections import defaultdict
    
    daily_locations = defaultdict(set)
    for txn in transactions:
        date = txn['timestamp'].date()
        location = txn.get('location', 'Unknown')
        if location != 'Unknown':
            daily_locations[date].add(location)
    
    multi_location_days = {
        date: locations 
        for date, locations in daily_locations.items() 
        if len(locations) >= 2
    }
    
    # Check for geographically impossible patterns
    impossible_patterns = []
    for date, locations in multi_location_days.items():
        day_txns = [t for t in transactions if t['timestamp'].date() == date]
        
        for i in range(len(day_txns) - 1):
            txn1, txn2 = day_txns[i], day_txns[i + 1]
            time_diff = (txn2['timestamp'] - txn1['timestamp']).total_seconds() / 60
            
            if txn1['location'] != txn2['location'] and time_diff < 30:
                impossible_patterns.append({
                    'txn1': txn1,
                    'txn2': txn2,
                    'time_diff_minutes': time_diff,
                    'locations': [txn1['location'], txn2['location']]
                })
    
    return {
        'pattern_detected': len(multi_location_days) > 0,
        'multi_location_days': len(multi_location_days),
        'total_locations': len(set(t['location'] for t in transactions if t.get('location'))),
        'impossible_patterns': impossible_patterns
    }

geographic_pattern = detect_geographic_dispersion(transactions)
```

#### Pattern 4: Smurfing (Multiple Individuals)

```python
def detect_smurfing_pattern(customer_id: str, lookback_days: int = 30) -> dict:
    """Detect coordinated structuring across multiple individuals."""
    
    # Find related persons
    related_persons = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .both('RELATED_TO', 'BUSINESS_ASSOCIATE', 'FAMILY_MEMBER')
            .hasLabel('Person')
            .dedup()
            .project('id', 'name', 'relationship')
            .by(values('customerId'))
            .by(values('name'))
            .by(inE().label())
    """)
    
    coordinated_activity = []
    
    for person in related_persons:
        person_txns = gather_transaction_history(person['id'], lookback_days)
        
        if person_txns:
            person_pattern = detect_classic_structuring(person_txns)
            
            if person_pattern['pattern_detected']:
                coordinated_activity.append({
                    'person': person,
                    'transaction_count': person_pattern['flagged_count'],
                    'total_amount': person_pattern['total_amount']
                })
    
    if len(coordinated_activity) >= 2:
        return {
            'pattern_detected': True,
            'involved_persons': len(coordinated_activity) + 1,
            'total_amount': sum(p['total_amount'] for p in coordinated_activity),
            'details': coordinated_activity
        }
    
    return {'pattern_detected': False}

smurfing_pattern = detect_smurfing_pattern(alert['customer_id'])
```

---

### Step 4: Calculate Risk Score

**Objective:** Quantify structuring risk based on detected patterns.

```python
def calculate_structuring_risk_score(
    classic_pattern: dict,
    temporal_pattern: dict,
    geographic_pattern: dict,
    smurfing_pattern: dict
) -> dict:
    """Calculate comprehensive structuring risk score."""
    
    score_components = {}
    
    # Pattern Strength (40%)
    pattern_score = 0.0
    if classic_pattern['pattern_detected']:
        pattern_score += classic_pattern['consistency_score'] * 0.15
        txn_factor = min(classic_pattern['flagged_count'] / 10, 1.0)
        pattern_score += txn_factor * 0.10
        amount_factor = min(classic_pattern['total_amount'] / 100000, 1.0)
        pattern_score += amount_factor * 0.15
    score_components['pattern_strength'] = pattern_score
    
    # Temporal Indicators (20%)
    temporal_score = 0.0
    if temporal_pattern['pattern_detected']:
        cluster_factor = min(temporal_pattern['cluster_count'] / 5, 1.0)
        temporal_score = cluster_factor * 0.20
    score_components['temporal_indicators'] = temporal_score
    
    # Geographic Dispersion (15%)
    geographic_score = 0.0
    if geographic_pattern['pattern_detected']:
        location_factor = min(geographic_pattern['total_locations'] / 5, 1.0)
        geographic_score += location_factor * 0.10
        if geographic_pattern['impossible_patterns']:
            geographic_score += 0.05
    score_components['geographic_dispersion'] = geographic_score
    
    # Coordination/Smurfing (25%)
    coordination_score = 0.0
    if smurfing_pattern['pattern_detected']:
        person_factor = min(smurfing_pattern['involved_persons'] / 5, 1.0)
        coordination_score = person_factor * 0.25
    score_components['coordination'] = coordination_score
    
    total_score = sum(score_components.values())
    
    # Risk classification
    if total_score >= 0.75:
        risk_level = 'CRITICAL'
    elif total_score >= 0.60:
        risk_level = 'HIGH'
    elif total_score >= 0.40:
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'
    
    return {
        'total_score': total_score,
        'risk_level': risk_level,
        'components': score_components,
        'sar_recommended': total_score >= 0.60
    }

risk_score = calculate_structuring_risk_score(
    classic_pattern, temporal_pattern, geographic_pattern, smurfing_pattern
)

print(f"\nRisk Score: {risk_score['total_score']:.2f}")
print(f"Risk Level: {risk_score['risk_level']}")
print(f"SAR Recommended: {'YES' if risk_score['sar_recommended'] else 'NO'}")
```

---

### Step 5: Prepare SAR Filing

**Objective:** Create Suspicious Activity Report if required.

```python
def prepare_sar_filing(evidence: dict, risk_score: dict) -> dict:
    """Prepare SAR filing package."""
    
    narrative = f"""
SUSPICIOUS ACTIVITY NARRATIVE

Subject: {evidence['customer_name']}
Account: {evidence['account_number']}

SUMMARY:
This SAR is filed due to suspected structuring activity designed to evade 
Currency Transaction Report (CTR) filing requirements under 31 U.S.C. § 5324.

ACTIVITY DESCRIPTION:
Between {evidence['start_date']} and {evidence['end_date']}, the subject 
conducted {evidence['transaction_count']} transactions totaling 
${evidence['total_amount']:,.2f}.

STRUCTURING INDICATORS:
- Multiple transactions just below $10,000 CTR threshold
- Consistent transaction amounts in $9,000-$9,999 range
- Pattern suggests deliberate avoidance of reporting requirements

RISK ASSESSMENT:
Risk Level: {risk_score['risk_level']}
Risk Score: {risk_score['total_score']:.2f}

This activity is inconsistent with the customer's stated occupation and 
income level, and appears designed to evade federal reporting requirements.
"""
    
    return {
        'filing_metadata': {
            'form_type': 'FinCEN SAR',
            'filing_date': datetime.now().isoformat(),
            'analyst': get_current_user()
        },
        'narrative': narrative.strip(),
        'suspicious_activity': {
            'activity_type': 'Structuring',
            'total_amount': evidence['total_amount'],
            'transaction_count': evidence['transaction_count']
        }
    }

if risk_score['sar_recommended']:
    sar_filing = prepare_sar_filing(evidence, risk_score)
    print(f"\n⚠️  SAR FILING REQUIRED")
```

---

## Real-World Examples

### Example 1: Classic Structuring - Retail Business

**Pattern:**
- 15 deposits over 20 days
- Amounts: $9,200, $9,500, $9,800, $9,300, $9,700
- All at same branch
- Total: $142,500

**Outcome:**
- Risk Level: HIGH
- SAR Filed: Yes
- Action: Enhanced monitoring

---

### Example 2: Smurfing - Organized Scheme

**Pattern:**
- 5 related individuals
- Each making 3-5 deposits of $9,000-$9,900
- Same 3-day period
- Different branches
- Total: $187,000

**Outcome:**
- Risk Level: CRITICAL
- SAR Filed: Yes (within 24 hours)
- Law Enforcement Notified: Yes

---

### Example 3: False Positive - Legitimate Business

**Pattern:**
- 20 deposits over 30 days
- Amounts: $3,000-$8,000 (variable)
- Consistent with daily receipts
- Restaurant business

**Outcome:**
- Risk Level: LOW
- SAR Filed: No
- Action: Documented as false positive

---

## Performance Metrics

| Metric | Target |
|--------|--------|
| Investigation Time | <4 hours |
| SAR Filing Time | <48 hours |
| False Positive Rate | <10% |
| Detection Rate | >95% |

---

## Integration

```python
from banking.aml.aml_detection import AMLDetector
from banking.compliance.audit_logger import get_audit_logger

# Log investigation
audit_logger = get_audit_logger()
audit_logger.log_compliance_event(
    event_type='STRUCTURING_INVESTIGATION_COMPLETE',
    user=get_current_user(),
    resource=f"customer:{customer_id}",
    metadata={'risk_score': risk_score['total_score']}
)
```

---

## Templates

See [`templates/sar-filing.md`](templates/sar-filing.md) for SAR template.

---

**Last Updated:** 2026-02-20  
**Version:** 1.0  
**Maintained By:** AML Compliance Team
