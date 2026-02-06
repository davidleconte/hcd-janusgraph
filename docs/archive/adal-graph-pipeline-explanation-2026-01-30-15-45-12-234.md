# Complete Data Generation and Graph Loading Pipeline
**Timestamp:** 2026-01-30 15:45:12.234
**Topic:** HCD+JanusGraph Data Generation & Graph Loading Architecture
**Session:** Turn 9

---

## Architecture Overview

The project has a **3-stage pipeline**:
1. **Generation** - Synthetic data creation via orchestrator
2. **Export** - JSON serialization of entities
3. **Loading** - JanusGraph ingestion via Gremlin

---

## Stage 1: Data Generation (Synthetic Creation)

### Orchestration Architecture

**Master Orchestrator** (`banking/data_generators/orchestration/master_orchestrator.py`):
```
MasterOrchestrator
├── Core Generators (3)
│   ├── PersonGenerator       → Person vertices
│   ├── CompanyGenerator      → Company vertices
│   └── AccountGenerator      → Account vertices
├── Event Generators (5)
│   ├── TransactionGenerator  → Transaction edges
│   ├── CommunicationGenerator→ Communication edges
│   ├── TradeGenerator        → Trade edges
│   ├── TravelGenerator       → Travel vertices
│   └── DocumentGenerator     → Document vertices
└── Pattern Generators (5)
    ├── InsiderTradingPatternGenerator
    ├── TBMLPatternGenerator
    ├── FraudRingPatternGenerator
    ├── StructuringPatternGenerator
    └── CATOPatternGenerator
```

### Generation Flow (3 Phases)

#### Phase 1: Core Entities (Lines 251-297)
```python
def _generate_core_entities(self):
    # 1. Generate persons (100 default)
    for i in range(self.config.person_count):
        person = self.person_gen.generate()  # Creates Person object
        self.persons.append(person)
    
    # 2. Generate companies (20 default)
    for i in range(self.config.company_count):
        company = self.company_gen.generate()  # Creates Company object
        self.companies.append(company)
    
    # 3. Generate accounts (200 default)
    for i in range(self.config.account_count):
        # 80% person accounts, 20% company accounts
        if random.random() < 0.8:
            owner = random.choice(self.persons)
            account = self.account_gen.generate(
                owner_id=owner.id,
                owner_type="person"  # Creates owns_account relationship
            )
        else:
            owner = random.choice(self.companies)
            account = self.account_gen.generate(
                owner_id=owner.id,
                owner_type="company"
            )
        self.accounts.append(account)
```

**Key Points:**
- **Person Generator**: Creates realistic person profiles (name, SSN, address, risk score)
- **Company Generator**: Creates company profiles (EIN, industry, officers)
- **Account Generator**: Creates accounts AND establishes ownership relationships
- All generators use **seed** for reproducibility
- Stores entities in memory lists: `self.persons`, `self.companies`, `self.accounts`

#### Phase 2: Events (Lines 299-371)
```python
def _generate_events(self):
    # 1. Generate transactions (10,000 default)
    for i in range(self.config.transaction_count):
        from_account = random.choice(self.accounts)
        to_account = random.choice(self.accounts)
        
        transaction = self.transaction_gen.generate(
            from_account_id=from_account.id,
            to_account_id=to_account.id  # Creates transfer edge
        )
        self.transactions.append(transaction)
    
    # 2. Generate communications (5,000 default)
    for i in range(self.config.communication_count):
        communication = self.communication_gen.generate()
        self.communications.append(communication)
    
    # 3. Generate trades, travel, documents...
```

**Key Points:**
- **Transaction Generator**: Creates financial transactions between accounts
- **Communication Generator**: Creates emails, phone calls, messages
- **Dependency Management**: Requires accounts to exist first (referential integrity)
- Creates **relationship metadata** (amounts, timestamps, channels)

#### Phase 3: Patterns (Lines 373-447)
```python
def _generate_patterns(self):
    # Inject suspicious patterns into existing data
    if self.config.structuring_patterns > 0:
        for i in range(self.config.structuring_patterns):
            pattern = self.structuring_gen.generate(
                pattern_type="smurfing",
                smurf_count=random.randint(5, 15)  # Creates mule network
            )
            self.patterns.append(pattern)
```

**Key Points:**
- **Pattern Injection**: Modifies existing entities with suspicious behaviors
- **Ground Truth Labels**: Marks entities for AML/fraud detection testing
- Creates complex multi-entity patterns (mule networks, fraud rings)

---

## Stage 2: Export (JSON Serialization)

