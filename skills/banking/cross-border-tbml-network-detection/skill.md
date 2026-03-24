# Cross-Border TBML Network Detection

**Version:** 1.0.0  
**Last Updated:** 2026-03-24  
**Complexity:** VERY HIGH  
**Estimated Time:** 4-8 hours per investigation  
**Skill Level:** Senior AML Analyst / Trade Finance Specialist

---

## Overview

Detect and investigate Trade-Based Money Laundering (TBML) networks operating across multiple jurisdictions. TBML is the most sophisticated money laundering method, using international trade transactions to move value while disguising illicit proceeds as legitimate commerce.

### Why This Is High Complexity

| Complexity Factor | Description |
|-------------------|-------------|
| **Multi-Jurisdictional** | Trade spans 3-10+ countries with different regulations |
| **Document Forgery** | Falsified invoices, bills of lading, customs declarations |
| **Value Transfer** | Over/under invoicing, phantom shipments, multiple invoicing |
| **Shell Company Networks** | 5-50+ entities across tax havens |
| **Trade Finance Instruments** | Letters of credit, documentary collections, guarantees |
| **Commodity Complexity** | Misclassification, quality manipulation, phantom goods |
| **Regulatory Fragmentation** | Different AML thresholds, reporting requirements |
| **Intelligence Integration** | Requires customs, shipping, banking, corporate registry data |

### TBML Value Transfer Methods

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TBML VALUE TRANSFER SPECTRUM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ METHOD 1: OVER/UNDER INVOICING                                          ││
│  │                                                                          ││
│  │  Legitimate Price: $100,000                                              ││
│  │  Invoiced Price: $150,000  ──► $50,000 value transferred to exporter    ││
│  │                                                                          ││
│  │  OR                                                                       ││
│  │                                                                          ││
│  │  Legitimate Price: $100,000                                              ││
│  │  Invoiced Price: $50,000  ──► $50,000 value retained by importer        ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ METHOD 2: PHANTOM SHIPMENTS                                              ││
│  │                                                                          ││
│  │  Invoice: $500,000 for "electronics"                                     ││
│  │  Shipment: EMPTY CONTAINER or non-existent goods                         ││
│  │  Result: $500,000 moved with no underlying trade                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ METHOD 3: MULTIPLE INVOICING                                             ││
│  │                                                                          ││
│  │  Same shipment invoiced 3 times:                                         ││
│  │  - Invoice 1: $100,000 (Bank A)                                          ││
│  │  - Invoice 2: $100,000 (Bank B)                                          ││
│  │  - Invoice 3: $100,000 (Bank C)                                          ││
│  │  Total Payment: $300,000 for $100,000 goods                              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ METHOD 4: QUALITY/QUANTITY MANIPULATION                                  ││
│  │                                                                          ││
│  │  Declared: 1000 units @ $100 = $100,000                                  ││
│  │  Actual: 500 units @ $100 = $50,000                                      ││
│  │  Overpayment: $50,000 moved                                              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ METHOD 5: COMMODITY MISCLASSIFICATION                                    ││
│  │                                                                          ││
│  │  Declared: "Industrial equipment" @ $10,000/unit                         ││
│  │  Actual: Luxury watches @ $50,000/unit                                   ││
│  │  Tariff evasion + value transfer combined                                ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Knowledge
- International trade finance (letters of credit, documentary collections)
- Customs procedures and HS code classification
- Corporate registry structures (offshore, shell companies)
- Currency exchange and correspondent banking
- FATF recommendations on TBML

### Required Tools
- JanusGraph with cross-border entity resolution
- Trade finance data integration (SWIFT, customs)
- Corporate registry APIs (offshore leak databases)
- Shipping databases (container tracking, vessel AIS)
- Invoice validation services

### Required Access
- Senior AML analyst role
- Trade finance data access
- Cross-border payment data
- Customs data (if available)
- Intelligence sharing networks (Egmont Group)

---

