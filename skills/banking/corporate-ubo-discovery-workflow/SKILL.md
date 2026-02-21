# Corporate UBO Discovery Workflow

**Skill Type:** Banking Domain - Compliance Investigation  
**Complexity:** Advanced  
**Estimated Time:** 2-4 hours per investigation  
**Prerequisites:** Understanding of corporate structures, beneficial ownership regulations, graph traversal

## Overview

This skill guides compliance analysts through the process of discovering Ultimate Beneficial Owners (UBOs) of corporate entities using graph-based ownership analysis. UBO discovery is critical for:

- **KYC/AML Compliance:** Identifying individuals who ultimately control or benefit from corporate entities
- **Regulatory Requirements:** Meeting FATF, EU 4AMLD/5AMLD, FinCEN beneficial ownership rules
- **Risk Assessment:** Understanding true ownership for sanctions screening and PEP identification
- **Due Diligence:** Enhanced due diligence for high-risk jurisdictions and complex structures

### Key Concepts

**Ultimate Beneficial Owner (UBO):** An individual who:
- Owns or controls ≥25% of shares/voting rights (EU threshold)
- Owns or controls ≥10% of shares/voting rights (US FinCEN threshold for certain entities)
- Exercises control through other means (board representation, contractual arrangements)

**Ownership Chain:** The path from a target entity through intermediate entities to individual beneficial owners.

**Control Mechanisms:**
- Direct ownership (shareholding)
- Indirect ownership (through intermediaries)
- Voting rights
- Board representation
- Contractual control

## Workflow Steps

### Step 1: Initiate UBO Discovery Request

**Objective:** Receive and validate the UBO discovery request for a corporate entity.

**Input:**
- Company identifier (registration number, LEI, internal ID)
- Jurisdiction
- Investigation reason (onboarding, periodic review, alert-triggered)
- Required ownership threshold (typically 25% or 10%)

**Actions:**

```python
from banking.analytics.detect_ubo import UBODiscovery
from src.python.client.janusgraph_client import JanusGraphClient

# Initialize clients
graph_client = JanusGraphClient()
ubo_discovery = UBODiscovery(graph_client)

# Retrieve company entity
company_id = "company-12345"
company = graph_client.execute(
    f"g.V().has('Company', 'companyId', '{company_id}').valueMap(true)"
)

# Validate company exists
if not company:
    raise ValueError(f"Company {company_id} not found in graph")

print(f"Initiating UBO discovery for: {company['name'][0]}")
print(f"Jurisdiction: {company['jurisdiction'][0]}")
print(f"Registration: {company['registrationNumber'][0]}")
```

**Output:**
- Company entity validated
- Investigation case created
- Ownership threshold confirmed

**Compliance Note:** Document the legal basis for the investigation (regulatory requirement, risk-based trigger, periodic review).

---

### Step 2: Map Direct Ownership Structure

**Objective:** Identify all direct shareholders and their ownership percentages.

**Query Pattern:**

```python
# Get direct shareholders (1-hop ownership)
direct_owners = graph_client.execute(f"""
    g.V().has('Company', 'companyId', '{company_id}')
        .in('OWNS')
        .project('owner', 'ownership', 'type')
        .by(valueMap(true))
        .by(inE('OWNS').values('percentage'))
        .by(label)
""")

# Categorize by owner type
individuals = []
companies = []

for owner in direct_owners:
    owner_type = owner['type']
    ownership_pct = owner['ownership']
    
    if owner_type == 'Person':
        individuals.append({
            'id': owner['owner']['id'],
            'name': owner['owner']['name'][0],
            'ownership': ownership_pct,
            'hops': 1
        })
    elif owner_type == 'Company':
        companies.append({
            'id': owner['owner']['id'],
            'name': owner['owner']['name'][0],
            'ownership': ownership_pct,
            'hops': 1
        })

print(f"Direct individual owners: {len(individuals)}")
print(f"Direct corporate owners: {len(companies)}")
```

**Analysis:**
- Identify individuals meeting threshold (potential UBOs)
- Identify corporate owners requiring further traversal
- Calculate total ownership accounted for
- Flag ownership gaps (nominee shareholders, bearer shares)

**Red Flags:**
- Ownership <100% with no explanation
- Nominee shareholders without disclosed principals
- Ownership through high-risk jurisdictions
- Complex circular ownership structures

