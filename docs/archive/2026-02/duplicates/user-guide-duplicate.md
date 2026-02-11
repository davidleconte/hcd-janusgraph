# Synthetic Data Generators - User Guide

Complete guide for using the synthetic data generation framework.

**Version**: 1.0.0  
**Last Updated**: 2026-01-28

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Concepts](#basic-concepts)
3. [Quick Start](#quick-start)
4. [Common Tasks](#common-tasks)
5. [Advanced Usage](#advanced-usage)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- pip or uv package manager
- 4GB+ RAM (8GB+ recommended for large datasets)
- 1GB+ disk space

### Installation

#### Option 1: Using pip

```bash
# Clone repository
git clone <repository-url>
cd hcd-tarball-janusgraph

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r banking/data_generators/requirements.txt
```

#### Option 2: Using uv (faster)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install -r banking/data_generators/requirements.txt
```

### Verify Installation

```bash
python -c "from banking.data_generators.core import PersonGenerator; print('Installation successful!')"
```

---

## Basic Concepts

### Generators

**Generators** create synthetic data entities and events:

- **Core Generators**: Create fundamental entities (Person, Company, Account)
- **Event Generators**: Create time-series events (Transaction, Communication, Trade)
- **Pattern Generators**: Inject complex patterns (Insider Trading, Money Laundering)

### Orchestrator

The **MasterOrchestrator** coordinates all generators and manages the generation workflow.

### Configuration

**GenerationConfig** defines what data to generate:

```python
config = GenerationConfig(
    seed=42,              # For reproducibility
    person_count=100,     # Number of persons
    company_count=50,     # Number of companies
    account_count=200,    # Number of accounts
    transaction_count=1000  # Number of transactions
)
```

### Seeds

**Seeds** ensure reproducible results. Same seed = same data.

```python
# These will generate identical data
gen1 = PersonGenerator(seed=42)
gen2 = PersonGenerator(seed=42)
```

---

## Quick Start

### Example 1: Generate a Single Person

```python
from banking.data_generators.core import PersonGenerator

# Create generator
generator = PersonGenerator(seed=42)

# Generate person
person = generator.generate()

# Access attributes
print(f"Name: {person.first_name} {person.last_name}")
print(f"Age: {person.age}")
print(f"Risk Level: {person.risk_level}")
```

### Example 2: Generate Multiple Entities

```python
from banking.data_generators.core import (
    PersonGenerator,
    CompanyGenerator,
    AccountGenerator
)

# Create generators
person_gen = PersonGenerator(seed=42)
company_gen = CompanyGenerator(seed=42)
account_gen = AccountGenerator(seed=42)

# Generate entities
persons = [person_gen.generate() for _ in range(10)]
companies = [company_gen.generate() for _ in range(5)]

# Generate accounts for persons
accounts = [account_gen.generate(owner=person) for person in persons]

print(f"Generated {len(persons)} persons")
print(f"Generated {len(companies)} companies")
print(f"Generated {len(accounts)} accounts")
```

### Example 3: Generate Complete Dataset

```python
from pathlib import Path
from banking.data_generators.orchestration import (
    MasterOrchestrator,
    GenerationConfig
)

# Configure generation
config = GenerationConfig(
    seed=42,
    person_count=100,
    company_count=50,
    account_count=200,
    transaction_count=1000,
    output_dir=Path("./output")
)

# Create orchestrator
orchestrator = MasterOrchestrator(config)

# Generate all data
stats = orchestrator.generate_all()

# Print statistics
print(f"Persons: {stats.persons_generated}")
print(f"Companies: {stats.companies_generated}")
print(f"Accounts: {stats.accounts_generated}")
print(f"Transactions: {stats.transactions_generated}")
```

---

## Common Tasks

### Task 1: Generate Test Data for Development

```python
from pathlib import Path
from banking.data_generators.orchestration import (
    MasterOrchestrator,
    GenerationConfig
)

# Small dataset for development
config = GenerationConfig(
    seed=42,
    person_count=50,
    company_count=25,
    account_count=100,
    transaction_count=500,
    output_dir=Path("./test_data")
)

orchestrator = MasterOrchestrator(config)
stats = orchestrator.generate_all()

print(f"Test data generated: {stats.persons_generated + stats.companies_generated + stats.accounts_generated} entities")
```

### Task 2: Generate Data with Patterns

```python
# Generate data with financial crime patterns
config = GenerationConfig(
    seed=42,
    person_count=500,
    company_count=250,
    account_count=1000,
    transaction_count=10000,
    
    # Add patterns
    insider_trading_patterns=2,
    fraud_ring_patterns=1,
    structuring_patterns=3,
    
    output_dir=Path("./pattern_data")
)

orchestrator = MasterOrchestrator(config)
stats = orchestrator.generate_all()

print(f"Patterns injected: {stats.patterns_injected}")
```

### Task 3: Export Data to JSON

```python
from pathlib import Path

# Generate data
orchestrator = MasterOrchestrator(config)
stats = orchestrator.generate_all()

# Export to JSON
output_file = Path("./output/data.json")
orchestrator.export_to_json(output_file)

print(f"Data exported to: {output_file}")
```

### Task 4: Generate Reproducible Data

```python
# Use same seed for reproducibility
SEED = 42

config1 = GenerationConfig(seed=SEED, person_count=100)
config2 = GenerationConfig(seed=SEED, person_count=100)

orch1 = MasterOrchestrator(config1)
orch2 = MasterOrchestrator(config2)

stats1 = orch1.generate_all()
stats2 = orch2.generate_all()

# These will be identical
assert stats1.persons_generated == stats2.persons_generated
```

### Task 5: Generate Large Dataset

```python
# Large dataset for performance testing
config = GenerationConfig(
    seed=42,
    person_count=10000,
    company_count=5000,
    account_count=20000,
    transaction_count=100000,
    output_dir=Path("./large_data")
)

orchestrator = MasterOrchestrator(config)

print("Generating large dataset (this may take a few minutes)...")
stats = orchestrator.generate_all()

print(f"Generated {stats.persons_generated + stats.companies_generated + stats.accounts_generated:,} entities")
print(f"Duration: {stats.duration_seconds:.2f}s")
```

---

## Advanced Usage

### Custom Generation Logic

```python
from banking.data_generators.core import PersonGenerator

# Create custom generator
class CustomPersonGenerator(PersonGenerator):
    def generate(self):
        person = super().generate()
        
        # Add custom logic
        if person.age > 65:
            person.risk_level = "low"
        
        return person

# Use custom generator
custom_gen = CustomPersonGenerator(seed=42)
person = custom_gen.generate()
```

### Batch Processing

```python
def generate_in_batches(total_count, batch_size=1000):
    """Generate data in batches to manage memory"""
    generator = PersonGenerator(seed=42)
    
    for i in range(0, total_count, batch_size):
        batch = [generator.generate() for _ in range(batch_size)]
        
        # Process batch
        process_batch(batch)
        
        # Free memory
        del batch
        
        print(f"Processed {i + batch_size}/{total_count}")

generate_in_batches(10000, batch_size=1000)
```

### Parallel Generation

```python
from concurrent.futures import ThreadPoolExecutor

def generate_parallel(count, workers=4):
    """Generate data in parallel"""
    def generate_batch(seed_offset):
        gen = PersonGenerator(seed=42 + seed_offset)
        return [gen.generate() for _ in range(count // workers)]
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(generate_batch, i) 
                   for i in range(workers)]
        results = [f.result() for f in futures]
    
    # Flatten results
    return [item for batch in results for item in batch]

persons = generate_parallel(1000, workers=4)
print(f"Generated {len(persons)} persons in parallel")
```

### Custom Export Format

```python
import csv

def export_to_csv(persons, output_file):
    """Export persons to CSV"""
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(['ID', 'First Name', 'Last Name', 'Age', 'Risk Level'])
        
        # Data
        for person in persons:
            writer.writerow([
                person.person_id,
                person.first_name,
                person.last_name,
                person.age,
                person.risk_level
            ])

# Generate and export
generator = PersonGenerator(seed=42)
persons = [generator.generate() for _ in range(100)]
export_to_csv(persons, 'persons.csv')
```

---

## Best Practices

### 1. Always Use Seeds

```python
# ✅ Good: Reproducible
generator = PersonGenerator(seed=42)

# ❌ Bad: Non-reproducible
generator = PersonGenerator()
```

### 2. Reuse Generator Instances

```python
# ✅ Good: Efficient
generator = PersonGenerator(seed=42)
persons = [generator.generate() for _ in range(1000)]

# ❌ Bad: Inefficient
persons = [PersonGenerator(seed=42).generate() for _ in range(1000)]
```

### 3. Use Orchestrator for Complex Scenarios

```python
# ✅ Good: Coordinated generation
config = GenerationConfig(seed=42, person_count=1000)
orchestrator = MasterOrchestrator(config)
stats = orchestrator.generate_all()

# ❌ Bad: Manual coordination
person_gen = PersonGenerator(seed=42)
company_gen = CompanyGenerator(seed=42)
# ... manual coordination is error-prone
```

### 4. Handle Errors Gracefully

```python
# ✅ Good: Error handling
try:
    stats = orchestrator.generate_all()
except Exception as e:
    logger.error(f"Generation failed: {e}")
    # Handle error appropriately

# ❌ Bad: No error handling
stats = orchestrator.generate_all()  # May crash
```

### 5. Validate Generated Data

```python
# ✅ Good: Validation
person = generator.generate()
assert person.age >= 18, "Person must be adult"
assert person.risk_score >= 0 and person.risk_score <= 1

# ❌ Bad: No validation
person = generator.generate()
;