## Graph Schema for TBML Detection

### Vertex Types

```gremlin
// Trade entities
Company              // Importers, exporters, intermediaries
Person               // UBOs, directors, agents
TradeFinanceFacility // Letters of credit, guarantees
Shipment             // Container, vessel, route
Invoice              // Commercial invoice
CustomsDeclaration   // Import/export declarations
BankAccount          // Settlement accounts
Commodity            // Goods being traded

// Reference entities
Port                 // Loading/discharge ports
Vessel               // Shipping vessels
Country              // Jurisdiction
HSCode               // Harmonized System classification
```

### Edge Types

```gremlin
// Corporate relationships
director_of           // Person -> Company
owns_share            // Person -> Company (percentage)
subsidiary_of         // Company -> Company
registered_agent      // Company -> Company (agent)

// Trade relationships
importer_of           // Company -> Shipment
exporter_of           // Company -> Shipment
consignee_of          // Company -> Shipment
notify_party          // Company -> Shipment

// Financial relationships
settled_via           // Shipment -> BankAccount
financed_by           // Shipment -> TradeFinanceFacility
payment_from          // Company -> Company (wire transfer)

// Trade documentation
has_invoice           // Shipment -> Invoice
has_customs_decl      // Shipment -> CustomsDeclaration
declares_value        // Invoice -> amount
declares_quantity     // Invoice -> quantity

// Shipping
loaded_at             // Shipment -> Port
discharged_at         // Shipment -> Port
transported_by        // Shipment -> Vessel

// Commodity
contains              // Shipment -> Commodity
classified_as         // Commodity -> HSCode
```

---

## Detection Algorithms

### Algorithm 1: Invoice Price Deviation Analysis

