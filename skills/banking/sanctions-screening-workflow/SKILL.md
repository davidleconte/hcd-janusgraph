# Sanctions Screening Workflow

**Skill Type:** Banking Domain - Compliance Screening  
**Complexity:** Advanced  
**Estimated Time:** 2-4 hours per screening batch  
**Prerequisites:** Understanding of sanctions regulations, screening requirements, false positive management

## Overview

This skill guides compliance analysts through sanctions screening - the process of checking customers, transactions, and counterparties against government sanctions lists (OFAC, UN, EU, etc.) to prevent prohibited transactions with sanctioned individuals, entities, or countries.

### Key Concepts

**Sanctions Lists:**
- **OFAC (Office of Foreign Assets Control):** US Treasury sanctions
- **UN Security Council:** United Nations sanctions
- **EU Sanctions:** European Union restrictive measures
- **HMT (UK Treasury):** UK financial sanctions
- **Country-Specific:** National sanctions programs

**Screening Types:**
- **Customer Screening:** Onboarding and periodic review
- **Transaction Screening:** Real-time payment screening
- **Batch Screening:** Periodic rescreening of customer base
- **Watchlist Screening:** Adverse media and PEP lists

**Match Types:**
- **Exact Match:** 100% name match
- **Fuzzy Match:** Partial match with similarity score
- **False Positive:** Non-sanctioned entity with similar name
- **True Positive:** Confirmed sanctions match

## Workflow Steps

### Step 1: Initiate Screening Request

**Objective:** Receive and validate screening request.

**Screening Triggers:**
- New customer onboarding
- Transaction initiation
- Periodic rescreening (quarterly/annual)
- Sanctions list update
- Customer profile change

**Request Types:**

```python
from banking.compliance.sanctions_screening import SanctionsScreener
from src.python.client.janusgraph_client import JanusGraphClient

# Initialize screener
graph_client = JanusGraphClient()
screener = SanctionsScreener(graph_client)

# Screen customer
customer_id = "customer-12345"
screening_result = screener.screen_customer(
    customer_id=customer_id,
    screening_type='ONBOARDING',  # or 'PERIODIC', 'TRANSACTION'
    lists=['OFAC', 'UN', 'EU']
)

print(f"Screening ID: {screening_result['screening_id']}")
print(f"Match Count: {screening_result['match_count']}")
print(f"Risk Level: {screening_result['risk_level']}")
```

---

### Step 2: Execute Fuzzy Name Matching

**Objective:** Compare entity name against sanctions lists using fuzzy matching algorithms.

**Matching Algorithm:**

```python
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz

def fuzzy_match_name(query_name: str, sanctions_name: str) -> dict:
    """
    Perform fuzzy name matching with multiple algorithms.
    
    Returns match score and algorithm details.
    """
    # Normalize names
    query_norm = normalize_name(query_name)
    sanctions_norm = normalize_name(sanctions_name)
    
    # Algorithm 1: Levenshtein distance (fuzzywuzzy)
    levenshtein_score = fuzz.ratio(query_norm, sanctions_norm) / 100.0
    
    # Algorithm 2: Token sort ratio (handles word order)
    token_sort_score = fuzz.token_sort_ratio(query_norm, sanctions_norm) / 100.0
    
    # Algorithm 3: Partial ratio (substring matching)
    partial_score = fuzz.partial_ratio(query_norm, sanctions_norm) / 100.0
    
    # Algorithm 4: Sequence matcher (Python built-in)
    sequence_score = SequenceMatcher(None, query_norm, sanctions_norm).ratio()
    
    # Weighted average (token_sort gets highest weight)
    weighted_score = (
        levenshtein_score * 0.25 +
        token_sort_score * 0.40 +
        partial_score * 0.20 +
        sequence_score * 0.15
    )
    
    return {
        'match_score': weighted_score,
        'levenshtein': levenshtein_score,
        'token_sort': token_sort_score,
        'partial': partial_score,
        'sequence': sequence_score,
        'threshold_met': weighted_score >= 0.85  # 85% threshold
    }

def normalize_name(name: str) -> str:
    """Normalize name for matching."""
    import re
    
    # Convert to uppercase
    name = name.upper()
    
    # Remove common business suffixes
    suffixes = ['INC', 'LLC', 'LTD', 'CORP', 'CO', 'SA', 'AG', 'GMBH']
    for suffix in suffixes:
        name = re.sub(rf'\b{suffix}\b\.?', '', name)
    
    # Remove special characters
    name = re.sub(r'[^\w\s]', ' ', name)
    
    # Normalize whitespace
    name = ' '.join(name.split())
    
    return name.strip()

# Execute matching
query_name = "ACME Corporation Ltd"
sanctions_name = "ACME Corp"

match_result = fuzzy_match_name(query_name, sanctions_name)
print(f"Match Score: {match_result['match_score']:.2%}")
print(f"Threshold Met: {match_result['threshold_met']}")
```

