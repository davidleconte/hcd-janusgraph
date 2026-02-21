# Customer 360 Profile Builder

**Skill Type:** Banking Domain - Customer Intelligence  
**Complexity:** Intermediate  
**Estimated Time:** 1-2 hours per profile  
**Prerequisites:** Understanding of customer data sources, relationship mapping, risk assessment

## Overview

This skill guides analysts through building comprehensive Customer 360 profiles - unified views of customers that aggregate data from multiple sources to provide complete visibility into customer relationships, activities, risk factors, and value.

### Key Concepts

**Customer 360:** A complete, unified view of a customer across all touchpoints, products, and interactions.

**Data Sources:**
- Core banking systems (accounts, transactions)
- CRM systems (interactions, preferences)
- Risk systems (credit scores, fraud alerts)
- Compliance systems (KYC, sanctions screening)
- External data (credit bureaus, social media)

**Profile Components:**
- **Identity:** Basic customer information
- **Relationships:** Connections to other entities
- **Products:** Accounts, loans, investments
- **Activity:** Transactions, interactions
- **Risk:** Credit, fraud, compliance risk scores
- **Value:** Lifetime value, profitability

## Workflow Steps

### Step 1: Initiate Profile Build

**Objective:** Identify customer and gather basic information.

```python
from banking.analytics.customer_360 import Customer360Builder
from src.python.client.janusgraph_client import JanusGraphClient

# Initialize builder
graph_client = JanusGraphClient()
profile_builder = Customer360Builder(graph_client)

# Start profile build
customer_id = "customer-12345"
profile = profile_builder.build_profile(customer_id)

print(f"Building profile for: {profile['name']}")
print(f"Customer since: {profile['customer_since']}")
```

---

### Step 2: Aggregate Identity Data

**Objective:** Collect and consolidate customer identity information.

```python
def aggregate_identity_data(customer_id: str) -> dict:
    """Aggregate customer identity from multiple sources."""
    
    # Get core identity
    identity = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .project('basic', 'contact', 'demographics')
            .by(valueMap('name', 'dateOfBirth', 'ssn', 'customerId'))
            .by(valueMap('email', 'phone', 'mobilePhone'))
            .by(valueMap('occupation', 'income', 'employer'))
    """)[0]
    
    # Get addresses
    addresses = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .out('HAS_ADDRESS')
            .valueMap(true)
    """)
    
    # Get identification documents
    documents = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .out('HAS_DOCUMENT')
            .valueMap('type', 'number', 'issueDate', 'expiryDate')
    """)
    
    return {
        'basic_info': identity['basic'],
        'contact_info': identity['contact'],
        'demographics': identity['demographics'],
        'addresses': addresses,
        'documents': documents,
        'last_updated': datetime.now().isoformat()
    }

identity_data = aggregate_identity_data(customer_id)
```

---

### Step 3: Map Relationships

**Objective:** Identify and map all customer relationships.

```python
def map_customer_relationships(customer_id: str) -> dict:
    """Map all customer relationships."""
    
    relationships = {
        'family': [],
        'business': [],
        'accounts': [],
        'entities': []
    }
    
    # Family relationships
    family = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .both('FAMILY_MEMBER', 'SPOUSE', 'CHILD', 'PARENT')
            .project('id', 'name', 'relationship')
            .by(values('customerId'))
            .by(values('name'))
            .by(inE().label())
    """)
    relationships['family'] = family
    
    # Business relationships
    business = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .both('BUSINESS_ASSOCIATE', 'PARTNER', 'EMPLOYEE_OF')
            .project('id', 'name', 'type', 'relationship')
            .by(values('customerId'))
            .by(values('name'))
            .by(label)
            .by(inE().label())
    """)
    relationships['business'] = business
    
    # Account relationships (joint accounts, authorized users)
    accounts = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .out('OWNS', 'AUTHORIZED_ON')
            .hasLabel('Account')
            .project('account', 'type', 'role')
            .by(values('accountNumber'))
            .by(values('accountType'))
            .by(inE().label())
    """)
    relationships['accounts'] = accounts
    
    # Entity relationships (companies owned/controlled)
    entities = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .out('OWNS', 'CONTROLS', 'DIRECTOR_OF')
            .hasLabel('Company')
            .project('entity', 'name', 'role', 'ownership')
            .by(values('companyId'))
            .by(values('name'))
            .by(inE().label())
            .by(inE().values('percentage').fold())
    """)
    relationships['entities'] = entities
    
    return relationships

relationships = map_customer_relationships(customer_id)
print(f"Family: {len(relationships['family'])}")
print(f"Business: {len(relationships['business'])}")
print(f"Accounts: {len(relationships['accounts'])}")
print(f"Entities: {len(relationships['entities'])}")
```