---

### Step 3: Traverse Multi-Hop Ownership Chains

**Objective:** Follow ownership chains through intermediate entities to identify ultimate individual owners.

**Algorithm:**

```python
def traverse_ownership_chain(company_id: str, threshold: float = 0.25, max_hops: int = 10):
    """
    Traverse ownership chain to find UBOs.
    
    Args:
        company_id: Starting company ID
        threshold: Minimum ownership percentage (0.25 = 25%)
        max_hops: Maximum traversal depth
    
    Returns:
        List of UBOs with ownership percentages and paths
    """
    ubos = []
    visited = set()
    
    def traverse(entity_id: str, cumulative_ownership: float, path: list, hops: int):
        if hops > max_hops:
            return
        
        if entity_id in visited:
            # Circular ownership detected
            return
        
        visited.add(entity_id)
        
        # Get owners of current entity
        owners = graph_client.execute(f"""
            g.V('{entity_id}')
                .in('OWNS')
                .project('id', 'type', 'name', 'ownership')
                .by(id)
                .by(label)
                .by(values('name'))
                .by(inE('OWNS').values('percentage'))
        """)
        
        for owner in owners:
            # Calculate effective ownership
            effective_ownership = cumulative_ownership * owner['ownership']
            
            if effective_ownership < threshold:
                continue  # Below threshold, skip
            
            new_path = path + [{
                'entity': owner['name'],
                'ownership': owner['ownership'],
                'effective': effective_ownership
            }]
            
            if owner['type'] == 'Person':
                # Found individual owner
                ubos.append({
                    'person_id': owner['id'],
                    'name': owner['name'],
                    'effective_ownership': effective_ownership,
                    'path': new_path,
                    'hops': hops + 1
                })
            else:
                # Continue traversing
                traverse(owner['id'], effective_ownership, new_path, hops + 1)
    
    # Start traversal
    traverse(company_id, 1.0, [], 0)
    
    return ubos

# Execute traversal
ubos = traverse_ownership_chain(company_id, threshold=0.25, max_hops=10)

print(f"Found {len(ubos)} UBOs meeting 25% threshold")
for ubo in ubos:
    print(f"  {ubo['name']}: {ubo['effective_ownership']:.2%} (via {ubo['hops']} hops)")
```

**Key Considerations:**
- **Cumulative Ownership:** Multiply ownership percentages along the chain
- **Circular Ownership:** Detect and handle circular references
- **Multiple Paths:** Same individual may appear through multiple paths (aggregate ownership)
- **Threshold Application:** Apply threshold to effective ownership, not each hop

---

### Step 4: Aggregate Ownership Across Multiple Paths

**Objective:** Consolidate ownership when the same individual appears through multiple ownership chains.

**Aggregation Logic:**

```python
def aggregate_ubo_ownership(ubos: list) -> list:
    """
    Aggregate ownership for individuals appearing in multiple paths.
    
    Args:
        ubos: List of UBO records with paths
    
    Returns:
        Consolidated UBO list with total ownership
    """
    from collections import defaultdict
    
    # Group by person_id
    ownership_by_person = defaultdict(lambda: {
        'name': None,
        'paths': [],
        'total_ownership': 0.0
    })
    
    for ubo in ubos:
        person_id = ubo['person_id']
        ownership_by_person[person_id]['name'] = ubo['name']
        ownership_by_person[person_id]['paths'].append({
            'ownership': ubo['effective_ownership'],
            'path': ubo['path'],
            'hops': ubo['hops']
        })
        ownership_by_person[person_id]['total_ownership'] += ubo['effective_ownership']
    
    # Convert to list
    consolidated_ubos = []
    for person_id, data in ownership_by_person.items():
        consolidated_ubos.append({
            'person_id': person_id,
            'name': data['name'],
            'total_ownership': data['total_ownership'],
            'path_count': len(data['paths']),
            'paths': data['paths']
        })
    
    # Sort by ownership percentage
    consolidated_ubos.sort(key=lambda x: x['total_ownership'], reverse=True)
    
    return consolidated_ubos

# Aggregate ownership
consolidated_ubos = aggregate_ubo_ownership(ubos)

print("\nConsolidated UBO Ownership:")
for ubo in consolidated_ubos:
    print(f"{ubo['name']}: {ubo['total_ownership']:.2%} (via {ubo['path_count']} paths)")
```