**Matching Thresholds:**
- **≥95%:** Exact match (immediate block)
- **85-94%:** High confidence match (manual review required)
- **70-84%:** Medium confidence match (enhanced review)
- **<70%:** Low confidence (likely false positive)

---

### Step 3: Screen Against Multiple Lists

**Objective:** Check entity against all relevant sanctions lists.

**List Screening:**

```python
def screen_against_all_lists(entity_name: str, entity_type: str = 'PERSON') -> list:
    """
    Screen entity against all sanctions lists.
    
    Args:
        entity_name: Name to screen
        entity_type: 'PERSON' or 'ENTITY'
    
    Returns:
        List of matches across all lists
    """
    sanctions_lists = {
        'OFAC_SDN': load_ofac_sdn_list(),
        'OFAC_NON_SDN': load_ofac_non_sdn_list(),
        'UN_CONSOLIDATED': load_un_consolidated_list(),
        'EU_SANCTIONS': load_eu_sanctions_list(),
        'UK_HMT': load_uk_hmt_list()
    }
    
    all_matches = []
    
    for list_name, sanctions_data in sanctions_lists.items():
        # Filter by entity type
        filtered_data = [
            entry for entry in sanctions_data 
            if entry['type'] == entity_type
        ]
        
        # Screen against filtered list
        for entry in filtered_data:
            match_result = fuzzy_match_name(entity_name, entry['name'])
            
            if match_result['threshold_met']:
                all_matches.append({
                    'list': list_name,
                    'entry_id': entry['id'],
                    'sanctioned_name': entry['name'],
                    'match_score': match_result['match_score'],
                    'program': entry.get('program', 'Unknown'),
                    'country': entry.get('country', 'Unknown'),
                    'added_date': entry.get('added_date'),
                    'remarks': entry.get('remarks', '')
                })
    
    # Sort by match score (highest first)
    all_matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return all_matches

# Execute screening
entity_name = "John Smith"
matches = screen_against_all_lists(entity_name, entity_type='PERSON')

print(f"Found {len(matches)} potential matches")
for match in matches[:5]:  # Top 5
    print(f"  {match['list']}: {match['sanctioned_name']} ({match['match_score']:.2%})")
```

---

### Step 4: Analyze Match Context

**Objective:** Gather additional context to assess match validity.

**Context Analysis:**