```python
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

@dataclass
class InvoiceDeviation:
    """Invoice price deviation from market baseline."""
    invoice_id: str
    commodity: str
    hs_code: str
    invoice_price: float
    market_price: float
    deviation_pct: float
    deviation_type: str  # 'over', 'under', 'within_normal'
    risk_score: float
    shipment_id: str
    importer_id: str
    exporter_id: str

class TBMLDetector:
    """
    Trade-Based Money Laundering detection engine.
    
    Detects value transfer through:
    1. Invoice price manipulation
    2. Phantom shipments
    3. Shell company networks
    4. Circular trading patterns
    5. Trade finance manipulation
    """
    
    def __init__(
        self,
        client,
        price_deviation_threshold: float = 0.20,  # 20% deviation
        min_shipment_value: float = 50000,  # $50K minimum
        time_window_months: int = 24
    ):
        self.client = client
        self.price_deviation_threshold = price_deviation_threshold
        self.min_shipment_value = min_shipment_value
        self.time_window_months = time_window_months
        
    def detect_tbml_networks(self) -> List[Dict]:
        """
        Main TBML detection pipeline.
        
        Returns:
            List of detected TBML networks with risk scores.
        """
        networks = []
        
        # Phase 1: Invoice anomaly detection
        invoice_anomalies = self._detect_invoice_anomalies()
        
        # Phase 2: Shell company network detection
        shell_networks = self._detect_shell_company_networks()
        
        # Phase 3: Phantom shipment detection
        phantom_shipments = self._detect_phantom_shipments()
        
        # Phase 4: Circular trading detection
        circular_patterns = self._detect_circular_trading()
        
        # Phase 5: Correlate and score
        correlated_networks = self._correlate_detections(
            invoice_anomalies,
            shell_networks,
            phantom_shipments,
            circular_patterns
        )
        
        return sorted(correlated_networks, key=lambda n: n['risk_score'], reverse=True)
    
    def _detect_invoice_anomalies(self) -> List[InvoiceDeviation]:
        """
        Detect invoices with significant price deviations.
        
        Compares:
        - Invoice price vs market price (by HS code)
        - Invoice price vs similar transactions
        - Invoice price vs customs declarations
        """
        deviations = []
        
        # Get all invoices in time window
        invoices_query = f"""
            g.V().hasLabel('invoice').
            has('date', gte('{self._get_start_date()}')).
            has('amount', gte({self.min_shipment_value})).
            project('invoice_id', 'amount', 'hs_code', 'quantity', 'unit', 
                    'shipment_id', 'importer_id', 'exporter_id').
            by('invoiceId').
            by('amount').
            by('hsCode').
            by('quantity').
            by('unit').
            by(out('invoices_shipment').id()).
            by(in('importer_of').id()).
            by(out('exporter_of').id()).
            toList()
        """
        
        invoices = self.client.execute(invoices_query)
        
        for invoice in invoices:
            # Get market price baseline for HS code
            market_price = self._get_market_price(
                invoice['hs_code'],
                invoice['date'] if 'date' in invoice else None
            )
            
            if market_price:
                unit_price = invoice['amount'] / invoice['quantity']
                deviation_pct = (unit_price - market_price) / market_price
                
                deviation_type = 'within_normal'
                if abs(deviation_pct) > self.price_deviation_threshold:
                    deviation_type = 'over' if deviation_pct > 0 else 'under'
                
                risk_score = min(abs(deviation_pct) * 2, 1.0)  # Scale to 0-1
                
                deviations.append(InvoiceDeviation(
                    invoice_id=invoice['invoice_id'],
                    commodity=self._hs_code_to_commodity(invoice['hs_code']),
                    hs_code=invoice['hs_code'],
                    invoice_price=unit_price,
                    market_price=market_price,
                    deviation_pct=deviation_pct,
                    deviation_type=deviation_type,
                    risk_score=risk_score,
                    shipment_id=invoice['shipment_id'],
                    importer_id=invoice['importer_id'],
                    exporter_id=invoice['exporter_id']
                ))
        
        return deviations
    
    def _get_market_price(self, hs_code: str, date: Optional[str] = None) -> Optional[float]:
        """
        Get market reference price for commodity.
        
        Sources:
        - Commodity exchange prices
        - Trade statistics databases
        - Historical transaction averages
        """
        # This would integrate with external pricing APIs
        # Placeholder implementation
        market_prices = {
            '8471.30': 800.0,   # Portable computers
            '8517.12': 150.0,   # Smartphones
            '2709.00': 75.0,    # Crude oil (per barrel)
            '7108.13': 58000.0, # Gold (per kg)
            '3004.90': 25.0,    # Pharmaceuticals
        }
        
        # Match HS code prefix
        for code_prefix, price in market_prices.items():
            if hs_code.startswith(code_prefix[:4]):
                return price
        
        return None
    
    def _detect_shell_company_networks(self) -> List[Dict]:
        """
        Detect networks of shell companies used in TBML.
        
        Indicators:
        - Registered in tax havens
        - No physical operations
        - Nominee directors
        - Similar names/addresses
        - Minimal capital
        - Recent incorporation
        """
        networks = []
        
        # Find companies with shell indicators
        shell_query = """
            g.V().hasLabel('company').
            has('jurisdiction', within('VG', 'KY', 'SC', 'BVI', 'PA', 'MU', 'CY')).
            or(
                has('employeeCount', lt(5)),
                has('annualRevenue', lt(100000)),
                has('registeredAgent', eq(true))
            ).
            project('company_id', 'name', 'jurisdiction', 'incorporation_date',
                    'directors', 'shareholders', 'related_companies').
            by('companyId').
            by('name').
            by('jurisdiction').
            by('incorporationDate').
            by(in('director_of').values('personId').fold()).
            by(in('owns_share').values('personId').fold()).
            by(both('subsidiary_of', 'parent_of').values('companyId').fold()).
            toList()
        """
        
        potential_shells = self.client.execute(shell_query)
        
        # Group by shared directors/shareholders
        director_groups = defaultdict(list)
        for company in potential_shells:
            for director in company['directors']:
                director_groups[director].append(company['company_id'])
        
        # Networks with shared directors (common control)
        for director, companies in director_groups.items():
            if len(companies) >= 3:  # At least 3 companies
                networks.append({
                    'network_type': 'shared_director',
                    'controller_id': director,
                    'companies': companies,
                    'company_count': len(companies),
                    'risk_score': min(len(companies) / 10, 1.0)
                })
        
        return networks
    
    def _detect_phantom_shipments(self) -> List[Dict]:
        """
        Detect shipments that may not exist (phantom shipments).
        
        Indicators:
        - No container tracking data
        - No vessel AIS data for route
        - No customs clearance
        - Invoice but no bill of lading
        - Weight/volume inconsistencies
        - Impossibly fast transit times
        """
        phantom_indicators = []
        
        # Find shipments without tracking data
        no_tracking_query = """
            g.V().hasLabel('shipment').
            has('status', eq('completed')).
            where(
                __.not(out('has_container_tracking'))
            ).
            project('shipment_id', 'value', 'route', 'declared_weight',
                    'importer', 'exporter').
            by('shipmentId').
            by('declaredValue').
            by('route').
            by('declaredWeight').
            by(in('importer_of').id()).
            by(out('exporter_of').id()).
            toList()
        """
        
        shipments_no_tracking = self.client.execute(no_tracking_query)
        
        for shipment in shipments_no_tracking:
            phantom_indicators.append({
                'shipment_id': shipment['shipment_id'],
                'indicator': 'no_container_tracking',
                'value': shipment['value'],
                'risk_score': 0.7
            })
        
        # Find shipment route inconsistencies
        route_query = """
            g.V().hasLabel('shipment').
            where(
                __.out('loaded_at').as('load_port').
                out('discharged_at').as('discharge_port').
                select('load_port', 'discharge_port').
                where('load_port', eq('discharge_port'))  // Same port = red flag
            ).
            values('shipmentId').
            toList()
        """
        
        same_port_shipments = self.client.execute(route_query)
        for shipment_id in same_port_shipments:
            phantom_indicators.append({
                'shipment_id': shipment_id,
                'indicator': 'same_load_discharge_port',
                'risk_score': 0.8
            })
        
        # Find transit time anomalies
        transit_query = """
            g.V().hasLabel('shipment').
            has('loading_date', neq(null)).
            has('discharge_date', neq(null)).
            project('shipment_id', 'load_date', 'discharge_date', 'route').
            by('shipmentId').
            by('loadingDate').
            by('dischargeDate').
            by('route').
            toList()
        """
        
        transit_shipments = self.client.execute(transit_query)
        for shipment in transit_shipments:
            if shipment['load_date'] and shipment['discharge_date']:
                load = datetime.fromisoformat(shipment['load_date'])
                discharge = datetime.fromisoformat(shipment['discharge_date'])
                transit_days = (discharge - load).days
                
                expected_days = self._get_expected_transit(shipment['route'])
                
                if transit_days < expected_days * 0.5:  # Too fast
                    phantom_indicators.append({
                        'shipment_id': shipment['shipment_id'],
                        'indicator': 'impossibly_fast_transit',
                        'actual_days': transit_days,
                        'expected_days': expected_days,
                        'risk_score': 0.9
                    })
        
        return phantom_indicators
    
    def _detect_circular_trading(self) -> List[Dict]:
        """
        Detect circular trading patterns where goods move in circles.
        
        Pattern: A -> B -> C -> A
        Same goods, multiple payments, no real trade purpose.
        
        Also detects:
        - Back-to-back trades
        - Mirror trades
        - Round-trip invoicing
        """
        circular_patterns = []
        
        # Find circular paths in trade
        circular_query = """
            g.V().hasLabel('company').as('start').
            repeat(
                out('exporter_of').in('importer_of').simplePath()
            ).times(3).
            where(eq('start')).
            path().
            by('companyId').
            dedup().
            toList()
        """
        
        circular_paths = self.client.execute(circular_query)
        
        for path in circular_paths:
            # Calculate total value moved
            total_value = 0
            for i in range(len(path) - 1):
                # Get shipments between consecutive companies
                value_query = f"""
                    g.V().has('companyId', '{path[i]}').
                    out('exporter_of').
                    where(in('importer_of').has('companyId', '{path[i+1]}')).
                    values('declaredValue').
                    sum()
                """
                value = self.client.execute(value_query)
                total_value += value[0] if value else 0
            
            circular_patterns.append({
                'pattern_type': 'circular_trade',
                'path': path,
                'path_length': len(path),
                'total_value': total_value,
                'risk_score': 0.85
            })
        
        return circular_patterns
    
    def _correlate_detections(
        self,
        invoice_anomalies: List[InvoiceDeviation],
        shell_networks: List[Dict],
        phantom_shipments: List[Dict],
        circular_patterns: List[Dict]
    ) -> List[Dict]:
        """
        Correlate individual detections into TBML networks.
        
        A comprehensive TBML network combines:
        1. Invoice manipulation
        2. Shell company structure
        3. Phantom or circular shipments
        4. Multiple jurisdictions
        """
        networks = []
        
        # Group entities across detections
        entity_detections = defaultdict(list)
        
        for inv in invoice_anomalies:
            entity_detections[inv.importer_id].append(('invoice_anomaly', inv))
            entity_detections[inv.exporter_id].append(('invoice_anomaly', inv))
        
        for shell in shell_networks:
            for company_id in shell['companies']:
                entity_detections[company_id].append(('shell_network', shell))
        
        for phantom in phantom_shipments:
            entity_detections[phantom['shipment_id']].append(('phantom', phantom))
        
        for circular in circular_patterns:
            for company_id in circular['path']:
                entity_detections[company_id].append(('circular', circular))
        
        # Score entities by detection count and severity
        for entity_id, detections in entity_detections.items():
            if len(detections) >= 2:  # Multiple detection types
                risk_score = sum(d[1].get('risk_score', 0.5) for d in detections) / len(detections)
                
                networks.append({
                    'network_id': entity_id,
                    'detection_types': list(set(d[0] for d in detections)),
                    'detection_count': len(detections),
                    'risk_score': risk_score,
                    'details': detections
                })
        
        return networks
```