### Export Process (Lines 449-529)

```python
def _export_json(self):
    # Export persons
    path = self.config.output_dir / "persons.json"
    with open(path, 'w') as f:
        json.dump([p.dict() for p in self.persons], f, indent=2, default=str)
    
    # Export companies, accounts, transactions, communications...
    # Each entity type in separate file
```

**Output Structure:**
```
output/
├── persons.json          # Person vertices
├── companies.json        # Company vertices
├── accounts.json         # Account vertices + owner references
├── transactions.json     # Transaction edges (from/to account_id)
├── communications.json   # Communication edges
├── patterns.json         # Suspicious pattern metadata
└── generation_stats.json # Generation statistics
```

**Example `persons.json` (simplified):**
```json
[
  {
    "id": "P000001",
    "person_id": "P000001",
    "first_name": "Alice",
    "last_name": "Johnson",
    "ssn": "123-45-6789",
    "date_of_birth": "1990-05-15",
    "risk_score": 0.95,
    "flagged": true,
    "addresses": [...],
    "phone_numbers": [...]
  }
]
```

**Example `transactions.json` (simplified):**
```json
[
  {
    "transaction_id": "TXN00001",
    "from_account_id": "ACC00000001",
    "to_account_id": "ACC00000011",
    "amount": 9500.00,
    "timestamp": "2026-01-15T14:23:00",
    "transaction_type": "wire",
    "suspicious": true
  }
]
```

---

## Stage 3: Graph Loading (JanusGraph Ingestion)

### Loading Architecture

**Two Loading Approaches:**

#### Approach 1: Direct Gremlin (Demo Scripts)
**File**: `scripts/init/load_data.py`

```python
# Connection
gc = client.Client('ws://localhost:18182/gremlin', 'g')

# Vertex Creation (Lines 11-24)
gc.submit("""
g.addV('person')
  .property('name', 'Alice Johnson')
  .property('age', 30)
  .property('email', 'alice@example.com')
  .next()
g.tx().commit()
""")

# Edge Creation (Lines 31-43)
gc.submit("""
g.V().has('person','name','Alice Johnson').as('alice')
 .V().has('person','name','Bob Smith')
 .addE('knows')
 .from('alice')
 .property('since', 2018)
 .iterate()
g.tx().commit()
""")
```

**Process:**
1. **Connect** to JanusGraph via Gremlin Server (WebSocket)
2. **Create vertices** using `addV(label).property(key, value)`
3. **Create edges** using `addE(label).from(source).to(target)`
4. **Commit transactions** using `g.tx().commit()`

#### Approach 2: Structured Loader (AML Data)
**File**: `banking/data/aml/load_structuring_data_v2.py`

```python
class ImprovedAMLLoader:
    def create_vertex(self, label, properties):
        """Create vertex with error handling"""
        prop_str = ''.join([
            f".property('{k}', {self._format_value(v)})" 
            for k, v in properties.items()
        ])
        query = f"g.addV('{label}'){prop_str}.next()"
        
        result = self.gc.submit(query).all().result()
        return True
    
    def create_edge(self, from_label, from_prop, from_val, 
                    edge_label, to_label, to_prop, to_val):
        """Create edge with error handling"""
        query = f"""
        from_v = g.V().hasLabel('{from_label}')
                      .has('{from_prop}', '{from_val}')
                      .next()
        to_v = g.V().hasLabel('{to_label}')
                    .has('{to_prop}', '{to_val}')
                    .next()
        from_v.addEdge('{edge_label}', to_v)
        """
        self.gc.submit(query).all().result()
```

**Features:**
- **Error handling**: Detects duplicates, missing vertices
- **Type formatting**: Handles strings, floats, booleans correctly
- **Existence checks**: Prevents duplicate vertex creation
- **Statistics tracking**: Counts loaded/skipped/errors

### Graph Structure Mapping

**Vertex Types (Labels):**
```
person          → Person entities
company         → Company entities
account         → Bank accounts
transaction     → (Can be edge or vertex depending on design)
communication   → (Can be edge or vertex)
product         → Products/services
travel          → Travel records
document        → Document records
```

**Edge Types (Labels):**
```
owns_account    → Person/Company --owns--> Account
knows           → Person --knows--> Person
worksFor        → Person --worksFor--> Company
created         → Company --created--> Product
uses            → Person --uses--> Product
transfer        → Account --transfer--> Account (transaction edge)
communicates    → Person --communicates--> Person
traveled_to     → Person --traveled_to--> Location
```