```python
def analyze_match_context(entity_id: str, match: dict) -> dict:
    """
    Analyze additional context for match assessment.
    
    Args:
        entity_id: Entity vertex ID
        match: Match dictionary from screening
    
    Returns:
        Context analysis
    """
    # Get entity details
    entity = graph_client.execute(f"""
        g.V('{entity_id}').valueMap(true)
    """)[0]
    
    # Compare attributes
    context = {
        'entity_name': entity['name'][0],
        'sanctioned_name': match['sanctioned_name'],
        'match_score': match['match_score'],
        'attribute_matches': {}
    }
    
    # Date of birth comparison (if available)
    if 'dateOfBirth' in entity and 'dob' in match:
        entity_dob = entity['dateOfBirth'][0]
        sanctions_dob = match['dob']
        context['attribute_matches']['dob'] = (entity_dob == sanctions_dob)
    
    # Nationality comparison
    if 'nationality' in entity and 'nationality' in match:
        entity_nat = set(entity['nationality'])
        sanctions_nat = set(match['nationality'])
        context['attribute_matches']['nationality'] = bool(entity_nat & sanctions_nat)
    
    # Address comparison
    if 'address' in entity and 'address' in match:
        entity_addr = entity['address'][0].upper()
        sanctions_addr = match['address'].upper()
        addr_match_score = fuzz.partial_ratio(entity_addr, sanctions_addr) / 100.0
        context['attribute_matches']['address'] = addr_match_score > 0.70
    
    # Calculate confidence score
    attribute_match_count = sum(context['attribute_matches'].values())
    total_attributes = len(context['attribute_matches'])
    
    if total_attributes > 0:
        context['confidence_score'] = (
            match['match_score'] * 0.60 +
            (attribute_match_count / total_attributes) * 0.40
        )
    else:
        context['confidence_score'] = match['match_score']
    
    # Determine match classification
    if context['confidence_score'] >= 0.95:
        context['classification'] = 'TRUE_POSITIVE'
    elif context['confidence_score'] >= 0.85:
        context['classification'] = 'PROBABLE_MATCH'
    elif context['confidence_score'] >= 0.70:
        context['classification'] = 'POSSIBLE_MATCH'
    else:
        context['classification'] = 'FALSE_POSITIVE'
    
    return context

# Analyze match
context = analyze_match_context(customer_id, matches[0])
print(f"Classification: {context['classification']}")
print(f"Confidence: {context['confidence_score']:.2%}")
```

---

### Step 5: False Positive Reduction

**Objective:** Filter out false positives using business rules and historical data.

**False Positive Rules:**

```python
def apply_false_positive_rules(entity_id: str, match: dict, context: dict) -> dict:
    """
    Apply false positive reduction rules.
    
    Returns updated classification and reasoning.
    """
    false_positive_indicators = []
    
    # Rule 1: Common name with no attribute matches
    if match['match_score'] < 0.90 and not any(context['attribute_matches'].values()):
        false_positive_indicators.append('COMMON_NAME_NO_ATTRIBUTES')
    
    # Rule 2: Different country with no connection
    entity_country = get_entity_country(entity_id)
    sanctions_country = match.get('country', 'Unknown')
    
    if entity_country != sanctions_country and entity_country not in ['Unknown', 'Multiple']:
        # Check for business connections to sanctions country
        has_connection = check_country_connection(entity_id, sanctions_country)
        if not has_connection:
            false_positive_indicators.append('DIFFERENT_COUNTRY_NO_CONNECTION')
    
    # Rule 3: Historical false positive
    historical_matches = get_historical_matches(entity_id, match['entry_id'])
    if historical_matches:
        previous_classification = historical_matches[-1]['classification']
        if previous_classification == 'FALSE_POSITIVE':
            false_positive_indicators.append('HISTORICAL_FALSE_POSITIVE')
    
    # Rule 4: Significant age difference
    if 'dob' in context['attribute_matches'] and not context['attribute_matches']['dob']:
        entity_age = calculate_age(entity['dateOfBirth'][0])
        sanctions_age = calculate_age(match['dob'])
        
        if abs(entity_age - sanctions_age) > 10:
            false_positive_indicators.append('SIGNIFICANT_AGE_DIFFERENCE')
    
    # Update classification if false positive indicators present
    if len(false_positive_indicators) >= 2:
        context['classification'] = 'LIKELY_FALSE_POSITIVE'
        context['false_positive_reasons'] = false_positive_indicators
    
    return context

# Apply rules
context = apply_false_positive_rules(customer_id, matches[0], context)
```

---

### Step 6: Escalate or Clear

**Objective:** Make screening decision and take appropriate action.

**Decision Matrix:**