**Validation:**
- Total ownership should not exceed 100% (unless multiple share classes)
- Check for double-counting in complex structures
- Verify ownership percentages against source documents

---

### Step 5: Enrich UBO Profiles with Risk Data

**Objective:** Gather additional information about identified UBOs for risk assessment.

**Data Points to Collect:**

```python
def enrich_ubo_profile(person_id: str) -> dict:
    """
    Enrich UBO profile with risk-relevant data.
    
    Args:
        person_id: Person vertex ID
    
    Returns:
        Enriched profile dictionary
    """
    # Get person details
    person = graph_client.execute(f"""
        g.V('{person_id}')
            .project('basic', 'addresses', 'nationalities', 'accounts', 'relationships')
            .by(valueMap(true))
            .by(out('HAS_ADDRESS').valueMap(true).fold())
            .by(values('nationality').fold())
            .by(out('OWNS').hasLabel('Account').count())
            .by(both().hasLabel('Person').dedup().count())
    """)[0]
    
    # Check PEP status
    is_pep = check_pep_status(person_id)
    
    # Check sanctions lists
    sanctions_hits = check_sanctions_lists(person['basic']['name'][0])
    
    # Get adverse media
    adverse_media = search_adverse_media(person['basic']['name'][0])
    
    # Calculate risk score
    risk_score = calculate_ubo_risk_score(
        is_pep=is_pep,
        sanctions_hits=len(sanctions_hits),
        adverse_media_count=len(adverse_media),
        high_risk_jurisdictions=any(
            addr['country'][0] in HIGH_RISK_COUNTRIES 
            for addr in person['addresses']
        )
    )
    
    return {
        'person_id': person_id,
        'name': person['basic']['name'][0],
        'date_of_birth': person['basic'].get('dateOfBirth', [None])[0],
        'nationalities': person['nationalities'],
        'addresses': person['addresses'],
        'is_pep': is_pep,
        'sanctions_hits': sanctions_hits,
        'adverse_media_count': len(adverse_media),
        'risk_score': risk_score,
        'account_count': person['accounts'],
        'relationship_count': person['relationships']
    }

# Enrich all UBOs
enriched_ubos = []
for ubo in consolidated_ubos:
    profile = enrich_ubo_profile(ubo['person_id'])
    profile['ownership'] = ubo['total_ownership']
    profile['paths'] = ubo['paths']
    enriched_ubos.append(profile)

# Sort by risk score
enriched_ubos.sort(key=lambda x: x['risk_score'], reverse=True)
```

**Risk Factors:**
- **PEP Status:** Politically Exposed Person (high risk)
- **Sanctions:** OFAC, UN, EU sanctions lists
- **Adverse Media:** Negative news, criminal proceedings
- **High-Risk Jurisdictions:** FATF blacklist, tax havens
- **Complex Structures:** Excessive layers, offshore entities

---

### Step 6: Identify Control Beyond Ownership

**Objective:** Detect control mechanisms beyond direct ownership (voting rights, board seats, contractual control).

**Control Mechanisms to Check:**

```python
def analyze_control_mechanisms(company_id: str, person_id: str) -> dict:
    """
    Analyze non-ownership control mechanisms.
    
    Args:
        company_id: Company vertex ID
        person_id: Person vertex ID
    
    Returns:
        Control analysis dictionary
    """
    control_mechanisms = {
        'board_representation': False,
        'voting_rights': 0.0,
        'contractual_control': False,
        'management_control': False
    }
    
    # Check board membership
    board_positions = graph_client.execute(f"""
        g.V('{person_id}')
            .out('DIRECTOR_OF')
            .has('companyId', '{company_id}')
            .count()
    """)[0]
    
    control_mechanisms['board_representation'] = board_positions > 0
    
    # Check voting rights (may differ from ownership)
    voting_rights = graph_client.execute(f"""
        g.V('{person_id}')
            .outE('OWNS')
            .has('targetCompany', '{company_id}')
            .values('votingRights')
            .sum()
    """)
    
    if voting_rights:
        control_mechanisms['voting_rights'] = voting_rights[0]
    
    # Check management positions
    management_roles = graph_client.execute(f"""
        g.V('{person_id}')
            .out('MANAGES')
            .has('companyId', '{company_id}')
            .count()
    """)[0]
    
    control_mechanisms['management_control'] = management_roles > 0
    
    # Check contractual control (power of attorney, trust arrangements)
    contractual_control = graph_client.execute(f"""
        g.V('{person_id}')
            .outE('CONTROLS')
            .has('targetCompany', '{company_id}')
            .count()
    """)[0]
    
    control_mechanisms['contractual_control'] = contractual_control > 0
    
    return control_mechanisms

# Analyze control for each UBO
for ubo in enriched_ubos:
    control = analyze_control_mechanisms(company_id, ubo['person_id'])
    ubo['control_mechanisms'] = control
    
    # Determine if UBO based on control (even if <25% ownership)
    ubo['is_ubo_by_control'] = (
        control['board_representation'] or
        control['voting_rights'] >= 0.25 or
        control['contractual_control'] or
        control['management_control']
    )
```

