# Multi-Product Fraud Ring Detection

**Version:** 1.0.0  
**Last Updated:** 2026-03-24  
**Complexity:** VERY HIGH  
**Estimated Time:** 2-4 hours per investigation  
**Skill Level:** Senior Fraud Analyst / Graph Data Scientist

---

## Overview

Detect and dismantle sophisticated fraud rings operating across multiple banking products (accounts, credit cards, loans, mortgages). This skill addresses organized crime networks that exploit product silos to maximize fraud while staying below detection thresholds.

### Why This Is High Complexity

| Complexity Factor | Description |
|-------------------|-------------|
| **Multi-Product Scope** | Crosses account, card, loan, mortgage systems |
| **Temporal Patterns** | Tracks fraud ring lifecycle over months/years |
| **Identity Fragmentation** | Same actor with multiple synthetic identities |
| **Coordination Detection** | Identifies orchestrated activity across entities |
| **Regulatory Overlay** | SAR/CTR filing across multiple jurisdictions |
| **Network Scale** | 100-1000+ entities in sophisticated rings |
| **Adversarial Behavior** | Rings adapt to detection patterns |

---

## Prerequisites

### Required Knowledge
- Graph theory (centrality, community detection, path analysis)
- Fraud patterns (bust-out, synthetic identity, loan stacking, card testing)
- Regulatory requirements (BSA/AML, SAR filing)
- ML concepts (anomaly detection, clustering, time series)

### Required Tools
- JanusGraph with Gremlin traversal engine
- Graph ML infrastructure (`banking/analytics/graph_ml.py`)
- Community detection (`banking/analytics/community_detection.py`)
- Compliance audit logger
- Case management system

### Required Access
- Senior fraud analyst role
- Cross-product data access (accounts, cards, loans, mortgages)
- Identity verification services
- Law enforcement liaison permissions

---

## Fraud Ring Lifecycle Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FRAUD RING LIFECYCLE (12-24 months)                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PHASE 1: SEEDING (Month 1-3)                                           │
│  ┌──────────┐                                                           │
│  │ Synthetic │──► Create identities with fabricated SSNs, DOBs         │
│  │ Identities│──► Establish credit history with small accounts         │
│  └──────────┘──► Build trust scores through on-time payments           │
│                                                                          │
│  PHASE 2: CULTIVATION (Month 4-9)                                       │
│  ┌──────────┐                                                           │
│  │ Credit    │──► Open multiple credit cards across banks              │
│  │ Building  │──► Apply for personal loans, auto loans                 │
│  └──────────┘──► Establish relationships between identities            │
│                                                                          │
│  PHASE 3: EXPANSION (Month 10-15)                                       │
│  ┌──────────┐                                                           │
│  │ Product   │──► Add authorized users to maximize credit lines        │
│  │ Prolifer- │──► Apply for mortgages, business loans                  │
│  │ ation     │──► Cross-product coordination                            │
│  └──────────┘                                                           │
│                                                                          │
│  PHASE 4: BUST-OUT (Month 16-24)                                        │
│  ┌──────────┐                                                           │
│  │ Coordinated│──► Max out all credit lines simultaneously             │
│  │ Extraction│──► Cash out through ATMs, wire transfers               │
│  └──────────┘──► Disappear before detection                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Graph Schema for Multi-Product Detection

### Vertex Types

```gremlin
// Core entities
Person          // Natural persons (real + synthetic)
Company         // Shell companies for corporate layering
Account         // Deposit accounts
CreditCard      // Credit card accounts
Loan            // Personal/auto/student loans
Mortgage        // Mortgage loans
Device          // Device fingerprints
Address         // Physical addresses
PhoneNumber     // Phone numbers
Email           // Email addresses
IPAddress       // IP addresses

// External reference
ExternalRef     // Third-party identifiers (SSN, passport, etc.)
```

### Edge Types

```gremlin
// Ownership/Identity
owns_account        // Person -> Account
owns_card           // Person -> CreditCard
has_loan            // Person -> Loan
has_mortgage        // Person -> Mortgage
director_of         // Person -> Company
owns_share          // Person -> Company (percentage)

// Contact/Location
has_address         // Entity -> Address
has_phone           // Entity -> PhoneNumber
has_email           // Entity -> Email
used_ip             // Entity -> IPAddress
used_device         // Entity -> Device

// Financial Relationships
transfers_to        // Account -> Account
paid_to             // Account/CreditCard -> Entity
authorized_user     // CreditCard -> Person
co_applicant        // Loan/Mortgage -> Person

// Shared Attributes
same_ssn            // Person -> Person (synthetic identity link)
same_device         // Entity -> Entity
same_address        // Entity -> Entity
same_phone          // Entity -> Entity
```

