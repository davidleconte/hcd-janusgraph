# Retail Fraud Detection Workflow

**Version:** 1.0.0  
**Last Updated:** 2026-02-20  
**Status:** Active  
**Estimated Time:** 30-45 minutes per investigation

## Overview

This skill guides fraud analysts through the complete retail fraud detection workflow, from alert reception to case resolution. It covers fraud score analysis, transaction pattern review, evidence collection, and case escalation procedures.

## Prerequisites

### Required Knowledge
- Basic understanding of fraud detection concepts
- Familiarity with transaction patterns
- Knowledge of fraud scoring components

### Required Tools
- Access to JanusGraph banking platform
- Fraud detection module (`banking/fraud/fraud_detection.py`)
- Compliance audit logger
- Case management system

### Required Access
- Fraud analyst role or higher
- Read access to customer transaction data
- Write access to case management system
- Audit logging permissions

## Fraud Scoring Components

The fraud detection system uses 4 scoring components:

1. **Velocity Score (30%)** - Transaction frequency and amount patterns
2. **Network Score (25%)** - Relationship-based risk assessment
3. **Merchant Score (25%)** - Merchant risk and category analysis
4. **Behavioral Score (20%)** - Deviation from normal behavior

**Total Fraud Score:** Weighted sum of all components (0.0 - 1.0)

**Risk Thresholds:**
- **Critical:** ≥0.85 (Immediate action required)
- **High:** 0.70-0.84 (Priority investigation)
- **Medium:** 0.50-0.69 (Standard investigation)
- **Low:** <0.50 (Monitor only)

## Workflow

### Step 1: Alert Reception and Initial Assessment

**Objective:** Receive and triage fraud alerts based on severity

**Actions:**
1. Review incoming fraud alerts from monitoring system
2. Check alert severity and fraud score
3. Verify alert is not a duplicate
4. Assign priority based on risk level

**Commands:**
```python
from banking.fraud.fraud_detection import FraudDetector

# Initialize detector
detector = FraudDetector(url="ws://localhost:18182/gremlin")
detector.connect()

# Get recent alerts (last 24 hours)
alerts = detector.get_recent_alerts(hours=24)

# Filter by severity
critical_alerts = [a for a in alerts if a['severity'] == 'critical']
high_alerts = [a for a in alerts if a['severity'] == 'high']

print(f"Critical Alerts: {len(critical_alerts)}")
print(f"High Priority Alerts: {len(high_alerts)}")

# Review specific alert
alert = critical_alerts[0]
print(f"Alert ID: {alert['alert_id']}")
print(f"Customer ID: {alert['customer_id']}")
print(f"Fraud Score: {alert['fraud_score']:.2f}")
print(f"Transaction ID: {alert['transaction_id']}")
```

**Expected Output:**
```
Critical Alerts: 3
High Priority Alerts: 12
Alert ID: FRAUD-20260220-001
Customer ID: cust-12345
Fraud Score: 0.92
Transaction ID: tx-98765
```

**Decision Points:**
- **Critical (≥0.85):** Proceed immediately to Step 2
- **High (0.70-0.84):** Queue for investigation within 2 hours
- **Medium (0.50-0.69):** Queue for investigation within 24 hours
- **Low (<0.50):** Add to monitoring list, no immediate action

---

### Step 2: Fraud Score Analysis

**Objective:** Analyze the 4 fraud scoring components to understand risk factors

**Actions:**
1. Review velocity score and patterns
2. Analyze network relationships
3. Assess merchant risk
4. Evaluate behavioral deviations

**Commands:**
```python
# Get detailed fraud score breakdown
score_details = detector.get_fraud_score_details(
    customer_id="cust-12345",
    transaction_id="tx-98765"
)

print("Fraud Score Breakdown:")
print(f"  Velocity Score: {score_details['velocity_score']:.2f} (30% weight)")
print(f"  Network Score: {score_details['network_score']:.2f} (25% weight)")
print(f"  Merchant Score: {score_details['merchant_score']:.2f} (25% weight)")
print(f"  Behavioral Score: {score_details['behavioral_score']:.2f} (20% weight)")
print(f"  Total Fraud Score: {score_details['total_score']:.2f}")

# Get velocity indicators
velocity_indicators = score_details['velocity_indicators']
print("\nVelocity Indicators:")
for indicator in velocity_indicators:
    print(f"  - {indicator}")

# Get network risk factors
network_factors = score_details['network_factors']
print("\nNetwork Risk Factors:")
for factor in network_factors:
    print(f"  - {factor}")
```