### Algorithm 2: Trade Finance Manipulation Detection

```python
def detect_trade_finance_manipulation(self) -> List[Dict]:
    """
    Detect manipulation of trade finance instruments.
    
    Patterns:
    - Duplicate financing (same invoice financed by multiple banks)
    - Over-drawing (drawing more than shipment value)
    - Falsified documents (forged bills of lading, certificates)
    - LC manipulation (amendments to increase value)
    """
    manipulations = []
    
    # Find duplicate financing
    duplicate_query = """
        g.V().hasLabel('invoice').as('inv').
        in('finances').as('lc1').
        match(
            __.as('inv').in('finances').as('lc2')
        ).
        where('lc1', neq('lc2')).
        select('inv', 'lc1', 'lc2').
        by('invoiceId').
        by('lcId').
        by('lcId').
        toList()
    """
    
    duplicates = self.client.execute(duplicate_query)
    
    for dup in duplicates:
        manipulations.append({
            'type': 'duplicate_financing',
            'invoice_id': dup['inv'],
            'lc_ids': [dup['lc1'], dup['lc2']],
            'risk_score': 0.95
        })
    
    return manipulations
```

### Algorithm 3: Jurisdiction Risk Correlation

```python
def analyze_jurisdiction_risk(self, trade_flow: Dict) -> Dict:
    """
    Analyze jurisdiction-based risk for trade flows.
    
    Risk factors:
    - FATF grey/black list
    - Transparency International CPI score
    - Trade-based risk indicators by country
    - Correspondent banking relationships
    """
    # Jurisdiction risk matrix
    jurisdiction_risk = {
        'IRN': 0.95,  # Iran - OFAC sanctions
        'PRK': 0.95,  # North Korea
        'MMR': 0.85,  # Myanmar
        'VEN': 0.80,  # Venezuela
        'RUS': 0.75,  # Russia
        'ARE': 0.60,  # UAE (transit hub)
        'HKG': 0.55,  # Hong Kong (transit hub)
        'SGP': 0.50,  # Singapore (transit hub)
        'VGB': 0.85,  # British Virgin Islands (secrecy)
        'CYM': 0.80,  # Cayman Islands
        'PAN': 0.75,  # Panama
    }
    
    import_jurisdiction = trade_flow['importer_jurisdiction']
    export_jurisdiction = trade_flow['exporter_jurisdiction']
    
    import_risk = jurisdiction_risk.get(import_jurisdiction, 0.2)
    export_risk = jurisdiction_risk.get(export_jurisdiction, 0.2)
    
    # High-risk corridor
    corridor_risk = max(import_risk, export_risk)
    if import_risk > 0.5 and export_risk > 0.5:
        corridor_risk *= 1.2  # Both high risk
    
    return {
        'import_jurisdiction': import_jurisdiction,
        'export_jurisdiction': export_jurisdiction,
        'import_risk': import_risk,
        'export_risk': export_risk,
        'corridor_risk': min(corridor_risk, 1.0),
        'is_sanctioned_corridor': import_risk > 0.8 or export_risk > 0.8
    }
```