---

## Detection Algorithms

### Algorithm 1: Multi-Product Network Centrality Analysis

Detect fraud ring coordinators using multi-dimensional centrality.

```python
from banking.analytics.graph_ml import GraphMLEngine
import numpy as np
from typing import Dict, List, Tuple, Set
from collections import defaultdict

class MultiProductFraudRingDetector:
    """
    Detects fraud rings operating across multiple banking products.
    
    Uses multi-dimensional centrality analysis:
    - Degree centrality: Number of cross-product connections
    - Betweenness centrality: Broker role in ring
    - Temporal centrality: Activity timing coordination
    - Financial centrality: Transaction volume concentration
    """
    
    def __init__(self, client, min_ring_size: int = 5, time_window_days: int = 365):
        self.client = client
        self.min_ring_size = min_ring_size
        self.time_window_days = time_window_days
        
    def detect_rings(self) -> List[Dict]:
        """
        Main detection pipeline.
        
        Returns:
            List of detected fraud rings with risk scores and entities.
        """
        # Step 1: Build cross-product adjacency
        cross_product_graph = self._build_cross_product_graph()
        
        # Step 2: Calculate multi-dimensional centrality
        centrality_scores = self._calculate_centrality(cross_product_graph)
        
        # Step 3: Identify coordinator nodes
        coordinators = self._identify_coordinators(centrality_scores)
        
        # Step 4: Extract rings around coordinators
        rings = self._extract_rings(coordinators, cross_product_graph)
        
        # Step 5: Calculate ring risk scores
        scored_rings = self._score_rings(rings)
        
        return sorted(scored_rings, key=lambda r: r['risk_score'], reverse=True)
    
    def _build_cross_product_graph(self) -> Dict[str, Set[str]]:
        """
        Build adjacency graph across all products.
        
        Includes:
        - Direct ownership (Person -> Product)
        - Shared attributes (same_device, same_address, etc.)
        - Financial relationships (transfers, authorized_users)
        """
        graph = defaultdict(set)
        
        # Person -> Product edges
        person_product_query = """
            g.V().hasLabel('person').as('p').
            union(
                out('owns_account'),
                out('owns_card'),
                out('has_loan'),
                out('has_mortgage')
            ).as('product').
            select('p', 'product').
            by('personId').
            by('accountId')  // or cardId, loanId, mortgageId
        """
        
        # Shared attribute edges
        shared_attr_query = """
            g.V().hasLabel('person', 'account', 'creditCard', 'loan', 'mortgage').
            match(
                __.as('e1').out('has_address').as('addr'),
                __.as('e2').out('has_address').as('addr')
            ).
            where('e1', neq('e2')).
            select('e1', 'e2').
            by(elementMap())
        """
        
        # Device sharing
        device_sharing_query = """
            g.V().hasLabel('device').as('d').
            in('used_device').as('e1').
            in('used_device').as('e2').
            where('e1', neq('e2')).
            select('e1', 'e2').
            by(elementMap())
        """
        
        # Execute queries and build graph
        # ... (implementation details)
        
        return dict(graph)
    
    def _calculate_centrality(self, graph: Dict) -> Dict[str, Dict[str, float]]:
        """
        Calculate multi-dimensional centrality for each node.
        
        Dimensions:
        1. Degree centrality: Cross-product connection count
        2. Betweenness centrality: Broker role
        3. Temporal centrality: Activity coordination score
        4. Financial centrality: Transaction volume
        """
        centrality = {}
        
        for node_id in graph.keys():
            centrality[node_id] = {
                'degree': self._degree_centrality(node_id, graph),
                'betweenness': self._betweenness_centrality(node_id, graph),
                'temporal': self._temporal_centrality(node_id),
                'financial': self._financial_centrality(node_id),
                'composite': 0.0  # Calculated below
            }
            
            # Composite score (weighted)
            weights = {
                'degree': 0.25,
                'betweenness': 0.30,
                'temporal': 0.20,
                'financial': 0.25
            }
            
            centrality[node_id]['composite'] = sum(
                centrality[node_id][k] * v for k, v in weights.items()
            )
        
        return centrality
    
    def _temporal_centrality(self, node_id: str) -> float:
        """
        Calculate temporal coordination score.
        
        High score indicates:
        - Activity timed with other entities
        - Coordinated application timing
        - Synchronized bust-out timing
        """
        # Get all timestamped events for this node
        events_query = f"""
            g.V('{node_id}').
            union(
                outE('owns_account', 'owns_card', 'has_loan').values('since'),
                outE('transfers_to').values('timestamp'),
                inE('authorized_user').values('since')
            ).
            order().
            toList()
        """
        
        events = self.client.execute(events_query)
        
        if not events or len(events) < 2:
            return 0.0
        
        # Calculate timing clusters
        # ... implementation
        
        return 0.0  # Placeholder
    
    def _financial_centrality(self, node_id: str) -> float:
        """
        Calculate financial flow centrality.
        
        Measures:
        - Total transaction volume through node
        - Ratio of incoming vs outgoing funds
        - Cash-out ratio for bust-out detection
        """
        # Get financial flows
        flows_query = f"""
            g.V('{node_id}').
            union(
                outE('transfers_to').values('amount').sum(),
                inE('transfers_to').values('amount').sum()
            ).
            toList()
        """
        
        flows = self.client.execute(flows_query)
        
        # Calculate centrality based on volume and patterns
        # ... implementation
        
        return 0.0  # Placeholder
    
    def _identify_coordinators(
        self, 
        centrality_scores: Dict[str, Dict[str, float]],
        threshold: float = 0.75
    ) -> List[Tuple[str, float]]:
        """
        Identify likely ring coordinators.
        
        Coordinators exhibit:
        - High composite centrality (> threshold)
        - High betweenness (broker role)
        - Multiple cross-product connections
        """
        coordinators = []
        
        for node_id, scores in centrality_scores.items():
            if scores['composite'] >= threshold and scores['betweenness'] >= 0.6:
                coordinators.append((node_id, scores['composite']))
        
        return sorted(coordinators, key=lambda x: x[1], reverse=True)
    
    def _extract_rings(
        self, 
        coordinators: List[Tuple[str, float]],
        graph: Dict[str, Set[str]],
        max_depth: int = 3
    ) -> List[Dict]:
        """
        Extract fraud rings around coordinator nodes.
        
        Uses breadth-first expansion with:
        - Product type tracking
        - Relationship type tracking
        - Temporal clustering
        """
        rings = []
        visited = set()
        
        for coordinator_id, score in coordinators:
            if coordinator_id in visited:
                continue
            
            # BFS to find ring members
            ring_members = self._bfs_ring_extraction(
                coordinator_id, graph, visited, max_depth
            )
            
            if len(ring_members) >= self.min_ring_size:
                rings.append({
                    'coordinator_id': coordinator_id,
                    'coordinator_score': score,
                    'members': list(ring_members),
                    'size': len(ring_members)
                })
                
                visited.update(ring_members)
        
        return rings
    
    def _score_rings(self, rings: List[Dict]) -> List[Dict]:
        """
        Calculate risk scores for detected rings.
        
        Risk factors:
        - Ring size (larger = higher risk)
        - Product diversity (more products = higher risk)
        - Total exposure (credit limits + loan amounts)
        - Temporal coordination (synchronized activity = higher risk)
        - Known fraud patterns detected
        """
        for ring in rings:
            # Calculate product diversity
            product_types = self._get_product_types(ring['members'])
            ring['product_types'] = product_types
            ring['product_diversity'] = len(product_types)
            
            # Calculate total exposure
            ring['total_exposure'] = self._calculate_exposure(ring['members'])
            
            # Detect fraud patterns
            ring['detected_patterns'] = self._detect_patterns(ring)
            
            # Calculate composite risk score
            ring['risk_score'] = self._calculate_risk_score(ring)
            
            # Assign risk level
            if ring['risk_score'] >= 0.85:
                ring['risk_level'] = 'critical'
            elif ring['risk_score'] >= 0.70:
                ring['risk_level'] = 'high'
            elif ring['risk_score'] >= 0.50:
                ring['risk_level'] = 'medium'
            else:
                ring['risk_level'] = 'low'
        
        return rings
```