---

### Step 4: Aggregate Product Holdings

**Objective:** Compile all products and services held by customer.

```python
def aggregate_product_holdings(customer_id: str) -> dict:
    """Aggregate all customer product holdings."""
    
    products = {
        'checking_accounts': [],
        'savings_accounts': [],
        'credit_cards': [],
        'loans': [],
        'investments': [],
        'insurance': []
    }
    
    # Get all accounts
    accounts = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .out('OWNS')
            .hasLabel('Account')
            .project('number', 'type', 'balance', 'status', 'opened')
            .by(values('accountNumber'))
            .by(values('accountType'))
            .by(values('balance'))
            .by(values('status'))
            .by(values('openDate'))
    """)
    
    # Categorize accounts
    for account in accounts:
        account_type = account['type'].lower()
        if 'checking' in account_type:
            products['checking_accounts'].append(account)
        elif 'savings' in account_type:
            products['savings_accounts'].append(account)
        elif 'credit' in account_type or 'card' in account_type:
            products['credit_cards'].append(account)
        elif 'loan' in account_type or 'mortgage' in account_type:
            products['loans'].append(account)
        elif 'investment' in account_type or 'brokerage' in account_type:
            products['investments'].append(account)
    
    # Calculate totals
    products['summary'] = {
        'total_accounts': len(accounts),
        'total_deposits': sum(
            a['balance'] for a in accounts 
            if a['type'] in ['CHECKING', 'SAVINGS']
        ),
        'total_credit': sum(
            a['balance'] for a in accounts 
            if 'CREDIT' in a['type']
        ),
        'total_loans': sum(
            a['balance'] for a in accounts 
            if 'LOAN' in a['type']
        )
    }
    
    return products

products = aggregate_product_holdings(customer_id)
print(f"Total Accounts: {products['summary']['total_accounts']}")
print(f"Total Deposits: ${products['summary']['total_deposits']:,.2f}")
```

---

### Step 5: Analyze Activity Patterns

**Objective:** Analyze customer transaction and interaction patterns.

```python
def analyze_activity_patterns(customer_id: str, lookback_days: int = 90) -> dict:
    """Analyze customer activity patterns."""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    # Get transaction activity
    transactions = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .out('OWNS')
            .outE('TRANSACTION')
            .has('timestamp', gte({start_date.timestamp()}))
            .project('type', 'amount', 'timestamp', 'location')
            .by(values('type'))
            .by(values('amount'))
            .by(values('timestamp'))
            .by(values('location'))
    """)
    
    # Analyze patterns
    activity = {
        'transaction_count': len(transactions),
        'total_volume': sum(t['amount'] for t in transactions),
        'average_transaction': sum(t['amount'] for t in transactions) / len(transactions) if transactions else 0,
        'transaction_types': {},
        'locations': set(),
        'time_patterns': {
            'weekday': 0,
            'weekend': 0,
            'business_hours': 0,
            'after_hours': 0
        }
    }
    
    # Categorize transactions
    for txn in transactions:
        # By type
        txn_type = txn['type']
        if txn_type not in activity['transaction_types']:
            activity['transaction_types'][txn_type] = {'count': 0, 'volume': 0}
        activity['transaction_types'][txn_type]['count'] += 1
        activity['transaction_types'][txn_type]['volume'] += txn['amount']
        
        # By location
        activity['locations'].add(txn['location'])
        
        # By time
        txn_time = datetime.fromtimestamp(txn['timestamp'])
        if txn_time.weekday() < 5:
            activity['time_patterns']['weekday'] += 1
        else:
            activity['time_patterns']['weekend'] += 1
        
        if 9 <= txn_time.hour < 17:
            activity['time_patterns']['business_hours'] += 1
        else:
            activity['time_patterns']['after_hours'] += 1
    
    activity['locations'] = list(activity['locations'])
    
    return activity

activity = analyze_activity_patterns(customer_id)
print(f"Transactions: {activity['transaction_count']}")
print(f"Total Volume: ${activity['total_volume']:,.2f}")
```