**Control Indicators:**
- Board representation (especially chairman, CEO)
- Voting rights exceeding ownership percentage
- Power of attorney or proxy arrangements
- Trust beneficiary status
- Management control (CEO, CFO, COO)

---

### Step 7: Generate UBO Report

**Objective:** Create comprehensive UBO disclosure report for compliance records.

**Report Structure:**

```python
def generate_ubo_report(
    company_id: str,
    enriched_ubos: list,
    threshold: float,
    investigation_date: str
) -> dict:
    """
    Generate comprehensive UBO report.
    
    Args:
        company_id: Company vertex ID
        enriched_ubos: List of enriched UBO profiles
        threshold: Ownership threshold used
        investigation_date: Date of investigation
    
    Returns:
        UBO report dictionary
    """
    # Get company details
    company = graph_client.execute(f"""
        g.V('{company_id}').valueMap(true)
    """)[0]
    
    # Filter UBOs meeting threshold or control criteria
    qualifying_ubos = [
        ubo for ubo in enriched_ubos
        if ubo['ownership'] >= threshold or ubo['is_ubo_by_control']
    ]
    
    # Calculate ownership coverage
    total_ownership = sum(ubo['ownership'] for ubo in qualifying_ubos)
    
    report = {
        'report_metadata': {
            'report_id': f"UBO-{company_id}-{investigation_date}",
            'investigation_date': investigation_date,
            'analyst': get_current_user(),
            'threshold_applied': threshold,
            'regulatory_basis': 'EU 4AMLD Article 3(6)'
        },
        'company_information': {
            'company_id': company_id,
            'name': company['name'][0],
            'registration_number': company['registrationNumber'][0],
            'jurisdiction': company['jurisdiction'][0],
            'incorporation_date': company.get('incorporationDate', [None])[0]
        },
        'ubo_summary': {
            'total_ubos_identified': len(qualifying_ubos),
            'ownership_coverage': total_ownership,
            'high_risk_ubos': sum(1 for ubo in qualifying_ubos if ubo['risk_score'] > 0.7),
            'pep_ubos': sum(1 for ubo in qualifying_ubos if ubo['is_pep']),
            'sanctions_hits': sum(len(ubo['sanctions_hits']) for ubo in qualifying_ubos)
        },
        'ubos': [
            {
                'name': ubo['name'],
                'date_of_birth': ubo['date_of_birth'],
                'nationalities': ubo['nationalities'],
                'ownership_percentage': ubo['ownership'],
                'ownership_paths': len(ubo['paths']),
                'control_mechanisms': ubo['control_mechanisms'],
                'is_pep': ubo['is_pep'],
                'risk_score': ubo['risk_score'],
                'risk_classification': classify_risk(ubo['risk_score'])
            }
            for ubo in qualifying_ubos
        ],
        'ownership_structure': {
            'direct_owners': len([ubo for ubo in qualifying_ubos if ubo['paths'][0]['hops'] == 1]),
            'indirect_owners': len([ubo for ubo in qualifying_ubos if ubo['paths'][0]['hops'] > 1]),
            'max_ownership_depth': max(path['hops'] for ubo in qualifying_ubos for path in ubo['paths']),
            'complex_structure': any(len(ubo['paths']) > 1 for ubo in qualifying_ubos)
        },
        'risk_assessment': {
            'overall_risk': calculate_overall_ubo_risk(qualifying_ubos),
            'risk_factors': identify_risk_factors(qualifying_ubos, company),
            'recommended_actions': generate_recommendations(qualifying_ubos, company)
        },
        'compliance_status': {
            'ubo_disclosure_complete': total_ownership >= 0.75,  # 75% threshold
            'verification_required': [
                ubo['name'] for ubo in qualifying_ubos 
                if ubo['risk_score'] > 0.7 or ubo['is_pep']
            ],
            'next_review_date': calculate_next_review_date(qualifying_ubos)
        }
    }
    
    return report

# Generate report
report = generate_ubo_report(
    company_id=company_id,
    enriched_ubos=enriched_ubos,
    threshold=0.25,
    investigation_date=datetime.now().isoformat()
)

# Save report
save_ubo_report(report, output_path='reports/ubo/')
```