```python
def make_screening_decision(context: dict) -> dict:
    """
    Make final screening decision.
    
    Returns decision and required actions.
    """
    classification = context['classification']
    confidence = context['confidence_score']
    
    if classification == 'TRUE_POSITIVE':
        decision = {
            'action': 'BLOCK',
            'priority': 'CRITICAL',
            'escalation': 'IMMEDIATE',
            'required_actions': [
                'Block all transactions',
                'Freeze accounts',
                'Notify OFAC within 10 days',
                'File blocking report',
                'Senior management notification'
            ],
            'timeline': '24 hours'
        }
    
    elif classification == 'PROBABLE_MATCH':
        decision = {
            'action': 'HOLD',
            'priority': 'HIGH',
            'escalation': 'COMPLIANCE_OFFICER',
            'required_actions': [
                'Hold transaction',
                'Enhanced due diligence',
                'Request additional documentation',
                'Manual review required',
                'Document decision rationale'
            ],
            'timeline': '48 hours'
        }
    
    elif classification == 'POSSIBLE_MATCH':
        decision = {
            'action': 'REVIEW',
            'priority': 'MEDIUM',
            'escalation': 'ANALYST',
            'required_actions': [
                'Manual review',
                'Compare additional attributes',
                'Check transaction history',
                'Document findings'
            ],
            'timeline': '5 business days'
        }
    
    else:  # FALSE_POSITIVE or LIKELY_FALSE_POSITIVE
        decision = {
            'action': 'CLEAR',
            'priority': 'LOW',
            'escalation': 'NONE',
            'required_actions': [
                'Document false positive',
                'Add to whitelist (if appropriate)',
                'Update screening rules'
            ],
            'timeline': 'Immediate'
        }
    
    return decision

# Make decision
decision = make_screening_decision(context)
print(f"Decision: {decision['action']}")
print(f"Priority: {decision['priority']}")
```

---

## Real-World Examples

### Example 1: True Positive - Exact Match

**Scenario:** Customer name exactly matches OFAC SDN list entry

```
Customer: "Viktor Bout"
OFAC Entry: "BOUT, Viktor"
Match Score: 98%
DOB Match: Yes
Nationality Match: Yes (Russia)
```

**Outcome:**
- Classification: TRUE_POSITIVE
- Action: BLOCK
- All accounts frozen
- OFAC notification filed

---

### Example 2: False Positive - Common Name

**Scenario:** Common name with no attribute matches

```
Customer: "John Smith" (US, DOB: 1985-03-15)
UN Entry: "SMITH, John" (Syria, DOB: 1960-07-22)
Match Score: 87%
DOB Match: No (25 year difference)
Nationality Match: No
Country Connection: No
```

**Outcome:**
- Classification: FALSE_POSITIVE
- Action: CLEAR
- Added to whitelist
- Documented for future screening

---

### Example 3: Probable Match - Requires Review

**Scenario:** High match score but missing attributes

```
Customer: "Ahmed Al-Rashid Trading LLC" (UAE)
EU Entry: "Al-Rashid Trading Company" (Syria)
Match Score: 91%
Country Match: No (but regional connection)
Business Type: Similar (import/export)
```

**Outcome:**
- Classification: PROBABLE_MATCH
- Action: HOLD
- Enhanced due diligence requested
- Compliance officer review required

---

## Performance Metrics

| Metric | Target |
|--------|--------|
| Screening Time | <5 seconds per entity |
| False Positive Rate | <5% |
| True Positive Detection | 100% |
| Review Time | <48 hours |

---

## Integration

```python
from banking.compliance.audit_logger import get_audit_logger

# Log screening
audit_logger = get_audit_logger()
audit_logger.log_compliance_event(
    event_type='SANCTIONS_SCREENING_COMPLETE',
    user=get_current_user(),
    resource=f"customer:{customer_id}",
    metadata={
        'matches_found': len(matches),
        'classification': context['classification'],
        'action': decision['action']
    }
)
```

---

## Templates

See [`templates/screening-report.md`](templates/screening-report.md) for screening report template.

---

**Last Updated:** 2026-02-20  
**Version:** 1.0  
**Maintained By:** Compliance Team