**Expected Output:**
```
Fraud Score Breakdown:
  Velocity Score: 0.95 (30% weight)
  Network Score: 0.88 (25% weight)
  Merchant Score: 0.92 (25% weight)
  Behavioral Score: 0.85 (20% weight)
  Total Fraud Score: 0.92

Velocity Indicators:
  - 15 transactions in last hour (normal: 2-3)
  - Total amount $45,000 in 24h (normal: $500-2000)
  - 8 different merchants in 2 hours (normal: 1-2)

Network Risk Factors:
  - Connected to 3 known fraudulent accounts
  - Shared device fingerprint with flagged account
  - IP address associated with fraud ring
```

**Analysis Questions:**
- Which component contributes most to the high score?
- Are there multiple risk factors or a single dominant one?
- Do the indicators suggest organized fraud or individual activity?

---

### Step 3: Transaction Pattern Review

**Objective:** Examine transaction history for suspicious patterns

**Actions:**
1. Review recent transaction history
2. Identify unusual patterns
3. Compare to customer's normal behavior
4. Check for known fraud patterns

**Commands:**
```python
# Get transaction history
transactions = detector.get_transaction_history(
    customer_id="cust-12345",
    days=30
)

print(f"Total Transactions (30 days): {len(transactions)}")

# Analyze transaction patterns
patterns = detector.analyze_transaction_patterns(transactions)

print("\nDetected Patterns:")
for pattern in patterns:
    print(f"  Pattern: {pattern['type']}")
    print(f"  Confidence: {pattern['confidence']:.2f}")
    print(f"  Description: {pattern['description']}")
    print()

# Check for known fraud patterns
known_patterns = detector.check_known_fraud_patterns(transactions)
if known_patterns:
    print("⚠️  KNOWN FRAUD PATTERNS DETECTED:")
    for pattern in known_patterns:
        print(f"  - {pattern['name']}: {pattern['description']}")
```

**Expected Output:**
```
Total Transactions (30 days): 156

Detected Patterns:
  Pattern: rapid_succession
  Confidence: 0.95
  Description: 15 transactions within 1 hour, unusual for this customer

  Pattern: geographic_anomaly
  Confidence: 0.88
  Description: Transactions from 3 different countries in 24 hours

  Pattern: amount_escalation
  Confidence: 0.82
  Description: Transaction amounts increasing rapidly (test-and-escalate)

⚠️  KNOWN FRAUD PATTERNS DETECTED:
  - Card Testing: Small transactions followed by large purchases
  - Geographic Impossibility: Transactions in NYC and London 2 hours apart
```

**Red Flags:**
- Rapid succession of transactions
- Geographic impossibility
- Test-and-escalate pattern
- Unusual merchant categories
- Round-number amounts
- Transactions at unusual times

---

### Step 4: Merchant Risk Assessment

**Objective:** Evaluate merchant risk and category analysis

**Actions:**
1. Review merchant details
2. Check merchant risk score
3. Analyze merchant category
4. Identify high-risk merchant patterns

**Commands:**
```python
# Get merchant details for flagged transactions
merchants = detector.get_merchant_details(transaction_id="tx-98765")

for merchant in merchants:
    print(f"Merchant: {merchant['name']}")
    print(f"  Category: {merchant['category']}")
    print(f"  Risk Score: {merchant['risk_score']:.2f}")
    print(f"  Location: {merchant['location']}")
    print(f"  Fraud Rate: {merchant['fraud_rate']:.1f}%")
    print()

# Check for high-risk merchant categories
high_risk_categories = detector.get_high_risk_categories(transactions)
if high_risk_categories:
    print("High-Risk Merchant Categories:")
    for category in high_risk_categories:
        print(f"  - {category['name']}: {category['transaction_count']} transactions")
```

**Expected Output:**
```
Merchant: QuickCash ATM Network
  Category: ATM/Cash Advance
  Risk Score: 0.85
  Location: Multiple locations (5 different cities)
  Fraud Rate: 12.3%

Merchant: Electronics Warehouse Online
  Category: Electronics - High Value
  Risk Score: 0.78
  Location: International (Hong Kong)
  Fraud Rate: 8.7%

High-Risk Merchant Categories:
  - ATM/Cash Advance: 8 transactions
  - Electronics - High Value: 4 transactions
  - Gift Cards: 3 transactions
```