### Algorithm 2: Synthetic Identity Network Detection

```python
def detect_synthetic_identity_networks(self) -> List[Dict]:
    """
    Detect synthetic identity fraud networks.
    
    Synthetic identities share:
    - Fabricated SSNs (often using valid area codes with invalid group numbers)
    - Shared addresses/phones during "cultivation" phase
    - Coordinated credit building patterns
    - Eventual bust-out coordination
    """
    networks = []
    
    # Step 1: Find SSN anomalies
    ssn_anomaly_query = """
        g.V().hasLabel('person').has('ssn').
        group().
        by('ssn').
        by(count()).
        where(select(values).is(gt(1)))
    """
    # SSNs used by multiple persons = potential synthetic cluster
    
    # Step 2: Find shared contact info
    shared_contact_query = """
        g.V().hasLabel('person').as('p1').
        out('has_phone', 'has_email', 'has_address').as('contact').
        in('has_phone', 'has_email', 'has_address').as('p2').
        where('p1', neq('p2')).
        group().
        by(select('contact')).
        by(select('p1', 'p2').by('personId').fold())
    """
    
    # Step 3: Find credit building coordination
    # Multiple identities opening accounts at similar times
    
    # Step 4: Find bust-out signals
    # Sudden max-out of credit across multiple identities
    
    return networks
```

