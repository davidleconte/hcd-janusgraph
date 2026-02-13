# Gremlin OLAP & Advanced Scenarios Guide

**Date:** 2026-01-28
**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS
**Purpose:** OLAP operations using Gremlin graph traversals + Ultra-complex realistic scenarios

---

## Table of Contents

1. [OLAP with Gremlin](#olap-with-gremlin)
2. [Why Gremlin for OLAP?](#why-gremlin-for-olap)
3. [Gremlin OLAP Operations](#gremlin-olap-operations)
4. [Ultra-Complex Scenarios](#ultra-complex-scenarios)
5. [Hybrid Approach: OpenSearch + Gremlin](#hybrid-approach)

---

## OLAP with Gremlin

### Why Gremlin for OLAP?

**Traditional OLAP** (OpenSearch/SQL):

- ✅ Fast aggregations
- ✅ Time-series analysis
- ✅ Statistical operations
- ❌ Limited relationship analysis
- ❌ No path traversal

**Graph OLAP** (Gremlin):

- ✅ Relationship-based aggregations
- ✅ Multi-hop path analysis
- ✅ Network metrics (centrality, clustering)
- ✅ Pattern detection across relationships
- ❌ Slower for simple aggregations

**Best Practice:** Use both!

- OpenSearch for transaction-level OLAP
- Gremlin for relationship-based OLAP

---

## Gremlin OLAP Operations

### 1. SLICE with Gremlin

**Definition:** Filter graph by one dimension (vertex/edge property)

**Business Example:** "All transactions in Q1 2024"

```groovy
// Gremlin SLICE: Q1 2024 transactions
g.V().hasLabel('Transaction').
  has('timestamp', between(
    datetime('2024-01-01T00:00:00Z'),
    datetime('2024-04-01T00:00:00Z')
  )).
  group().
    by('transaction_type').
    by(fold().
      project('count', 'total_amount', 'avg_amount').
        by(count()).
        by(values('amount').sum()).
        by(values('amount').mean())
    )
```

**Result:**

```json
{
  "DEPOSIT": {
    "count": 450,
    "total_amount": 567890.12,
    "avg_amount": 1261.98
  },
  "WITHDRAWAL": {
    "count": 350,
    "total_amount": 345678.90,
    "avg_amount": 987.37
  },
  "TRANSFER": {
    "count": 355,
    "total_amount": 320998.87,
    "avg_amount": 904.22
  }
}
```

### 2. DICE with Gremlin

**Definition:** Multi-dimensional filtering

**Business Example:** "High-value international wires from suspicious accounts"

```groovy
// Gremlin DICE: Multiple filters
g.V().hasLabel('Transaction').
  has('transaction_type', 'WIRE_TRANSFER').
  has('amount', gte(10000)).
  has('currency', within('USD', 'EUR', 'GBP')).
  where(
    out('from_account').
    has('risk_score', gte(70))
  ).
  group().
    by(out('from_account').values('account_id')).
    by(fold().
      project('txn_count', 'total_volume', 'unique_counterparties', 'avg_amount').
        by(count()).
        by(values('amount').sum()).
        by(out('to_account').dedup().count()).
        by(values('amount').mean())
    ).
  order(local).
    by(select(values).select('total_volume'), desc).
  limit(local, 10)
```

**Result:**

```json
{
  "ACC_001": {
    "txn_count": 12,
    "total_volume": 234567.89,
    "unique_counterparties": 8,
    "avg_amount": 19547.32
  },
  "ACC_002": {
    "txn_count": 8,
    "total_volume": 189234.56,
    "unique_counterparties": 5,
    "avg_amount": 23654.32
  }
}
```

### 3. DRILL-DOWN with Gremlin

**Definition:** Navigate from summary to detail through graph hierarchy

**Business Example:** "Account → Transaction Type → Counterparty → Individual Transactions"

```groovy
// Gremlin DRILL-DOWN: Multi-level hierarchy
g.V().hasLabel('Account').
  has('account_id', 'ACC_001').
  project('account', 'by_type', 'by_counterparty', 'transactions').
    // Level 1: Account summary
    by(valueMap('account_id', 'balance', 'risk_score')).
    // Level 2: By transaction type
    by(
      out('has_transaction').
      group().
        by('transaction_type').
        by(fold().
          project('count', 'volume').
            by(count()).
            by(values('amount').sum())
        )
    ).
    // Level 3: By counterparty
    by(
      out('has_transaction').
      out('to_account').
      group().
        by('account_id').
        by(
          in('to_account').
          fold().
          project('txn_count', 'total_sent', 'avg_amount').
            by(count()).
            by(values('amount').sum()).
            by(values('amount').mean())
        ).
      order(local).
        by(select(values).select('total_sent'), desc).
      limit(local, 5)
    ).
    // Level 4: Individual transactions
    by(
      out('has_transaction').
      order().by('timestamp', desc).
      limit(10).
      valueMap('transaction_id', 'amount', 'timestamp', 'transaction_type')
    )
```

**Result:**

```json
{
  "account": {
    "account_id": "ACC_001",
    "balance": 125000.00,
    "risk_score": 45
  },
  "by_type": {
    "WIRE_TRANSFER": {"count": 12, "volume": 234567.89},
    "DEPOSIT": {"count": 25, "volume": 156789.01},
    "WITHDRAWAL": {"count": 8, "volume": 89012.34}
  },
  "by_counterparty": {
    "ACC_105": {"txn_count": 5, "total_sent": 89234.56, "avg_amount": 17846.91},
    "ACC_203": {"txn_count": 3, "total_sent": 67890.12, "avg_amount": 22630.04}
  },
  "transactions": [
    {"transaction_id": "TXN_1234", "amount": 25000.00, "timestamp": "2024-01-15T10:30:00Z"}
  ]
}
```

### 4. ROLL-UP with Gremlin

**Definition:** Aggregate from detail to summary

**Business Example:** "Transaction → Account → Customer → Region"

```groovy
// Gremlin ROLL-UP: Bottom-up aggregation
g.V().hasLabel('Transaction').
  project('transaction_level', 'account_level', 'customer_level', 'region_level').
    // Level 1: Transaction details
    by(
      group().
        by('transaction_type').
        by(fold().
          project('count', 'volume').
            by(count()).
            by(values('amount').sum())
        )
    ).
    // Level 2: Account aggregation
    by(
      out('from_account').
      group().
        by('account_type').
        by(
          in('from_account').
          fold().
          project('account_count', 'total_volume', 'avg_per_account').
            by(dedup().count()).
            by(values('amount').sum()).
            by(values('amount').mean())
        )
    ).
    // Level 3: Customer aggregation
    by(
      out('from_account').
      out('owned_by').
      group().
        by('customer_segment').
        by(
          in('owned_by').
          in('from_account').
          fold().
          project('customer_count', 'total_volume', 'avg_per_customer').
            by(out('owned_by').dedup().count()).
            by(values('amount').sum()).
            by(values('amount').mean())
        )
    ).
    // Level 4: Regional aggregation
    by(
      out('from_account').
      out('owned_by').
      group().
        by('region').
        by(
          in('owned_by').
          in('from_account').
          fold().
          project('region_volume', 'customer_count', 'account_count').
            by(values('amount').sum()).
            by(out('owned_by').dedup().count()).
            by(out('from_account').dedup().count())
        )
    )
```

### 5. PIVOT with Gremlin

**Definition:** Rotate data for different perspectives

**Business Example:** "Account Type × Transaction Type matrix"

```groovy
// Gremlin PIVOT: Cross-tabulation
g.V().hasLabel('Account').
  project('account_type', 'transaction_matrix').
    by('account_type').
    by(
      out('has_transaction').
      group().
        by('transaction_type').
        by(fold().
          project('count', 'volume', 'avg_amount').
            by(count()).
            by(values('amount').sum()).
            by(values('amount').mean())
        )
    ).
  group().
    by(select('account_type')).
    by(select('transaction_matrix'))
```

**Result:**

```json
{
  "CHECKING": {
    "DEPOSIT": {"count": 450, "volume": 567890.12, "avg_amount": 1261.98},
    "WITHDRAWAL": {"count": 350, "volume": 345678.90, "avg_amount": 987.37},
    "TRANSFER": {"count": 200, "volume": 234567.89, "avg_amount": 1172.84}
  },
  "SAVINGS": {
    "DEPOSIT": {"count": 300, "volume": 456789.01, "avg_amount": 1522.63},
    "WITHDRAWAL": {"count": 150, "volume": 189012.34, "avg_amount": 1260.08}
  },
  "BUSINESS": {
    "WIRE_TRANSFER": {"count": 120, "volume": 890123.45, "avg_amount": 7417.70},
    "DEPOSIT": {"count": 200, "volume": 678901.23, "avg_amount": 3394.51}
  }
}
```

---

## Ultra-Complex Scenarios

### Scenario 1: Trade-Based Money Laundering (TBML)

**Business Problem:** Detect sophisticated TBML schemes:

- Over/under-invoicing
- Multiple invoices for same shipment
- Circular trading patterns
- Shell company networks
- Mismatched commodity descriptions

**Gremlin Query:**

```groovy
// Detect TBML: Circular trading with price manipulation
g.V().hasLabel('Company').as('origin').
  // Find circular trade paths (3-5 hops)
  repeat(
    out('traded_with').simplePath()
  ).times(3).emit().times(5).
  where(
    out('traded_with').as('origin')
  ).as('cycle').
  // Analyze the cycle
  path().
  project('companies', 'transactions', 'price_variance', 'time_span', 'risk_indicators').
    // Extract companies in cycle
    by(
      unfold().
      hasLabel('Company').
      dedup().
      valueMap('company_name', 'country', 'incorporation_date')
    ).
    // Extract transactions
    by(
      unfold().
      hasLabel('Trade').
      order().by('trade_date').
      valueMap('trade_id', 'commodity', 'quantity', 'unit_price', 'total_value', 'trade_date')
    ).
    // Calculate price variance (manipulation indicator)
    by(
      unfold().
      hasLabel('Trade').
      values('unit_price').
      fold().
      project('min', 'max', 'mean', 'std_dev', 'variance_ratio').
        by(min(local)).
        by(max(local)).
        by(mean(local)).
        by(
          // Calculate standard deviation
          math('(max - min) / mean')
        ).
        by(
          // Variance ratio (high = manipulation)
          math('(max - min) / mean * 100')
        )
    ).
    // Time span analysis
    by(
      unfold().
      hasLabel('Trade').
      values('trade_date').
      fold().
      project('first_trade', 'last_trade', 'duration_days').
        by(min(local)).
        by(max(local)).
        by(
          // Calculate duration
          math('(max - min) / 86400000')  // milliseconds to days
        )
    ).
    // Risk indicators
    by(
      unfold().
      hasLabel('Company').
      project('shell_company_indicators', 'sanctions_exposure', 'high_risk_jurisdictions').
        by(
          coalesce(
            values('has_physical_office'),
            constant(false)
          ).
          choose(
            is(false),
            constant(1),
            constant(0)
          ).
          sum()
        ).
        by(
          out('has_relationship').
          hasLabel('SanctionedEntity').
          count()
        ).
        by(
          values('country').
          where(
            within('North Korea', 'Iran', 'Syria', 'Venezuela')
          ).
          count()
        )
    ).
  // Filter high-risk cycles
  where(
    select('price_variance').
    select('variance_ratio').
    is(gte(50))  // >50% price variance
  ).
  where(
    select('risk_indicators').
    select('shell_company_indicators').
    is(gte(2))  // At least 2 shell companies
  ).
  // Calculate overall risk score
  project('cycle_details', 'risk_score', 'recommendation').
    by(identity()).
    by(
      // Risk score calculation
      math(
        'price_var * 0.3 + ' +
        'shell_companies * 20 + ' +
        'sanctions * 30 + ' +
        'high_risk_jurisdictions * 15'
      )
    ).
    by(
      choose(
        select('risk_score').is(gte(80)),
        constant('IMMEDIATE INVESTIGATION - High TBML Risk'),
        choose(
          select('risk_score').is(gte(60)),
          constant('PRIORITY REVIEW - Moderate TBML Risk'),
          constant('MONITOR - Low TBML Risk')
        )
      )
    ).
  order().by(select('risk_score'), desc).
  limit(10)
```

**Expected Output:**

```json
{
  "cycle_details": {
    "companies": [
      {"company_name": "Global Trading LLC", "country": "Panama", "incorporation_date": "2023-01-15"},
      {"company_name": "International Exports SA", "country": "Cyprus", "incorporation_date": "2023-02-20"},
      {"company_name": "Worldwide Commodities Inc", "country": "BVI", "incorporation_date": "2023-03-10"}
    ],
    "transactions": [
      {"trade_id": "T001", "commodity": "Electronics", "quantity": 1000, "unit_price": 100, "total_value": 100000},
      {"trade_id": "T002", "commodity": "Electronics", "quantity": 1000, "unit_price": 250, "total_value": 250000},
      {"trade_id": "T003", "commodity": "Electronics", "quantity": 1000, "unit_price": 180, "total_value": 180000}
    ],
    "price_variance": {
      "min": 100,
      "max": 250,
      "mean": 176.67,
      "variance_ratio": 84.91
    },
    "time_span": {
      "first_trade": "2024-01-10",
      "last_trade": "2024-01-25",
      "duration_days": 15
    },
    "risk_indicators": {
      "shell_company_indicators": 3,
      "sanctions_exposure": 1,
      "high_risk_jurisdictions": 2
    }
  },
  "risk_score": 95.47,
  "recommendation": "IMMEDIATE INVESTIGATION - High TBML Risk"
}
```

### Scenario 2: Layered Money Laundering Network

**Business Problem:** Detect multi-layered laundering:

- Placement through multiple accounts
- Complex layering through shell companies
- Integration through legitimate businesses
- Cross-border transfers
- Cryptocurrency mixing

**Gremlin Query:**

```groovy
// Detect 5-layer money laundering network
g.V().hasLabel('Account').
  has('account_type', 'PERSONAL').
  // Layer 1: PLACEMENT - Structured deposits
  where(
    out('has_transaction').
    hasLabel('Transaction').
    has('transaction_type', 'DEPOSIT').
    has('amount', between(5000, 9999)).
    count().is(gte(5))  // At least 5 structured deposits
  ).as('placement_account').
  // Layer 2: LAYERING - Rapid transfers to shell companies
  out('has_transaction').
  has('transaction_type', 'TRANSFER').
  has('timestamp', within(datetime('now-7d'), datetime('now'))).
  out('to_account').
  where(
    out('owned_by').
    hasLabel('Company').
    has('is_shell_company', true)
  ).as('shell_account_1').
  // Layer 3: LAYERING - International wire transfers
  out('has_transaction').
  has('transaction_type', 'WIRE_TRANSFER').
  has('is_international', true).
  out('to_account').
  where(
    values('country').is(neq('USA'))
  ).as('offshore_account').
  // Layer 4: LAYERING - Cryptocurrency conversion
  out('has_transaction').
  has('transaction_type', 'CRYPTO_EXCHANGE').
  out('to_wallet').
  hasLabel('CryptoWallet').as('crypto_wallet').
  // Layer 5: INTEGRATION - Back to legitimate business
  out('has_transaction').
  has('transaction_type', 'CRYPTO_WITHDRAWAL').
  out('to_account').
  where(
    out('owned_by').
    hasLabel('Company').
    has('is_legitimate_business', true)
  ).as('integration_account').
  // Analyze the complete path
  path().
  project('network_summary', 'placement_layer', 'layering_layers', 'integration_layer', 'risk_metrics').
    // Network summary
    by(
      project('total_accounts', 'total_transactions', 'total_amount', 'duration_days').
        by(
          unfold().
          hasLabel('Account').
          dedup().
          count()
        ).
        by(
          unfold().
          hasLabel('Transaction').
          count()
        ).
        by(
          unfold().
          hasLabel('Transaction').
          values('amount').
          sum()
        ).
        by(
          unfold().
          hasLabel('Transaction').
          values('timestamp').
          fold().
          project('duration').
            by(
              math('(max - min) / 86400000')
            )
        )
    ).
    // Placement analysis
    by(
      select('placement_account').
      project('account_id', 'structured_deposits', 'total_placed').
        by(values('account_id')).
        by(
          out('has_transaction').
          has('transaction_type', 'DEPOSIT').
          has('amount', between(5000, 9999)).
          count()
        ).
        by(
          out('has_transaction').
          has('transaction_type', 'DEPOSIT').
          has('amount', between(5000, 9999)).
          values('amount').
          sum()
        )
    ).
    // Layering analysis
    by(
      project('shell_companies', 'offshore_transfers', 'crypto_mixing').
        by(
          select('shell_account_1').
          out('owned_by').
          dedup().
          valueMap('company_name', 'country', 'incorporation_date')
        ).
        by(
          select('offshore_account').
          in('to_account').
          valueMap('transaction_id', 'amount', 'country', 'timestamp')
        ).
        by(
          select('crypto_wallet').
          valueMap('wallet_address', 'blockchain', 'total_received')
        )
    ).
    // Integration analysis
    by(
      select('integration_account').
      project('account_id', 'business_name', 'final_amount').
        by(values('account_id')).
        by(
          out('owned_by').
          values('company_name')
        ).
        by(
          in('to_account').
          values('amount').
          sum()
        )
    ).
    // Risk metrics
    by(
      project('velocity_score', 'complexity_score', 'obfuscation_score', 'overall_risk').
        // Velocity: How fast money moved
        by(
          math('total_amount / duration_days')
        ).
        // Complexity: Number of hops and entities
        by(
          math('total_accounts * 10 + total_transactions * 2')
        ).
        // Obfuscation: Shell companies + crypto + offshore
        by(
          math('shell_count * 20 + crypto_count * 25 + offshore_count * 15')
        ).
        // Overall risk (0-100)
        by(
          math('min(100, (velocity_score * 0.3 + complexity_score * 0.3 + obfuscation_score * 0.4))')
        )
    ).
  // Filter high-risk networks
  where(
    select('risk_metrics').
    select('overall_risk').
    is(gte(75))
  ).
  order().by(select('risk_metrics').select('overall_risk'), desc).
  limit(5)
```

### Scenario 3: Insider Trading Network

**Business Problem:** Detect insider trading rings:

- Information flow from corporate insiders
- Coordinated trading before announcements
- Family/friend networks
- Offshore accounts
- Timing patterns

**Gremlin Query:**

```groovy
// Detect insider trading network
g.V().hasLabel('Company').
  has('has_upcoming_announcement', true).as('target_company').
  // Find corporate insiders
  in('works_for').
  hasLabel('Person').
  has('position', within('CEO', 'CFO', 'Board Member', 'Executive')).as('insider').
  // Find their social network (family, friends)
  out('related_to').
  hasLabel('Person').as('network_member').
  // Find trading accounts
  out('owns').
  hasLabel('Account').as('trading_account').
  // Find suspicious trades
  out('has_transaction').
  hasLabel('Trade').
  where(
    // Trade occurred 1-30 days before announcement
    and(
      has('trade_date', gte(datetime('announcement_date - 30d'))),
      has('trade_date', lt(datetime('announcement_date')))
    )
  ).
  where(
    // Trade was in target company stock
    has('security_id', select('target_company').values('stock_symbol'))
  ).
  where(
    // Unusual volume (>3x average)
    has('volume', gte(
      select('trading_account').
      out('has_transaction').
      values('volume').
      mean().
      math('_ * 3')
    ))
  ).as('suspicious_trade').
  // Analyze the network
  path().
  project('insider_info', 'network_analysis', 'trading_pattern', 'timing_analysis', 'risk_assessment').
    // Insider information
    by(
      select('insider').
      project('name', 'position', 'company', 'access_level').
        by(values('full_name')).
        by(values('position')).
        by(
          out('works_for').
          values('company_name')
        ).
        by(
          coalesce(
            values('has_material_nonpublic_info'),
            constant(false)
          )
        )
    ).
    // Network analysis
    by(
      project('network_size', 'relationships', 'account_connections').
        by(
          select('network_member').
          dedup().
          count()
        ).
        by(
          select('insider').
          outE('related_to').
          project('relationship_type', 'person').
            by('relationship_type').
            by(inV().values('full_name'))
        ).
        by(
          select('trading_account').
          project('account_id', 'owner', 'account_type', 'jurisdiction').
            by(values('account_id')).
            by(
              out('owned_by').
              values('full_name')
            ).
            by(values('account_type')).
            by(values('country'))
        )
    ).
    // Trading pattern
    by(
      select('suspicious_trade').
      order().by('trade_date').
      project('trade_details', 'profit_analysis').
        by(
          valueMap('trade_id', 'trade_date', 'trade_type', 'volume', 'price', 'total_value')
        ).
        by(
          project('entry_price', 'exit_price', 'profit_amount', 'profit_percentage').
            by(values('price')).
            by(
              // Price after announcement
              coalesce(
                values('exit_price'),
                constant(0)
              )
            ).
            by(
              math('(exit_price - entry_price) * volume')
            ).
            by(
              math('((exit_price - entry_price) / entry_price) * 100')
            )
        )
    ).
    // Timing analysis
    by(
      project('days_before_announcement', 'coordination_score', 'timing_pattern').
        by(
          select('suspicious_trade').
          values('trade_date').
          fold().
          project('earliest', 'latest', 'avg_days_before').
            by(
              math('(announcement_date - min) / 86400000')
            ).
            by(
              math('(announcement_date - max) / 86400000')
            ).
            by(
              math('(announcement_date - mean) / 86400000')
            )
        ).
        // Coordination score (trades within 48 hours = coordinated)
        by(
          select('suspicious_trade').
          values('trade_date').
          fold().
          project('time_clustering').
            by(
              // Calculate if trades clustered within 48 hours
              math('(max - min) / 3600000 < 48 ? 100 : 0')
            )
        ).
        by(
          select('suspicious_trade').
          group().
            by(
              // Group by day
              values('trade_date').
              math('floor(_ / 86400000)')
            ).
            by(count()).
          select(values).
          max(local)
        )
    ).
    // Risk assessment
    by(
      project('insider_risk', 'network_risk', 'timing_risk', 'profit_risk', 'overall_risk', 'recommendation').
        // Insider risk (position + access)
        by(
          choose(
            select('insider_info').select('access_level').is(true),
            constant(30),
            constant(15)
          )
        ).
        // Network risk (size + offshore accounts)
        by(
          math('network_size * 5 + offshore_accounts * 10')
        ).
        // Timing risk (how close to announcement)
        by(
          choose(
            select('timing_analysis').select('avg_days_before').is(lte(7)),
            constant(30),
            choose(
              select('timing_analysis').select('avg_days_before').is(lte(14)),
              constant(20),
              constant(10)
            )
          )
        ).
        // Profit risk (abnormal profits)
        by(
          choose(
            select('trading_pattern').select('profit_analysis').select('profit_percentage').is(gte(50)),
            constant(25),
            choose(
              select('trading_pattern').select('profit_analysis').select('profit_percentage').is(gte(25)),
              constant(15),
              constant(5)
            )
          )
        ).
        // Overall risk
        by(
          math('insider_risk + network_risk + timing_risk + profit_risk')
        ).
        // Recommendation
        by(
          choose(
            select('overall_risk').is(gte(80)),
            constant('CRITICAL: Report to SEC immediately - Strong insider trading indicators'),
            choose(
              select('overall_risk').is(gte(60)),
              constant('HIGH: Escalate to compliance - Suspicious pattern detected'),
              constant('MEDIUM: Monitor closely - Potential coincidence')
            )
          )
        )
    ).
  // Filter high-risk cases
  where(
    select('risk_assessment').
    select('overall_risk').
    is(gte(60))
  ).
  order().by(select('risk_assessment').select('overall_risk'), desc).
  limit(10)
```

---

## Hybrid Approach: OpenSearch + Gremlin

### Best Practice: Combine Both Technologies

**Use OpenSearch for:**

1. Transaction-level aggregations
2. Time-series analysis
3. Statistical operations
4. Full-text search
5. Vector similarity

**Use Gremlin for:**

1. Relationship analysis
2. Network detection
3. Path traversal
4. Pattern matching
5. Graph metrics

### Example: Hybrid TBML Detection

```python
from opensearchpy import OpenSearch
from gremlin_python.process.graph_traversal import __
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

# Step 1: OpenSearch - Find suspicious transactions
os_client = OpenSearch([{'host': 'localhost', 'port': 9200}])

suspicious_txns = os_client.search(
    index="trade_transactions",
    body={
        "size": 100,
        "query": {
            "bool": {
                "must": [
                    {"range": {"unit_price_variance": {"gte": 50}}},
                    {"range": {"trade_date": {"gte": "now-90d"}}}
                ]
            }
        },
        "aggs": {
            "by_company": {
                "terms": {"field": "company_id", "size": 50},
                "aggs": {
                    "price_stats": {"extended_stats": {"field": "unit_price"}},
                    "trade_count": {"value_count": {"field": "trade_id"}}
                }
            }
        }
    }
)

# Extract suspicious company IDs
suspicious_companies = [
    bucket['key']
    for bucket in suspicious_txns['aggregations']['by_company']['buckets']
    if bucket['trade_count']['value'] >= 5
]

# Step 2: Gremlin - Analyze company networks
g = traversal().with_remote(
    DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
)

for company_id in suspicious_companies:
    # Find circular trading patterns
    cycles = g.V().has('Company', 'company_id', company_id). \
        repeat(__.out('traded_with').simplePath()).times(3).emit().times(5). \
        where(__.out('traded_with').has('company_id', company_id)). \
        path(). \
        by(__.valueMap('company_name', 'country')). \
        toList()

    if cycles:
        print(f"🚨 TBML ALERT: Company {company_id} involved in circular trading")
        print(f"   Cycles detected: {len(cycles)}")
        print(f"   Network: {cycles[0]}")

# Step 3: Combined risk scoring
for company_id in suspicious_companies:
    # OpenSearch: Transaction metrics
    os_metrics = os_client.search(
        index="trade_transactions",
        body={
            "query": {"term": {"company_id": company_id}},
            "aggs": {
                "price_variance": {"extended_stats": {"field": "unit_price"}},
                "volume": {"sum": {"field": "total_value"}}
            }
        }
    )

    # Gremlin: Network metrics
    network_metrics = g.V().has('Company', 'company_id', company_id). \
        project('degree', 'shell_connections', 'sanctions_exposure'). \
        by(__.bothE().count()). \
        by(__.out('traded_with').has('is_shell_company', True).count()). \
        by(__.out('has_relationship').hasLabel('SanctionedEntity').count()). \
        next()

    # Calculate combined risk score
    price_var = os_metrics['aggregations']['price_variance']['std_deviation']
    volume = os_metrics['aggregations']['volume']['value']
    degree = network_metrics['degree']
    shells = network_metrics['shell_connections']
    sanctions = network_metrics['sanctions_exposure']

    risk_score = (
        (price_var / 100) * 30 +  # Price manipulation
        (volume / 1000000) * 20 +  # Volume
        degree * 2 +               # Network size
        shells * 15 +              # Shell companies
        sanctions * 25             # Sanctions exposure
    )

    print(f"\n📊 Risk Assessment: {company_id}")
    print(f"   Price Variance: {price_var:.2f}")
    print(f"   Trade Volume: ${volume:,.2f}")
    print(f"   Network Degree: {degree}")
    print(f"   Shell Connections: {shells}")
    print(f"   Sanctions Exposure: {sanctions}")
    print(f"   RISK SCORE: {risk_score:.2f}/100")

    if risk_score >= 75:
        print(f"   ⚠️  CRITICAL: Immediate investigation required")
```

---

## Summary

### Key Takeaways

1. **Gremlin OLAP** is powerful for relationship-based analysis
2. **OpenSearch OLAP** is faster for transaction-level aggregations
3. **Hybrid approach** provides comprehensive detection
4. **Complex scenarios** require multi-dimensional analysis
5. **Graph traversals** reveal hidden networks and patterns

### When to Use What

| Use Case | Technology | Reason |
|----------|-----------|--------|
| Transaction aggregations | OpenSearch | Fast, efficient |
| Network detection | Gremlin | Relationship traversal |
| Time-series analysis | OpenSearch | Date histograms |
| Path analysis | Gremlin | Multi-hop traversal |
| Text search | OpenSearch | Full-text capabilities |
| Pattern matching | Gremlin | Graph patterns |
| Statistical analysis | OpenSearch | Aggregation pipeline |
| Centrality metrics | Gremlin | Graph algorithms |

### Performance Tips

1. **Index properly** - Both OpenSearch and JanusGraph
2. **Use filters early** - Reduce traversal scope
3. **Limit results** - Don't fetch everything
4. **Cache frequently used queries**
5. **Monitor query performance**
6. **Use batch operations** for bulk analysis

---

**Document Version:** 1.0
**Last Updated:** 2026-01-28
**Status:** ✅ Complete