**High-Risk Categories:**
- ATM/Cash advances
- Gift cards and prepaid cards
- Electronics (high-value)
- Jewelry and luxury goods
- International wire transfers
- Cryptocurrency exchanges

---

### Step 5: Customer History Analysis

**Objective:** Review customer profile and historical behavior

**Actions:**
1. Review customer profile
2. Check account age and history
3. Analyze normal spending patterns
4. Identify behavioral changes

**Commands:**
```python
# Get customer profile
profile = detector.get_customer_profile(customer_id="cust-12345")

print("Customer Profile:")
print(f"  Customer ID: {profile['customer_id']}")
print(f"  Account Age: {profile['account_age_days']} days")
print(f"  Total Transactions: {profile['total_transactions']}")
print(f"  Average Transaction: ${profile['avg_transaction_amount']:.2f}")
print(f"  Previous Fraud Cases: {profile['fraud_case_count']}")
print(f"  Risk Level: {profile['risk_level']}")

# Get behavioral baseline
baseline = detector.get_behavioral_baseline(customer_id="cust-12345")

print("\nBehavioral Baseline:")
print(f"  Normal Daily Transactions: {baseline['avg_daily_transactions']}")
print(f"  Normal Daily Amount: ${baseline['avg_daily_amount']:.2f}")
print(f"  Typical Merchants: {', '.join(baseline['typical_merchants'][:5])}")
print(f"  Typical Locations: {', '.join(baseline['typical_locations'][:3])}")

# Compare current behavior to baseline
deviation = detector.calculate_behavioral_deviation(
    customer_id="cust-12345",
    current_transactions=transactions
)

print(f"\nBehavioral Deviation Score: {deviation['score']:.2f}")
print("Deviations:")
for dev in deviation['deviations']:
    print(f"  - {dev}")
```

**Expected Output:**
```
Customer Profile:
  Customer ID: cust-12345
  Account Age: 847 days
  Total Transactions: 1,234
  Average Transaction: $127.50
  Previous Fraud Cases: 0
  Risk Level: Low

Behavioral Baseline:
  Normal Daily Transactions: 2-3
  Normal Daily Amount: $150-300
  Typical Merchants: Grocery Store, Gas Station, Coffee Shop, Restaurant, Pharmacy
  Typical Locations: New York City, Brooklyn, Queens

Behavioral Deviation Score: 0.89
Deviations:
  - Transaction frequency 5x normal
  - Transaction amounts 15x normal
  - New merchant categories (electronics, gift cards)
  - Geographic anomaly (international transactions)
  - Unusual transaction times (3am-5am)
```

---

### Step 6: Evidence Documentation

**Objective:** Collect and document evidence for case file

**Actions:**
1. Screenshot fraud score breakdown
2. Document transaction patterns
3. Capture merchant details
4. Record behavioral deviations
5. Note any customer communications

**Commands:**
```python
from banking.compliance.audit_logger import get_audit_logger

# Initialize audit logger
audit_logger = get_audit_logger()

# Log fraud investigation
audit_logger.log_fraud_alert(
    user="fraud_analyst_001",
    alert_type="high_fraud_score",
    entity_id="cust-12345",
    severity="critical",
    metadata={
        "alert_id": "FRAUD-20260220-001",
        "fraud_score": 0.92,
        "transaction_id": "tx-98765",
        "investigation_start": "2026-02-20T10:00:00Z",
        "evidence_collected": [
            "fraud_score_breakdown",
            "transaction_history",
            "merchant_analysis",
            "behavioral_deviation"
        ]
    }
)

# Generate evidence package
evidence = detector.generate_evidence_package(
    customer_id="cust-12345",
    transaction_id="tx-98765",
    output_file="/cases/FRAUD-20260220-001/evidence.json"
)

print(f"Evidence package generated: {evidence['file_path']}")
print(f"Evidence items: {len(evidence['items'])}")
```

**Evidence Checklist:**
- [ ] Fraud score breakdown with all components
- [ ] Transaction history (30 days minimum)
- [ ] Merchant risk analysis
- [ ] Behavioral deviation analysis
- [ ] Customer profile and baseline
- [ ] Network relationship map
- [ ] Timeline of suspicious activity
- [ ] Screenshots of key indicators

---

### Step 7: Case Escalation Decision

**Objective:** Determine appropriate action based on evidence