---

## Workflow

### Step 1: TBML Network Detection

```python
from banking.aml.tbml_detector import TBMLDetector

# Initialize detector
detector = TBMLDetector(
    client=janusgraph_client,
    price_deviation_threshold=0.25,  # 25% deviation
    min_shipment_value=100000,        # $100K minimum
    time_window_months=24
)

# Run full detection
print("🔍 Scanning for TBML networks...")
networks = detector.detect_tbml_networks()

print(f"\n📊 Detection Results:")
print(f"   Networks detected: {len(networks)}")
for i, network in enumerate(networks[:5], 1):
    print(f"\n   Network #{i}:")
    print(f"      Primary Entity: {network['network_id'][:16]}...")
    print(f"      Detection Types: {network['detection_types']}")
    print(f"      Risk Score: {network['risk_score']:.2f}")
```

### Step 2: Invoice Anomaly Analysis

```python
# Deep dive on invoice anomalies
print("\n📋 Invoice Anomaly Analysis:")
print("=" * 70)

anomalies = detector._detect_invoice_anomalies()

over_invoiced = [a for a in anomalies if a.deviation_type == 'over']
under_invoiced = [a for a in anomalies if a.deviation_type == 'under']

print(f"\n   Over-invoiced: {len(over_invoiced)}")
print(f"   Under-invoiced: {len(under_invoiced)}")

print("\n   Top 10 Over-invoiced Transactions:")
for inv in sorted(over_invoiced, key=lambda x: x.deviation_pct, reverse=True)[:10]:
    print(f"      {inv.invoice_id[:16]}... | {inv.commodity[:20]:20s} | "
          f"+{inv.deviation_pct*100:.1f}% | ${inv.invoice_price:,.2f} vs ${inv.market_price:,.2f}")

print("\n   Top 10 Under-invoiced Transactions:")
for inv in sorted(under_invoiced, key=lambda x: x.deviation_pct)[:10]:
    print(f"      {inv.invoice_id[:16]}... | {inv.commodity[:20]:20s} | "
          f"{inv.deviation_pct*100:.1f}% | ${inv.invoice_price:,.2f} vs ${inv.market_price:,.2f}")
```