### Algorithm 3: Temporal Pattern Mining

```python
def detect_temporal_coordination(
    self, 
    entity_ids: List[str],
    time_window: timedelta = timedelta(days=7)
) -> Dict:
    """
    Detect coordinated timing patterns across entities.
    
    Patterns:
    - Application clustering: Multiple applications in short window
    - Payment synchronization: Same-day payments across accounts
    - Bust-out coordination: Simultaneous max-out events
    - Communication bursts: Coordinated contact patterns
    """
    
    # Get all timestamped events
    events = []
    for entity_id in entity_ids:
        entity_events = self._get_entity_events(entity_id)
        events.extend(entity_events)
    
    # Sort by timestamp
    events.sort(key=lambda e: e['timestamp'])
    
    # Detect clusters
    clusters = self._cluster around
    # Cluster events
    clusters = self._cluster_events_by_time(events, time_window)
    
    # Calculate coordination score
    # High score = events are not randomly distributed
    coordination_score = self._calculate_coordination_score(clusters)
    
    return {
        'entity_ids': entity_ids,
        'event_count': len(events),
        'cluster_count': len(clusters),
        'coordination_score': coordination_score,
        'clusters': clusters
    }
```

---

## Workflow

### Step 1: Ring Detection Initiation

**Trigger:** Cross-product fraud alert, law enforcement tip, or periodic scan.

```python
from banking.fraud.multi_product_ring_detector import MultiProductFraudRingDetector

# Initialize detector
detector = MultiProductFraudRingDetector(
    client=janusgraph_client,
    min_ring_size=5,
    time_window_days=365
)

# Run detection
print("🔍 Scanning for multi-product fraud rings...")
rings = detector.detect_rings()

print(f"\n📊 Detection Results:")
print(f"   Rings detected: {len(rings)}")
for i, ring in enumerate(rings[:5], 1):
    print(f"\n   Ring #{i}:")
    print(f"      Coordinator: {ring['coordinator_id'][:16]}...")
    print(f"      Size: {ring['size']} entities")
    print(f"      Products: {ring['product_types']}")
    print(f"      Exposure: ${ring['total_exposure']:,.2f}")
    print(f"      Risk Level: {ring['risk_level'].upper()}")
    print(f"      Patterns: {ring['detected_patterns']}")
```

### Step 2: Deep Ring Analysis

**Objective:** Understand ring structure and validate detection.