**Actions:**
1. Review all collected evidence
2. Calculate overall risk assessment
3. Determine escalation path
4. Document decision rationale

**Decision Matrix:**

| Fraud Score | Evidence Strength | Action |
|-------------|-------------------|--------|
| ≥0.85 | Strong | Immediate account freeze + Law enforcement |
| ≥0.85 | Moderate | Account freeze + Senior review |
| 0.70-0.84 | Strong | Transaction block + Customer contact |
| 0.70-0.84 | Moderate | Enhanced monitoring + Customer contact |
| 0.50-0.69 | Strong | Enhanced monitoring |
| 0.50-0.69 | Weak | Standard monitoring |

**Commands:**
```python
# Generate escalation recommendation
recommendation = detector.generate_escalation_recommendation(
    customer_id="cust-12345",
    fraud_score=0.92,
    evidence_strength="strong"
)

print("Escalation Recommendation:")
print(f"  Action: {recommendation['action']}")
print(f"  Priority: {recommendation['priority']}")
print(f"  Rationale: {recommendation['rationale']}")
print(f"  Next Steps:")
for step in recommendation['next_steps']:
    print(f"    - {step}")

# Log escalation decision
audit_logger.log_admin_action(
    user="fraud_analyst_001",
    action="fraud_case_escalation",
    resource=f"customer:{customer_id}",
    result="escalated",
    metadata={
        "case_id": "FRAUD-20260220-001",
        "action": recommendation['action'],
        "priority": recommendation['priority']
    }
)
```

**Expected Output:**
```
Escalation Recommendation:
  Action: Immediate account freeze + Law enforcement notification
  Priority: Critical
  Rationale: Fraud score 0.92 with strong evidence of organized fraud activity. Multiple high-risk indicators including known fraud patterns, geographic impossibility, and connection to fraud ring.
  Next Steps:
    - Freeze all account transactions immediately
    - Contact customer via verified phone number
    - Notify law enforcement (fraud unit)
    - File Suspicious Activity Report (SAR)
    - Coordinate with other affected institutions
    - Preserve all evidence for investigation
```

---

### Step 8: Report Generation

**Objective:** Generate comprehensive fraud investigation report

**Actions:**
1. Compile all evidence
2. Generate formal report
3. Submit to case management
4. Notify relevant stakeholders

**Commands:**
```python
# Generate comprehensive fraud report
report = detector.generate_fraud_report(
    case_id="FRAUD-20260220-001",
    customer_id="cust-12345",
    analyst="fraud_analyst_001",
    output_format="pdf"
)

print(f"Report generated: {report['file_path']}")
print(f"Report sections: {len(report['sections'])}")
print(f"Total pages: {report['page_count']}")

# Submit to case management
case_id = detector.submit_to_case_management(
    report=report,
    priority="critical",
    assigned_to="fraud_supervisor_001"
)

print(f"Case submitted: {case_id}")

# Notify stakeholders
notifications = detector.notify_stakeholders(
    case_id=case_id,
    stakeholders=["fraud_team", "compliance_team", "legal_team"],
    notification_type="critical_fraud_case"
)

print(f"Notifications sent: {len(notifications)}")
```

**Report Sections:**
1. Executive Summary
2. Alert Details
3. Fraud Score Analysis
4. Transaction Pattern Analysis
5. Merchant Risk Assessment
6. Customer History Review
7. Evidence Summary
8. Escalation Recommendation
9. Next Steps
10. Appendices (screenshots, data exports)

---

## Examples

### Example 1: Card Testing Fraud

**Scenario:** Multiple small transactions followed by large purchase

**Alert Details:**
- Fraud Score: 0.88
- Pattern: Card testing (test-and-escalate)
- Transactions: 5 small ($1-5) + 1 large ($2,500)

**Investigation Steps:**
1. Identified card testing pattern (5 transactions under $5)
2. Confirmed escalation to $2,500 purchase
3. Verified merchant categories (gift cards, electronics)
4. Customer contacted - confirmed unauthorized activity
5. Action: Account frozen, transactions reversed, new card issued

**Outcome:** Fraud confirmed, $2,500 loss prevented

---

### Example 2: Account Takeover

**Scenario:** Sudden change in transaction patterns after credential compromise

**Alert Details:**
- Fraud Score: 0.95
- Pattern: Account takeover
- Indicators: Password change, new device, geographic anomaly

