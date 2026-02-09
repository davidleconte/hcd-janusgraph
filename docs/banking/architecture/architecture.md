# Synthetic Data Generators - Architecture

System architecture and design documentation for the synthetic data generation framework.

**Version**: 1.0.0
**Last Updated**: 2026-01-28

---

## Table of Contents

1. [Overview](#overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Design Patterns](#design-patterns)
6. [Extensibility](#extensibility)
7. [Performance Considerations](#performance-considerations)

---

## Overview

The synthetic data generation framework is designed to create realistic, complex financial crime patterns for testing and demonstration purposes. The system generates entities (persons, companies, accounts), events (transactions, communications, trades), and injects sophisticated patterns (insider trading, money laundering, fraud rings).

### Key Design Goals

1. **Modularity**: Independent, reusable generators
2. **Extensibility**: Easy to add new generators and patterns
3. **Reproducibility**: Deterministic generation with seeds
4. **Performance**: Efficient generation of large datasets
5. **Realism**: Statistically realistic data with proper relationships
6. **Testability**: Comprehensive test coverage

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Master Orchestrator                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Generation Configuration                    │  │
│  │  - Entity counts, pattern counts, seed, output dir   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Core          │   │ Event         │   │ Pattern       │
│ Generators    │   │ Generators    │   │ Generators    │
│               │   │               │   │               │
│ - Person      │   │ - Transaction │   │ - Insider     │
│ - Company     │   │ - Comm.       │   │ - TBML        │
│ - Account     │   │ - Trade       │   │ - Fraud Ring  │
│               │   │ - Travel      │   │ - Structuring │
│               │   │ - Document    │   │ - CATO        │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  Data Models  │
                    │  (Pydantic)   │
                    └───────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    Export     │
                    │ JSON/CSV/etc  │
                    └───────────────┘
```

### Architecture Layers

1. **Orchestration Layer**: Coordinates generation workflow
2. **Generator Layer**: Creates entities, events, and patterns
3. **Data Model Layer**: Defines data structures and validation
4. **Utility Layer**: Shared helpers and constants
5. **Export Layer**: Data serialization and output

---

## Component Architecture

### 1. Base Generator

All generators inherit from `BaseGenerator`:

```python
class BaseGenerator:
    """Base class for all generators"""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self.faker = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)
```

**Responsibilities**:

- Initialize Faker with seed
- Provide common generation utilities
- Ensure reproducibility

**Design Pattern**: Template Method Pattern

### 2. Core Generators

Generate fundamental entities:

```
BaseGenerator
    │
    ├── PersonGenerator
    │   └── generate() -> Person
    │
    ├── CompanyGenerator
    │   └── generate() -> Company
    │
    └── AccountGenerator
        └── generate(owner) -> Account
```

**Key Features**:

- Independent generation
- Realistic attribute distribution
- Risk scoring
- Relationship management

### 3. Event Generators

Generate time-series events:

```
BaseGenerator
    │
    ├── TransactionGenerator
    │   └── generate(from_account, to_account) -> Transaction
    │
    ├── CommunicationGenerator
    │   └── generate(from_person, to_person) -> Communication
    │
    ├── TradeGenerator
    │   └── generate(account) -> Trade
    │
    ├── TravelGenerator
    │   └── generate(person) -> Travel
    │
    └── DocumentGenerator
        └── generate(owner) -> Document
```

**Key Features**:

- Temporal consistency
- Entity relationships
- Realistic patterns
- Suspicious flag generation

### 4. Pattern Generators

Inject complex patterns:

```
BaseGenerator
    │
    ├── InsiderTradingPatternGenerator
    │   └── inject_pattern(persons, companies, accounts, trades, comms)
    │
    ├── TBMLPatternGenerator
    │   └── inject_pattern(companies, accounts, transactions, documents)
    │
    ├── FraudRingPatternGenerator
    │   └── inject_pattern(persons, accounts, transactions)
    │
    ├── StructuringPatternGenerator
    │   └── inject_pattern(persons, accounts, transactions)
    │
    └── CATOPatternGenerator
        └── inject_pattern(persons, accounts, transactions)
```

**Key Features**:

- Multi-entity coordination
- Temporal sequencing
- Realistic indicators
- Pattern metadata

### 5. Master Orchestrator

Coordinates entire generation process:

```python
class MasterOrchestrator:
    def __init__(self, config: GenerationConfig):
        self.config = config
        self._initialize_generators()

    def generate_all(self) -> GenerationStats:
        # Phase 1: Core entities
        self._generate_core_entities()

        # Phase 2: Events
        self._generate_events()

        # Phase 3: Patterns
        self._inject_patterns()

        # Phase 4: Export
        return self._collect_stats()
```

**Responsibilities**:

- Initialize all generators
- Coordinate generation phases
- Manage entity relationships
- Track statistics
- Handle errors

---

## Data Flow

### Generation Pipeline

```
1. Configuration
   ↓
2. Core Entity Generation
   ├── Persons (parallel)
   ├── Companies (parallel)
   └── Accounts (depends on persons/companies)
   ↓
3. Event Generation
   ├── Transactions (depends on accounts)
   ├── Communications (depends on persons)
   ├── Trades (depends on accounts)
   ├── Travels (depends on persons)
   └── Documents (depends on persons/companies)
   ↓
4. Pattern Injection
   ├── Select entities for pattern
   ├── Generate pattern-specific events
   ├── Update entity metadata
   └── Track pattern information
   ↓
5. Export
   ├── Serialize to JSON/CSV
   ├── Generate statistics
   └── Write to disk
```

### Data Dependencies

```
Person ──┐
         ├──> Account ──> Transaction
Company ─┘                    │
                              ├──> Pattern Detection
Person ──> Communication      │
                              │
Account ──> Trade ────────────┤
                              │
Person ──> Travel ────────────┤
                              │
Person/Company ──> Document ──┘
```

### Referential Integrity

All relationships maintain referential integrity:

1. **Accounts** reference valid persons or companies
2. **Transactions** reference valid accounts
3. **Communications** reference valid persons
4. **Trades** reference valid accounts
5. **Travels** reference valid persons
6. **Documents** reference valid persons or companies

---

## Design Patterns

### 1. Template Method Pattern

**Used In**: BaseGenerator

```python
class BaseGenerator:
    def generate(self):
        # Template method
        self._validate_preconditions()
        entity = self._create_entity()
        self._post_process(entity)
        return entity
```

**Benefits**:

- Consistent generation workflow
- Easy to extend
- Enforces best practices

### 2. Factory Pattern

**Used In**: Generator instantiation

```python
class GeneratorFactory:
    @staticmethod
    def create_generator(generator_type: str, seed: int):
        if generator_type == "person":
            return PersonGenerator(seed)
        elif generator_type == "company":
            return CompanyGenerator(seed)
        # ...
```

**Benefits**:

- Centralized creation logic
- Easy to add new generators
- Consistent initialization

### 3. Strategy Pattern

**Used In**: Pattern injection

```python
class PatternInjector:
    def __init__(self, strategy: PatternGenerator):
        self.strategy = strategy

    def inject(self, data):
        return self.strategy.inject_pattern(data)
```

**Benefits**:

- Interchangeable patterns
- Easy to add new patterns
- Testable in isolation

### 4. Builder Pattern

**Used In**: Configuration

```python
config = (GenerationConfig()
    .with_seed(42)
    .with_persons(1000)
    .with_companies(500)
    .with_patterns(insider_trading=2, fraud_ring=1)
    .build())
```

**Benefits**:

- Fluent API
- Validation at build time
- Immutable configuration

### 5. Observer Pattern

**Used In**: Statistics tracking

```python
class StatisticsObserver:
    def on_entity_generated(self, entity_type: str):
        self.stats[entity_type] += 1

    def on_pattern_injected(self, pattern_type: str):
        self.patterns[pattern_type] += 1
```

**Benefits**:

- Decoupled statistics
- Real-time monitoring
- Easy to add metrics

---

## Extensibility

### Adding New Generators

1. **Inherit from BaseGenerator**:

```python
class NewGenerator(BaseGenerator):
    def generate(self, **kwargs) -> NewEntity:
        # Implementation
        pass
```

2. **Define Data Model**:

```python
@dataclass
class NewEntity:
    entity_id: str
    # ... other fields
```

3. **Register with Orchestrator**:

```python
class MasterOrchestrator:
    def _initialize_generators(self):
        # ... existing generators
        self.new_generator = NewGenerator(self.config.seed)
```

### Adding New Patterns

1. **Inherit from BaseGenerator**:

```python
class NewPatternGenerator(BaseGenerator):
    def inject_pattern(self, entities, events) -> Dict[str, Any]:
        # Pattern injection logic
        return pattern_metadata
```

2. **Add to Configuration**:

```python
@dataclass
class GenerationConfig:
    # ... existing fields
    new_pattern_count: int = 0
```

3. **Integrate with Orchestrator**:

```python
def _inject_patterns(self):
    # ... existing patterns
    for _ in range(self.config.new_pattern_count):
        self.new_pattern_gen.inject_pattern(...)
```

### Custom Export Formats

1. **Implement Exporter**:

```python
class CustomExporter:
    def export(self, data: Dict, output_path: Path):
        # Custom export logic
        pass
```

2. **Register with Orchestrator**:

```python
orchestrator.register_exporter("custom", CustomExporter())
orchestrator.export("custom", output_path)
```

---

## Performance Considerations

### 1. Memory Management

**Strategy**: Generate in batches, don't hold all data in memory

```python
def generate_large_dataset(count: int, batch_size: int = 1000):
    for i in range(0, count, batch_size):
        batch = [generator.generate() for _ in range(batch_size)]
        process_batch(batch)
        del batch  # Free memory
```

### 2. Parallel Generation

**Strategy**: Generate independent entities in parallel

```python
from concurrent.futures import ThreadPoolExecutor

def generate_parallel(count: int):
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(generator.generate)
                   for _ in range(count)]
        return [f.result() for f in futures]
```

### 3. Caching

**Strategy**: Cache expensive computations

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_risk_score(entity_type: str, attributes: tuple) -> float:
    # Expensive calculation
    return calculate_risk(entity_type, attributes)
```

### 4. Lazy Loading

**Strategy**: Generate data on-demand

```python
class LazyGenerator:
    def __iter__(self):
        for _ in range(self.count):
            yield self.generator.generate()
```

### 5. Profiling

**Tools**:

- `cProfile` for CPU profiling
- `memory_profiler` for memory profiling
- `py-spy` for production profiling

```python
import cProfile

profiler = cProfile.Profile()
profiler.enable()
orchestrator.generate_all()
profiler.disable()
profiler.print_stats(sort='cumulative')
```

---

## Security Considerations

### 1. Seed Management

- Never use predictable seeds in production
- Store seeds securely for reproducibility
- Use cryptographically secure random for sensitive data

### 2. Data Sanitization

- Ensure generated data doesn't contain real PII
- Validate all generated data
- Implement data retention policies

### 3. Access Control

- Restrict access to generation tools
- Log all generation activities
- Implement audit trails

---

## Testing Architecture

### Test Pyramid

```
        ┌─────────────┐
        │ Integration │  (10%)
        │   Tests     │
        ├─────────────┤
        │   Unit      │  (70%)
        │   Tests     │
        ├─────────────┤
        │   Smoke     │  (20%)
        │   Tests     │
        └─────────────┘
```

### Test Categories

1. **Smoke Tests**: Quick validation
2. **Unit Tests**: Individual components
3. **Integration Tests**: End-to-end workflows
4. **Performance Tests**: Speed and scalability
5. **Data Quality Tests**: Statistical validation

---

## Deployment Architecture

### Development Environment

```
Developer Machine
├── Python 3.11+
├── Virtual Environment
├── Development Dependencies
└── Local Testing
```

### Production Environment

```
Production Server
├── Docker Container
│   ├── Python Runtime
│   ├── Application Code
│   └── Dependencies
├── Configuration Management
├── Monitoring & Logging
└── Data Storage
```

### Scaling Strategy

1. **Vertical Scaling**: Increase CPU/memory
2. **Horizontal Scaling**: Multiple generator instances
3. **Batch Processing**: Process in chunks
4. **Distributed Generation**: Coordinate across nodes

---

## Monitoring & Observability

### Metrics

- Generation throughput (entities/second)
- Memory usage
- Error rates
- Pattern injection success rate

### Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Generated {count} persons in {duration}s")
logger.warning(f"Low quality data detected: {entity_id}")
logger.error(f"Generation failed: {error}")
```

### Alerting

- Generation failures
- Performance degradation
- Data quality issues
- Resource exhaustion

---

## Future Enhancements

### Planned Features

1. **Real-time Generation**: Stream generation
2. **ML-based Patterns**: Learn from real data
3. **Graph Export**: Direct JanusGraph loading
4. **API Service**: REST API for generation
5. **UI Dashboard**: Web-based configuration

### Extensibility Points

1. Custom generators
2. Custom patterns
3. Custom export formats
4. Custom validation rules
5. Custom risk scoring

---

## Conclusion

The synthetic data generation framework provides a robust, extensible architecture for creating realistic financial crime patterns. The modular design enables easy extension while maintaining performance and data quality.

**Key Strengths**:

- Modular, extensible design
- High performance
- Comprehensive testing
- Production-ready
- Well-documented

---

**Version**: 1.0.0
**Last Updated**: 2026-01-28
**Maintained By**: Development Team