```python
# Analyze specific ring
ring_id = rings[0]['coordinator_id']

print(f"🔬 Deep Analysis of Ring {ring_id[:16]}...")
print("=" * 70)

# Get ring topology
topology = detector.get_ring_topology(ring_id)

print(f"\n📊 Ring Topology:")
print(f"   Nodes: {topology['node_count']}")
print(f"   Edges: {topology['edge_count']}")
print(f"   Avg Path Length: {topology['avg_path_length']:.2f}")
print(f"   Clustering Coefficient: {topology['clustering_coefficient']:.2f}")

# Product distribution
print(f"\n📈 Product Distribution:")
for product, count in topology['product_distribution'].items():
    print(f"   {product}: {count}")

# Relationship types
print(f"\n🔗 Relationship Types:")
for rel_type, count in topology['relationship_distribution'].items():
    print(f"   {rel_type}: {count}")

# Temporal analysis
temporal = detector.analyze_ring_temporal_patterns(ring_id)
print(f"\n⏰ Temporal Analysis:")
print(f"   Activity Span: {temporal['span_days']} days")
print(f"   Peak Activity: {temporal['peak_date']}")
print(f"   Coordination Score: {temporal['coordination_score']:.2f}")
```

### Step 3: Financial Exposure Analysis

```python
# Calculate total financial exposure
exposure = detector.calculate_ring_exposure(ring_id)

print(f"\n💰 Financial Exposure Analysis:")
print("=" * 70)

print(f"\n   Credit Exposure:")
for card_type, amount in exposure['credit_cards'].items():
    print(f"      {card_type}: ${amount:,.2f}")

print(f"\n   Loan Exposure:")
for loan_type, amount in exposure['loans'].items():
    print(f"      {loan_type}: ${amount:,.2f}")

print(f"\n   Mortgage Exposure: ${exposure['mortgages']:,.2f}")

print(f"\n   TOTAL EXPOSURE: ${exposure['total']:,.2f}")

# Transaction patterns
print(f"\n📤 Transaction Patterns (Last 90 days):")
print(f"   Total Outflow: ${exposure['outflow_90d']:,.2f}")
print(f"   Total Inflow: ${exposure['inflow_90d']:,.2f}")
print(f"   Net Flow: ${exposure['net_flow_90d']:,.2f}")
print(f"   Cash-Out Ratio: {exposure['cashout_ratio']:.1%}")
```

### Step 4: Identity Verification

```python
# Verify identities in ring
identities = detector.verify_ring_identities(ring_id)

print(f"\n🪪 Identity Verification:")
print("=" * 70)

verified_count = 0
synthetic_count = 0
unknown_count = 0

for identity in identities:
    status = identity['verification_status']
    
    if status == 'verified':
        verified_count += 1
    elif status == 'synthetic':
        synthetic_count += 1
        print(f"\n   ⚠️  SYNTHETIC: {identity['person_id'][:16]}...")
        print(f"      Reason: {identity['synthetic_indicators']}")
    else:
        unknown_count += 1

print(f"\n   Verified Identities: {verified_count}")
print(f"   Synthetic Identities: {synthetic_count}")
print(f"   Unknown/Unclear: {unknown_count}")
```

### Step 5: Evidence Package Generation

```python
# Generate evidence package for law enforcement
evidence = detector.generate_evidence_package(
    ring_id=ring_id,
    include_graph_export=True,
    include_transaction_history=True,
    include_identity_analysis=True
)

print(f"\n📦 Evidence Package Generated:")
print(f"   Package ID: {evidence['package_id']}")
print(f"   Files: {len(evidence['files'])}")
print(f"   Total Size: {evidence['total_size_mb']:.2f} MB")

for file_info in evidence['files']:
    print(f"      {file_info['name']}: {file_info['size_kb']:.1f} KB")
```

### Step 6: Law Enforcement Coordination

```python
# Prepare SAR filing
sar = detector.prepare_sar_filing(
    ring_id=ring_id,
    jurisdiction='federal',
    include_law_enforcement_referral=True
)

print(f"\n📋 SAR Filing Prepared:")
print(f"   SAR Reference: {sar['sar_reference']}")
print(f"   Filing Deadline: {sar['filing_deadline']}")
print(f"   Law Enforcement Notification: {sar['le_notification_required']}")

# Decision: Immediate freeze or continued monitoring
if exposure['total'] > 1_000_000 or synthetic_count > 3:
    action = "IMMEDIATE_ACCOUNT_FREEZE"
    print(f"\n🚨 RECOMMENDED ACTION: {action}")
    print(f"   Reason: High exposure (${exposure['total']:,.2f}) and synthetic identities detected")
else:
    action = "ENHANCED_MONITORING"
    print(f"\n⚠️  RECOMMENDED ACTION: {action}")
    print(f"   Reason: Moderate risk, continue observation")
```

---