### Step 3: Shell Company Network Mapping

```python
# Analyze shell company structures
print("\n🏢 Shell Company Network Analysis:")
print("=" * 70)

shell_networks = detector._detect_shell_company_networks()

for i, network in enumerate(shell_networks[:5], 1):
    print(f"\n   Network #{i} (Controller: {network['controller_id'][:16]}...):")
    
    for company_id in network['companies'][:10]:
        # Get company details
        details = detector.get_company_details(company_id)
        print(f"      {details['name'][:30]:30s} | {details['jurisdiction']} | "
              f"Inc: {details['incorporation_date']}")
    
    if len(network['companies']) > 10:
        print(f"      ... and {len(network['companies']) - 10} more companies")
```

### Step 4: Phantom Shipment Detection

```python
# Detect phantom shipments
print("\n🚢 Phantom Shipment Analysis:")
print("=" * 70)

phantoms = detector._detect_phantom_shipments()

no_tracking = [p for p in phantoms if p['indicator'] == 'no_container_tracking']
fast_transit = [p for p in phantoms if p['indicator'] == 'impossibly_fast_transit']
same_port = [p for p in phantoms if p['indicator'] == 'same_load_discharge_port']

print(f"\n   No Container Tracking: {len(no_tracking)}")
print(f"   Impossibly Fast Transit: {len(fast_transit)}")
print(f"   Same Load/Discharge Port: {len(same_port)}")

# Calculate potential value at risk
total_phantom_value = sum(p.get('value', 0) for p in phantoms)
print(f"\n   Total Value at Risk: ${total_phantom_value:,.2f}")
```