---

### Step 6: Calculate Risk Scores

**Objective:** Aggregate risk scores from multiple dimensions.

```python
def calculate_comprehensive_risk(customer_id: str) -> dict:
    """Calculate comprehensive customer risk score."""
    
    risk_scores = {}
    
    # Credit risk
    credit_score = get_credit_score(customer_id)
    risk_scores['credit'] = {
        'score': credit_score,
        'rating': classify_credit_score(credit_score)
    }
    
    # Fraud risk
    fraud_alerts = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .in('SUBJECT_OF')
            .hasLabel('FraudAlert')
            .count()
    """)[0]
    
    risk_scores['fraud'] = {
        'alert_count': fraud_alerts,
        'risk_level': 'HIGH' if fraud_alerts > 0 else 'LOW'
    }
    
    # AML risk
    aml_alerts = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .in('SUBJECT_OF')
            .hasLabel('AMLAlert')
            .count()
    """)[0]
    
    risk_scores['aml'] = {
        'alert_count': aml_alerts,
        'risk_level': 'HIGH' if aml_alerts > 0 else 'LOW'
    }
    
    # Sanctions risk
    sanctions_matches = check_sanctions_screening(customer_id)
    risk_scores['sanctions'] = {
        'matches': len(sanctions_matches),
        'risk_level': 'CRITICAL' if sanctions_matches else 'LOW'
    }
    
    # Calculate overall risk
    risk_factors = [
        1.0 if risk_scores['credit']['score'] < 600 else 0.0,
        1.0 if risk_scores['fraud']['alert_count'] > 0 else 0.0,
        1.0 if risk_scores['aml']['alert_count'] > 0 else 0.0,
        1.0 if risk_scores['sanctions']['matches'] > 0 else 0.0
    ]
    
    overall_risk_score = sum(risk_factors) / len(risk_factors)
    
    if overall_risk_score >= 0.75:
        overall_risk = 'CRITICAL'
    elif overall_risk_score >= 0.50:
        overall_risk = 'HIGH'
    elif overall_risk_score >= 0.25:
        overall_risk = 'MEDIUM'
    else:
        overall_risk = 'LOW'
    
    return {
        'scores': risk_scores,
        'overall_score': overall_risk_score,
        'overall_risk': overall_risk
    }

risk = calculate_comprehensive_risk(customer_id)
print(f"Overall Risk: {risk['overall_risk']}")
```

---

### Step 7: Calculate Customer Value

**Objective:** Determine customer lifetime value and profitability.