**Report Sections:**
1. **Executive Summary:** Key findings, UBO count, risk level
2. **Company Information:** Entity details, jurisdiction, registration
3. **UBO Disclosure:** Each UBO with ownership percentage and control mechanisms
4. **Ownership Structure:** Diagram showing ownership chains
5. **Risk Assessment:** Individual and aggregate risk scores
6. **Compliance Status:** Verification requirements, next review date
7. **Supporting Documentation:** Source documents, verification evidence

---

### Step 8: Document and Escalate High-Risk Findings

**Objective:** Escalate high-risk UBOs and document findings for compliance records.

**Escalation Criteria:**

```python
def determine_escalation_level(ubo: dict) -> str:
    """
    Determine escalation level based on risk factors.
    
    Args:
        ubo: Enriched UBO profile
    
    Returns:
        Escalation level: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    """
    # Critical escalation
    if ubo['sanctions_hits']:
        return 'CRITICAL'
    
    if ubo['is_pep'] and ubo['ownership'] >= 0.50:
        return 'CRITICAL'
    
    # High escalation
    if ubo['is_pep'] or ubo['risk_score'] > 0.8:
        return 'HIGH'
    
    if ubo['adverse_media_count'] > 5:
        return 'HIGH'
    
    # Medium escalation
    if ubo['risk_score'] > 0.6:
        return 'MEDIUM'
    
    # Low risk
    return 'LOW'

# Escalate high-risk UBOs
for ubo in enriched_ubos:
    escalation_level = determine_escalation_level(ubo)
    
    if escalation_level in ['CRITICAL', 'HIGH']:
        escalate_ubo_finding(
            ubo=ubo,
            company_id=company_id,
            escalation_level=escalation_level,
            reason=generate_escalation_reason(ubo)
        )
        
        # Log audit event
        audit_logger.log_compliance_event(
            event_type='UBO_HIGH_RISK_IDENTIFIED',
            user=get_current_user(),
            resource=f"company:{company_id}",
            metadata={
                'ubo_name': ubo['name'],
                'ownership': ubo['ownership'],
                'risk_score': ubo['risk_score'],
                'escalation_level': escalation_level
            }
        )
```

**Escalation Actions:**
- **CRITICAL:** Immediate senior management notification, freeze onboarding, file SAR if applicable
- **HIGH:** Compliance officer review within 24 hours, enhanced due diligence required
- **MEDIUM:** Standard enhanced due diligence, additional documentation required
- **LOW:** Standard due diligence, periodic monitoring

---

## Real-World Examples

### Example 1: Simple Direct Ownership

**Scenario:** Small business with 2 individual owners

```
Company A (Target)
├── Person 1: 60% ownership → UBO (direct)
└── Person 2: 40% ownership → UBO (direct)
```

**Analysis:**
- Both individuals meet 25% threshold
- Direct ownership (1 hop)
- Simple structure, low complexity
- Standard due diligence required

**Query:**

```python
ubos = graph_client.execute("""
    g.V().has('Company', 'companyId', 'company-a')
        .in('OWNS')
        .hasLabel('Person')
        .project('name', 'ownership')
        .by(values('name'))
        .by(inE('OWNS').values('percentage'))
""")

# Result: [
#   {'name': 'John Smith', 'ownership': 0.60},
#   {'name': 'Jane Doe', 'ownership': 0.40}
# ]
```

---

### Example 2: Multi-Tier Corporate Structure