### Step 5: Circular Trading Detection

```python
# Detect circular trading patterns
print("\n🔄 Circular Trading Detection:")
print("=" * 70)

circular = detector._detect_circular_trading()

for i, pattern in enumerate(circular[:5], 1):
    print(f"\n   Circular Path #{i}:")
    print(f"      Path: {' -> '.join([c[:8] + '...' for c in pattern['path']])}")
    print(f"      Total Value: ${pattern['total_value']:,.2f}")
    print(f"      Risk Score: {pattern['risk_score']:.2f}")
```

### Step 6: Jurisdiction Risk Analysis

```python
# Analyze jurisdiction risks
print("\n🌍 Jurisdiction Risk Analysis:")
print("=" * 70)

for network in networks[:3]:
    trade_flows = detector.get_trade_flows(network['network_id'])
    
    print(f"\n   Entity: {network['network_id'][:16]}...")
    
    for flow in trade_flows[:5]:
        jr = detector.analyze_jurisdiction_risk(flow)
        
        print(f"\n      Trade Flow: {jr['export_jurisdiction']} -> {jr['import_jurisdiction']}")
        print(f"      Export Risk: {jr['export_risk']:.2f}")
        print(f"      Import Risk: {jr['import_risk']:.2f}")
        print(f"      Corridor Risk: {jr['corridor_risk']:.2f}")
        
        if jr['is_sanctioned_corridor']:
            print(f"      ⚠️ SANCTIONED CORRIDOR")
```

### Step 7: Evidence Compilation

```python
# Compile evidence for regulatory filing
print("\n📦 Evidence Compilation:")
print("=" * 70)

evidence = detector.compile_evidence_package(
    network_id=networks[0]['network_id'],
    include_invoices=True,
    include_shipment_data=True,
    include_corporate_structure=True,
    include_jurisdiction_analysis=True
)

print(f"\n   Package ID: {evidence['package_id']}")
print(f"   Total Files: {len(evidence['files'])}")

for file_info in evidence['files']:
    print(f"      {file_info['name']}: {file_info['size_kb']:.1f} KB")
```

### Step 8: SAR Filing Preparation

```python
# Prepare SAR filing
print("\n📋 SAR Filing Preparation:")
print("=" * 70)

sar = detector.prepare_sar_filing(
    network_id=networks[0]['network_id'],
    sar_type='TBML',
    include_intelligence_sharing=True
)

print(f"\n   SAR Reference: {sar['sar_reference']}")
print(f"   Filing Type: {sar['sar_type']}")
print(f"   Filing Deadline: {sar['filing_deadline']}")
print(f"   Narratives Required: {len(sar['narratives'])}")

for i, narrative in enumerate(sar['narratives'], 1):
    print(f"\n   Narrative #{i}: {narrative['type']}")
    print(f"      {narrative['summary'][:100]}...")
```