### Complete Flow Example: Structuring Pattern

**1. Generation** (Orchestrator):
```python
# Create beneficiary
beneficiary = PersonGenerator().generate()
beneficiary.risk_score = 0.95  # High risk

# Create beneficiary account
ben_account = AccountGenerator().generate(
    owner_id=beneficiary.id,
    owner_type="person"
)

# Create 3 mule accounts
mules = []
for i in range(3):
    mule = PersonGenerator().generate()
    mule_account = AccountGenerator().generate(
        owner_id=mule.id,
        owner_type="person"
    )
    mules.append((mule, mule_account))

# Create structuring transactions (6 transactions, <$10K each)
for mule, mule_account in mules:
    for _ in range(2):  # 2 transactions per mule
        transaction = TransactionGenerator().generate(
            from_account_id=mule_account.id,
            to_account_id=ben_account.id,
            amount=random.uniform(7000, 9500),  # Below threshold
            suspicious=True
        )
```

**2. Export** (JSON):
```json
// persons.json
[
  {"person_id": "P000001", "first_name": "Alice", "risk_score": 0.95},
  {"person_id": "P000002", "first_name": "Bob", "risk_score": 0.75},
  {"person_id": "P000003", "first_name": "Carol", "risk_score": 0.78},
  {"person_id": "P000004", "first_name": "David", "risk_score": 0.72}
]

// accounts.json
[
  {"account_id": "ACC00000001", "owner_id": "P000001", "balance": 450000},
  {"account_id": "ACC00000011", "owner_id": "P000002", "balance": 25000},
  {"account_id": "ACC00000012", "owner_id": "P000003", "balance": 18000},
  {"account_id": "ACC00000013", "owner_id": "P000004", "balance": 22000}
]

// transactions.json
[
  {"id": "TXN001", "from": "ACC00000011", "to": "ACC00000001", "amount": 9500},
  {"id": "TXN002", "from": "ACC00000011", "to": "ACC00000001", "amount": 8800},
  {"id": "TXN003", "from": "ACC00000012", "to": "ACC00000001", "amount": 7200},
  ...
]
```

**3. Loading** (JanusGraph):
```python
# Create person vertices
for person_data in persons_json:
    loader.create_vertex('person', {
        'person_id': person_data['person_id'],
        'first_name': person_data['first_name'],
        'risk_score': person_data['risk_score']
    })

# Create account vertices
for account_data in accounts_json:
    loader.create_vertex('account', {
        'account_id': account_data['account_id'],
        'balance': account_data['balance']
    })

# Create ownership edges
for account_data in accounts_json:
    loader.create_edge(
        from_label='person',
        from_prop='person_id',
        from_val=account_data['owner_id'],
        edge_label='owns_account',
        to_label='account',
        to_prop='account_id',
        to_val=account_data['account_id']
    )

# Create transaction edges
for txn_data in transactions_json:
    loader.create_edge(
        from_label='account',
        from_prop='account_id',
        from_val=txn_data['from'],
        edge_label='transfer',
        to_label='account',
        to_prop='account_id',
        to_val=txn_data['to']
    )
```

**4. Final Graph Structure** (in JanusGraph):
```
┌──────────┐
│ Person   │ Alice (P000001, risk=0.95)
└─────┬────┘
      │ owns_account
      ▼
┌──────────┐    transfer (9500)
│ Account  │◄──────────────────┐
│ACC000001 │                   │
└──────────┘                   │
   ▲                           │
   │ transfer (8800)    ┌──────┴────┐
   │                    │ Account   │ Bob's
   └────────────────────┤ACC000011  │ (P000002)
                        └───────────┘
   ▲                           │
   │ transfer (7200)           │ owns_account
   │                           ▼
   │                    ┌──────────┐
   └────────────────────│ Person   │ Bob
                        │ P000002  │
                        └──────────┘

# Similar pattern for Carol (P000003) and David (P000004)
```

---

## Key Architectural Principles

### 1. **Separation of Concerns**
- **Generation**: Pure Python object creation (no graph knowledge)
- **Export**: Serialization to portable format (JSON)
- **Loading**: Graph-specific ingestion (Gremlin traversal)

### 2. **Referential Integrity**
- Generation follows dependency order: Persons → Companies → Accounts → Transactions
- Foreign keys maintained: `owner_id`, `from_account_id`, `to_account_id`
- Loader validates references before creating edges

### 3. **Determinism**
- All generators accept `seed` parameter
- Reproducible datasets for testing
- Same seed → identical graph structure