**Scenario:** Target company owned through holding companies

```
Company A (Target)
├── Company B: 80% ownership
│   ├── Person 1: 50% → Effective: 40% (UBO)
│   └── Person 2: 50% → Effective: 40% (UBO)
└── Person 3: 20% ownership → UBO (direct)
```

**Analysis:**
- Person 1: 40% effective ownership (0.80 × 0.50)
- Person 2: 40% effective ownership (0.80 × 0.50)
- Person 3: 20% direct ownership (below threshold but may qualify by control)
- 2-hop ownership chain for Persons 1 & 2

**Query:**

```python
# Multi-hop traversal
ubos = traverse_ownership_chain('company-a', threshold=0.25, max_hops=5)

# Result: [
#   {'name': 'Person 1', 'effective_ownership': 0.40, 'hops': 2},
#   {'name': 'Person 2', 'effective_ownership': 0.40, 'hops': 2},
#   {'name': 'Person 3', 'effective_ownership': 0.20, 'hops': 1}
# ]
```

---

### Example 3: Complex Offshore Structure with PEP

**Scenario:** Target company with offshore holding structure and PEP involvement

```
Company A (Target - UK)
├── Company B (BVI): 100% ownership
    ├── Trust (Jersey): 60% ownership
    │   └── Person 1 (Beneficiary, PEP): 100% → Effective: 60% (UBO, HIGH RISK)
    └── Company C (Panama): 40% ownership
        └── Person 2: 100% → Effective: 40% (UBO)
```

**Analysis:**
- Person 1: 60% effective ownership through trust structure
- Person 1 is PEP → HIGH RISK escalation
- Offshore jurisdictions (BVI, Jersey, Panama) → Enhanced due diligence
- Trust structure → Verify beneficiary status
- Person 2: 40% effective ownership through Panama company

**Risk Factors:**
- PEP involvement
- Multiple offshore jurisdictions
- Trust structure (potential nominee arrangements)
- 3-hop ownership chain (complexity)

**Enhanced Due Diligence Required:**
- Source of wealth verification
- Trust deed review
- Beneficial ownership certification
- Ongoing monitoring (quarterly)

---

## Troubleshooting

### Issue: Circular Ownership Detected

**Symptom:** Traversal algorithm encounters circular reference (Company A owns Company B, Company B owns Company A)

**Solution:**

```python
def traverse_with_cycle_detection(entity_id: str, visited: set = None):
    if visited is None:
        visited = set()
    
    if entity_id in visited:
        # Circular ownership detected
        log_circular_ownership(entity_id, visited)
        return []
    
    visited.add(entity_id)
    
    # Continue traversal
    owners = get_owners(entity_id)
    # ... rest of traversal logic
```

**Prevention:**
- Maintain visited set during traversal
- Log circular ownership for manual review
- Flag as high-risk structure

---

### Issue: Ownership Totals Exceed 100%

**Symptom:** Aggregated ownership percentages exceed 100%

**Causes:**
- Multiple share classes with different voting rights
- Convertible securities not properly accounted for
- Data quality issues (incorrect percentages)

**Solution:**

```python
def validate_ownership_totals(company_id: str):
    total_ownership = graph_client.execute(f"""
        g.V('{company_id}')
            .inE('OWNS')
            .values('percentage')
            .sum()
    """)[0]
    
    if total_ownership > 1.0:
        # Investigate discrepancy
        owners = get_all_owners(company_id)
        log_ownership_discrepancy(company_id, total_ownership, owners)
        
        # Flag for manual review
        flag_for_review(company_id, reason='OWNERSHIP_EXCEEDS_100')
```

---

### Issue: No UBOs Identified (Ownership Gap)

**Symptom:** Ownership chains terminate at corporate entities, no individuals found

**Causes:**
- Nominee shareholders without disclosed principals
- Bearer shares
- Incomplete data
- Offshore structures with privacy protections

**Solution:**

```python
def identify_ownership_gaps(company_id: str, ubos: list):
    total_ownership = sum(ubo['ownership'] for ubo in ubos)
    
    if total_ownership < 0.75:  # Less than 75% ownership identified
        # Flag as incomplete UBO disclosure
        flag_incomplete_disclosure(
            company_id=company_id,
            identified_ownership=total_ownership,
            gap=1.0 - total_ownership
        )
        
        # Require additional documentation
        request_additional_documentation(
            company_id=company_id,
            required_docs=[
                'Shareholder register',
                'Nominee agreements',
                'Trust deeds',
                'Beneficial ownership declaration'
            ]
        )
```