```python
def calculate_customer_value(customer_id: str) -> dict:
    """Calculate customer lifetime value."""
    
    # Get account balances
    balances = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .out('OWNS')
            .values('balance')
            .sum()
    """)[0] if graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .out('OWNS')
            .values('balance')
    """) else 0
    
    # Get revenue (fees, interest)
    revenue = calculate_annual_revenue(customer_id)
    
    # Get relationship length
    customer_since = graph_client.execute(f"""
        g.V().has('Person', 'customerId', '{customer_id}')
            .values('customerSince')
    """)[0]
    
    relationship_years = (datetime.now() - datetime.fromisoformat(customer_since)).days / 365
    
    # Calculate CLV (simplified)
    annual_value = revenue
    retention_rate = 0.85  # Assumed
    discount_rate = 0.10
    
    clv = annual_value * (retention_rate / (1 + discount_rate - retention_rate))
    
    return {
        'total_balances': balances,
        'annual_revenue': revenue,
        'relationship_years': relationship_years,
        'lifetime_value': clv,
        'value_segment': classify_value_segment(clv)
    }

value = calculate_customer_value(customer_id)
print(f"Lifetime Value: ${value['lifetime_value']:,.2f}")
print(f"Segment: {value['value_segment']}")
```

---

### Step 8: Generate Profile Report

**Objective:** Create comprehensive Customer 360 profile report.

```python
def generate_profile_report(
    customer_id: str,
    identity: dict,
    relationships: dict,
    products: dict,
    activity: dict,
    risk: dict,
    value: dict
) -> dict:
    """Generate complete Customer 360 profile."""
    
    profile = {
        'profile_id': f"C360-{customer_id}-{datetime.now().strftime('%Y%m%d')}",
        'generated_date': datetime.now().isoformat(),
        'customer_id': customer_id,
        
        'identity': identity,
        'relationships': relationships,
        'products': products,
        'activity': activity,
        'risk': risk,
        'value': value,
        
        'summary': {
            'name': identity['basic_info']['name'][0],
            'customer_since': identity['basic_info'].get('customerSince', ['Unknown'])[0],
            'total_accounts': products['summary']['total_accounts'],
            'total_value': products['summary']['total_deposits'],
            'risk_level': risk['overall_risk'],
            'value_segment': value['value_segment'],
            'relationship_count': (
                len(relationships['family']) +
                len(relationships['business']) +
                len(relationships['entities'])
            )
        }
    }
    
    return profile

# Generate complete profile
profile = generate_profile_report(
    customer_id, identity_data, relationships,
    products, activity, risk, value
)

print(f"\nCustomer 360 Profile Generated")
print(f"Profile ID: {profile['profile_id']}")
print(f"Risk Level: {profile['summary']['risk_level']}")
print(f"Value Segment: {profile['summary']['value_segment']}")
```

---

## Real-World Example

**High-Value Customer Profile:**

```
Name: Sarah Johnson
Customer Since: 2015-03-15 (9 years)
Accounts: 5 (Checking, Savings, Credit Card, Mortgage, Investment)
Total Deposits: $250,000
Total Credit: $15,000
Mortgage Balance: $350,000
Investment Portfolio: $500,000

Relationships:
- Spouse: John Johnson (joint checking)
- Business: Owner of Johnson Consulting LLC
- Family: 2 children (college savings accounts)

Activity (90 days):
- Transactions: 145
- Average: $1,250
- Locations: 3 branches, online banking

Risk:
- Credit Score: 780 (Excellent)
- Fraud Alerts: 0
- AML Alerts: 0
- Sanctions: Clear

Value:
- Annual Revenue: $8,500
- Lifetime Value: $72,250
- Segment: Platinum
```

---

## Performance Metrics

| Metric | Target |
|--------|--------|
| Profile Build Time | <30 seconds |
| Data Completeness | >95% |
| Update Frequency | Daily |
| Accuracy | >99% |

---

## Integration

```python
from banking.compliance.audit_logger import get_audit_logger

# Log profile access
audit_logger = get_audit_logger()
audit_logger.log_data_access(
    user=get_current_user(),
    resource=f"customer:{customer_id}",
    action="profile_view",
    result="success"
)
```

---

## Templates

See [`templates/customer-profile.md`](templates/customer-profile.md) for profile template.

---

**Last Updated:** 2026-02-20  
**Version:** 1.0  
**Maintained By:** Customer Intelligence Team