## Decision Matrices

### Ring Risk Score Calculation

| Factor | Weight | Scoring |
|--------|--------|---------|
| Ring Size | 15% | 5-10 members: 0.3, 11-25: 0.6, 26-50: 0.8, 50+: 1.0 |
| Product Diversity | 20% | 1 product: 0.1, 2: 0.4, 3: 0.7, 4+: 1.0 |
| Total Exposure | 25% | <$100K: 0.2, $100K-$500K: 0.5, $500K-$1M: 0.7, >$1M: 1.0 |
| Synthetic Identity Ratio | 20% | 0%: 0.0, 1-25%: 0.3, 26-50%: 0.6, 51-75%: 0.8, >75%: 1.0 |
| Temporal Coordination | 10% | <0.3: 0.1, 0.3-0.5: 0.4, 0.5-0.7: 0.7, >0.7: 1.0 |
| Known Patterns | 10% | Bust-out: 0.4, Synthetic: 0.3, Layering: 0.2, Multiple: 1.0 |

### Action Matrix

| Risk Level | Exposure | Synthetic % | Recommended Action |
|------------|----------|-------------|-------------------|
| Critical | >$1M | >50% | Immediate freeze + LE referral + SAR |
| Critical | >$1M | <50% | Immediate freeze + SAR |
| Critical | $500K-$1M | >75% | Immediate freeze + LE referral |
| High | $500K-$1M | 25-75% | Freeze + Enhanced monitoring |
| High | $100K-$500K | >50% | Enhanced monitoring + Account review |
| Medium | $100K-$500K | <25% | Enhanced monitoring |
| Medium | <$100K | >50% | Account review + Identity verification |
| Low | <$100K | <25% | Standard monitoring |

---

## Regulatory Compliance

### SAR Filing Requirements

**Filing Deadline:** 30 days from detection

**Required Information:**
1. All ring member identities
2. Total exposure amounts
3. Transaction patterns
4. Detection methodology
5. Timeline of fraudulent activity
6. Cross-institution coordination (if known)

### Evidence Preservation

**Retention Period:** 5 years minimum

**Required Documentation:
- Graph export with timestamps
- Transaction history (all products, 2 years)
- Identity verification results
- Communication records
- Case notes and analyst observations

---

## Performance Considerations

### Graph Size Limits

| Ring Size | Detection Time | Memory | Recommended Approach |
|-----------|----------------|--------|---------------------|
| <50 entities | <1 minute | 2GB | Standard BFS |
| 50-200 entities | 1-5 minutes | 4GB | Parallel traversal |
| 200-1000 entities | 5-30 minutes | 8GB | Graph partitioning |
| >1000 entities | 30+ minutes | 16GB+ | Distributed processing |

### Optimization Techniques

1. **Index-based filtering:** Pre-filter by risk scores before graph traversal
2. **Parallel edge traversal:** Use Gremlin `union()` for concurrent edge queries
3. **Caching:** Cache centrality calculations for frequently queried nodes
4. **Incremental updates:** Update ring membership incrementally rather than full re-scan

---

## Troubleshooting

### Issue: False Positive High-Coordination Scores

**Cause:** Legitimate business networks (family businesses, joint ventures)

**Solution:**
```python
# Add business relationship filter
detector.add_legitimate_relationship_filter([
    'joint_venture',
    'family_business',
    'co_habitation'  # Shared address with explanation
])
```

### Issue: Detection Timeout on Large Rings

**Cause:** Ring size exceeds processing threshold

**Solution:**
```python
# Use distributed processing
detector.enable_distributed_mode(
    partition_count=4,
    max_entities_per_partition=500
)
```

---

## Related Skills

- [Synthetic Identity Detection](../synthetic-identity-detection/skill.md)
- [AML Structuring Investigation](../aml-structuring-investigation/skill.md)
- [Corporate UBO Discovery](../corporate-ubo-discovery-workflow/skill.md)

## Related Documentation

- [Fraud Detection Module](../../../banking/fraud/README.md)
- [Graph ML Engine](../../../banking/analytics/graph_ml.py)
- [Notebook 03: Fraud Detection](../../../banking/notebooks/03_Fraud_Detection.ipynb)

---

**Last Reviewed:** 2026-03-24  
**Next Review:** 2026-06-24  
**Owner:** Fraud Analytics Team