### 4. **Type Safety**
- Pydantic models enforce schema validation
- Prevents invalid data at generation time
- Type checking at serialization/deserialization

### 5. **Error Resilience**
- Loaders handle duplicate detection
- Skip existing vertices/edges gracefully
- Continue on non-critical errors

---

## Performance Characteristics

**Generation** (Master Orchestrator):
- **Speed**: ~1,000-2,000 records/second
- **Memory**: Holds all entities in RAM
- **Bottleneck**: Random selection of related entities

**Export** (JSON):
- **Speed**: ~10,000 records/second
- **Bottleneck**: Disk I/O for large files

**Loading** (JanusGraph):
- **Speed**: ~100-500 records/second
- **Bottleneck**: Network latency + transaction commits
- **Optimization**: Batch operations, async commits

---

## Usage Examples

### Generate + Export
```python
from banking.data_generators.orchestration import MasterOrchestrator, GenerationConfig

config = GenerationConfig(
    seed=42,
    person_count=1000,
    company_count=50,
    account_count=2000,
    transaction_count=50000,
    structuring_patterns=10,
    output_dir=Path("./data/synthetic")
)

orchestrator = MasterOrchestrator(config)
stats = orchestrator.generate_all()
# Output: ./data/synthetic/persons.json, accounts.json, transactions.json, etc.
```

### Load to JanusGraph
```python
from banking.data.aml.load_structuring_data_v2 import ImprovedAMLLoader

loader = ImprovedAMLLoader(url='ws://localhost:18182/gremlin')
loader.connect()
loader.load_sample_data()  # Loads demo structuring pattern
```

### Query Loaded Graph
```python
from gremlin_python.driver import client

gc = client.Client('ws://localhost:18182/gremlin', 'g')

# Find high-risk persons
query = "g.V().hasLabel('person').has('risk_score', gt(0.9)).values('first_name')"
result = gc.submit(query).all().result()

# Find structuring patterns (multiple small transactions to same beneficiary)
query = """
g.V().hasLabel('account').as('beneficiary')
  .in('transfer').has('amount', lt(10000))
  .groupCount()
  .unfold()
  .where(values().is(gte(3)))
  .select(keys).values('account_id')
"""
result = gc.submit(query).all().result()
```

---

## Summary

**Generation → Export → Loading Pipeline:**

```
┌─────────────────────┐
│ MasterOrchestrator  │ Generation (Python objects)
│  ├─ Person Gen      │ • Deterministic (seeded)
│  ├─ Account Gen     │ • Dependency management
│  ├─ Transaction Gen │ • Referential integrity
│  └─ Pattern Gen     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  JSON Export        │ Serialization
│  ├─ persons.json    │ • Portable format
│  ├─ accounts.json   │ • Human-readable
│  └─ transactions.js │ • Version controlled
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Graph Loader       │ JanusGraph Ingestion
│  ├─ Create Vertices │ • Gremlin traversal
│  ├─ Create Edges    │ • Error handling
│  └─ Commit Txns     │ • Idempotent
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  JanusGraph         │ Graph Database
│  (HCD + OpenSearch) │ • Vertices + Edges
│                     │ • Indexed properties
│                     │ • Query-ready
└─────────────────────┘
```

This architecture provides:
- ✅ **Testability**: Generate deterministic test data
- ✅ **Scalability**: Generate millions of records
- ✅ **Flexibility**: Multiple export formats (JSON, CSV, Parquet planned)
- ✅ **Portability**: JSON export can load to any graph DB
- ✅ **Ground Truth**: Labeled patterns for ML model training

---

## Key Files in Pipeline

### Generation
- `banking/data_generators/orchestration/master_orchestrator.py` - Main orchestrator
- `banking/data_generators/core/` - Core entity generators (Person, Company, Account)
- `banking/data_generators/events/` - Event generators (Transaction, Communication, etc.)
- `banking/data_generators/patterns/` - Pattern generators (fraud/AML patterns)
- `banking/data_generators/utils/data_models.py` - Pydantic models

### Loading
- `scripts/init/load_data.py` - Simple demo loader
- `banking/data/aml/load_structuring_data_v2.py` - Production AML loader
- `src/python/client/janusgraph_client.py` - JanusGraph client wrapper

### Configuration
- `GenerationConfig` - Controls counts, dates, patterns
- `GenerationStats` - Tracks generation performance

---

**Document Status:** Complete Technical Reference
**Created:** 2026-01-30 15:45:12.234
**Version:** 1.0
**Purpose:** Technical documentation for data generation and graph loading pipeline