**Actions:**
- Request certified shareholder register
- Require beneficial ownership declaration
- Conduct enhanced due diligence
- Consider declining relationship if disclosure inadequate

---

## Performance Metrics

### Investigation Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Investigation Time** | <4 hours | Time from request to report completion |
| **UBO Identification Rate** | >90% | Percentage of cases with complete UBO disclosure |
| **Data Quality** | >95% | Accuracy of ownership percentages |
| **Escalation Rate** | 10-15% | Percentage of cases requiring escalation |

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **False Positives** | <5% | UBOs incorrectly identified |
| **False Negatives** | <2% | UBOs missed during investigation |
| **Regulatory Compliance** | 100% | Adherence to UBO disclosure requirements |
| **Review Cycle Time** | <24 hours | Time for high-risk case review |

### Risk Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **PEP Detection Rate** | 100% | PEPs identified in UBO population |
| **Sanctions Hit Rate** | 100% | Sanctions matches identified |
| **High-Risk Jurisdiction Flag** | 100% | Offshore structures flagged |

---

## Integration with Other Modules

### AML Module Integration

```python
from banking.aml.aml_detection import AMLDetector

# Check UBOs for AML alerts
aml_detector = AMLDetector(graph_client)

for ubo in enriched_ubos:
    aml_alerts = aml_detector.check_person_alerts(ubo['person_id'])
    
    if aml_alerts:
        ubo['aml_alerts'] = aml_alerts
        ubo['risk_score'] += 0.2  # Increase risk score
```

### Compliance Module Integration

```python
from banking.compliance.audit_logger import get_audit_logger

audit_logger = get_audit_logger()

# Log UBO discovery completion
audit_logger.log_compliance_event(
    event_type='UBO_DISCOVERY_COMPLETE',
    user=get_current_user(),
    resource=f"company:{company_id}",
    metadata={
        'ubos_identified': len(enriched_ubos),
        'high_risk_count': sum(1 for ubo in enriched_ubos if ubo['risk_score'] > 0.7),
        'investigation_time_minutes': investigation_time
    }
)
```

### Sanctions Screening Integration

```python
from banking.compliance.sanctions_screening import screen_entity

# Screen all UBOs against sanctions lists
for ubo in enriched_ubos:
    sanctions_result = screen_entity(
        name=ubo['name'],
        date_of_birth=ubo['date_of_birth'],
        nationalities=ubo['nationalities']
    )
    
    ubo['sanctions_screening'] = sanctions_result
```

---

## Regulatory References

### EU 4th Anti-Money Laundering Directive (4AMLD)

**Article 3(6) - Beneficial Owner Definition:**
- Natural person who ultimately owns or controls ≥25% of shares or voting rights
- Natural person who exercises control through other means

**Article 30 - Beneficial Ownership Registers:**
- Member states must maintain central registers of beneficial ownership
- Information must be accessible to competent authorities and FIUs

### EU 5th Anti-Money Laundering Directive (5AMLD)

**Enhanced Transparency:**
- Beneficial ownership registers accessible to persons with legitimate interest
- Reduced threshold for high-risk third countries (10%)

### FinCEN Beneficial Ownership Rule (US)

**Threshold:** ≥25% ownership or control
**Reporting:** Required for legal entities created or registered in the US
**Exemptions:** Publicly traded companies, regulated entities

### FATF Recommendations

**Recommendation 24:** Countries should ensure adequate transparency of beneficial ownership
**Recommendation 25:** Countries should prevent misuse of bearer shares and nominee arrangements

---

## Templates

See [`templates/ubo-report.md`](templates/ubo-report.md) for the complete UBO disclosure report template.

---

## Related Skills

- **AML Structuring Investigation:** Detect structuring patterns in UBO-related accounts
- **Sanctions Screening Workflow:** Screen UBOs against sanctions lists
- **Customer 360 Profile Builder:** Build comprehensive profiles for UBOs

---

**Last Updated:** 2026-02-20  
**Version:** 1.0  
**Maintained By:** Banking Compliance Team