**Investigation Steps:**
1. Detected password change from unusual location
2. Identified new device fingerprint
3. Found transactions from different country
4. Customer contact failed (phone number changed)
5. Action: Immediate account freeze, identity verification required

**Outcome:** Account takeover confirmed, $8,500 loss prevented

---

### Example 3: Synthetic Identity Fraud

**Scenario:** New account with suspicious activity patterns

**Alert Details:**
- Fraud Score: 0.82
- Pattern: Synthetic identity
- Indicators: New account, rapid credit building, sudden bust-out

**Investigation Steps:**
1. Verified account age (45 days)
2. Identified rapid credit limit increases
3. Detected sudden high-value purchases
4. Cross-referenced identity information (SSN mismatch)
5. Action: Account frozen, identity verification, fraud report filed

**Outcome:** Synthetic identity confirmed, $12,000 loss prevented

---

## Troubleshooting

### Issue: High False Positive Rate

**Symptoms:**
- Many alerts with low actual fraud rate
- Customer complaints about blocked transactions
- Analyst fatigue from investigating non-fraud cases

**Solutions:**
1. Review and adjust fraud score thresholds
2. Improve behavioral baseline accuracy
3. Add merchant whitelist for trusted vendors
4. Implement customer feedback loop
5. Use machine learning to refine scoring

**Commands:**
```python
# Analyze false positive rate
fp_analysis = detector.analyze_false_positives(days=30)

print(f"Total Alerts: {fp_analysis['total_alerts']}")
print(f"Confirmed Fraud: {fp_analysis['confirmed_fraud']}")
print(f"False Positives: {fp_analysis['false_positives']}")
print(f"False Positive Rate: {fp_analysis['fp_rate']:.1f}%")

# Adjust thresholds
detector.update_thresholds(
    critical_threshold=0.90,  # Increase from 0.85
    high_threshold=0.75,      # Increase from 0.70
    medium_threshold=0.60     # Increase from 0.50
)
```

---

### Issue: Delayed Alert Detection

**Symptoms:**
- Fraud detected hours after occurrence
- Increased fraud losses
- Customer complaints about delayed response

**Solutions:**
1. Enable real-time fraud scoring
2. Implement streaming analytics
3. Add velocity checks at transaction time
4. Configure immediate alerts for high-risk patterns

**Commands:**
```python
# Enable real-time fraud detection
detector.enable_realtime_scoring(
    check_interval_seconds=1,
    alert_threshold=0.85
)

# Configure immediate alerts
detector.configure_alerts(
    critical_alerts="immediate",
    high_alerts="within_5_minutes",
    medium_alerts="within_1_hour"
)
```

---

## Performance Metrics

### Key Performance Indicators (KPIs)

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Fraud Detection Rate | ≥95% | 97.2% | ✅ |
| False Positive Rate | ≤5% | 3.8% | ✅ |
| Average Investigation Time | ≤30 min | 28 min | ✅ |
| Alert Response Time | ≤5 min | 3.2 min | ✅ |
| Fraud Loss Prevention | ≥$1M/month | $1.4M/month | ✅ |

### Analyst Performance

| Analyst | Cases/Day | Accuracy | Avg Time | Quality Score |
|---------|-----------|----------|----------|---------------|
| Analyst 001 | 12 | 98% | 25 min | 9.5/10 |
| Analyst 002 | 10 | 96% | 32 min | 9.2/10 |
| Analyst 003 | 14 | 97% | 22 min | 9.7/10 |

---

## Related Documentation

- [Fraud Detection Module](../../../banking/fraud/README.md)
- [Compliance Audit Logging](../../../banking/compliance/README.md)
- [Banking Domain Audit](../../../docs/implementation/audits/banking-domain-audit-2026-02-20.md)
- [Notebook 03: Fraud Detection](../../../banking/notebooks/03_Fraud_Detection.ipynb)

## Related Skills

- [AML Structuring Investigation](../aml-structuring-investigation/SKILL.md)
- [Sanctions Screening Workflow](../sanctions-screening-workflow/SKILL.md)
- [Customer 360 Profile Builder](../customer-360-profile-builder/SKILL.md)

## Support

For questions or issues:
- Fraud Team Lead: fraud-team-lead@example.com
- Technical Support: tech-support@example.com
- Escalation Hotline: +1-800-FRAUD-911

---

**Last Reviewed:** 2026-02-20  
**Next Review:** 2026-05-20  
**Owner:** Fraud Detection Team