---

## Decision Matrices

### TBML Risk Score Calculation

| Factor | Weight | Scoring |
|--------|--------|---------|
| Invoice Deviation | 20% | <10%: 0.1, 10-20%: 0.3, 20-50%: 0.6, >50%: 1.0 |
| Shell Company Indicators | 20% | 0 indicators: 0.0, 1-2: 0.3, 3-4: 0.6, 5+: 1.0 |
| Phantom Shipment Evidence | 15% | 0: 0.0, 1: 0.5, 2+: 1.0 |
| Circular Trading Detected | 15% | None: 0.0, 1 path: 0.6, 2+ paths: 1.0 |
| Jurisdiction Risk | 15% | Low (<0.3): 0.1, Medium (0.3-0.6): 0.4, High (>0.6): 0.8 |
| Trade Finance Manipulation | 15% | None: 0.0, Suspected: 0.6, Confirmed: 1.0 |

### Action Matrix

| Risk Score | Sanctioned Corridor | Value | Recommended Action |
|------------|---------------------|-------|-------------------|
| ≥0.85 | Yes | Any | Immediate block + OFAC referral + SAR |
| ≥0.85 | No | >$1M | Enhanced due diligence + SAR |
| 0.70-0.84 | Yes | Any | Block + Investigation + SAR |
| 0.70-0.84 | No | >$500K | Investigation + SAR |
| 0.50-0.69 | Any | >$100K | Enhanced monitoring + Review |
| <0.50 | No | Any | Standard monitoring |

---

## Regulatory Compliance

### SAR Filing Requirements (TBML)

**Filing Deadline:** 30 days from detection

**Required Elements:**
1. Trade flow description (commodity, route, value)
2. Invoice manipulation details
3. Shell company structure
4. Jurisdiction risk analysis
5. Phantom shipment evidence
6. Estimated value transferred

### Intelligence Sharing

**Egmont Group Submission:**
- Cross-border TBML networks
- Multi-jurisdiction involvement
- Estimated value >$1M

**FINCEN Form 8300:**
- Cash transactions >$10K related to TBML
**CBP Notification:**
- Customs fraud indicators
- Misclassification evidence

---

## Performance Optimization

### Large-Scale Processing

| Trade Volume | Processing Time | Approach |
|--------------|-----------------|----------|
| <1,000 shipments/month | <5 minutes | Standard queries |
| 1,000-10,000 shipments/month | 5-30 minutes | Parallel processing |
| 10,000-100,000 shipments/month | 30-120 minutes | Partitioned processing |
| >100,000 shipments/month | 2+ hours | Distributed + sampling |

### Caching Strategy

```python
# Cache market prices
detector.enable_price_cache(
    ttl_hours=24,
    max_entries=10000
)

# Cache jurisdiction risk
detector.cache_jurisdiction_risk()

# Pre-compute shell indicators
detector.precompute_shell_indicators()
```

---

## Related Skills

- [Multi-Product Fraud Ring Detection](../multi-product-fraud-ring-detection/skill.md)
- [Corporate UBO Discovery](../corporate-ubo-discovery-workflow/skill.md)
- [Sanctions Screening](../sanctions-screening-workflow/skill.md)

## Related Documentation

- [AML Module](../../../banking/aml/README.md)
- [Trade Finance Detection](../../../banking/aml/trade_finance_detection.py)
- [Notebook 06: TBML Detection](../../../banking/notebooks/06_TBML_Detection.ipynb)

---

**Last Reviewed:** 2026-03-24  
**Next Review:** 2026-06-24  
**Owner:** AML Compliance Team