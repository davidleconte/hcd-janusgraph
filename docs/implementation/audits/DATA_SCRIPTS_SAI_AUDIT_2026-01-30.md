# Data Generation & Loading Scripts - SAI Compliance Audit

**Date:** 2026-01-30  
**Status:** CRITICAL ISSUES IDENTIFIED  
**Scope:** Data generation, loading, and ETL pipeline scripts

---

## Executive Summary

### Critical Findings
- **8 Critical Issues** in data generation/loading scripts
- **Port Hardcoding:** All scripts use hardcoded port 18182 (incorrect)
- **No Environment Validation:** Scripts don't check Python environment
- **Schema Misalignment:** Generated data doesn't match technical specifications
- **No Container Awareness:** Scripts assume local deployment, not containerized

### Scripts Audited
1. `banking/data/aml/generate_structuring_data.py` (477 lines)
2. `banking/data/aml/load_structuring_data.py` (378 lines)
3. `scripts/deployment/load_production_data.py` (297 lines)
4. `src/python/init/load_data.py` (137 lines)

---

## Critical Issues

### 1. Hardcoded Port Configuration (🔴 CRITICAL)

**Issue:** All scripts use port `18182` instead of standard `8182`

**Affected Files:**
- `load_structuring_data.py` line 24: `ws://localhost:18182/gremlin`
- `load_production_data.py` line 45: `janusgraph_port: int = 18182`
- `load_data.py` line 8: `ws://localhost:18182/gremlin`

**Technical Specifications (Section 1.3.2):**
- JanusGraph Gremlin port: **8182** (not 18182)
- Management port: 8184

**Impact:**
- Scripts will fail to connect to JanusGraph
- Port 18182 is non-standard and not documented
- Breaks containerized deployment

**Correction Required:**
```python
# WRONG:
gc = client.Client('ws://localhost:18182/gremlin', 'g')

# CORRECT:
JANUSGRAPH_HOST = os.getenv('JANUSGRAPH_HOST', 'localhost')
JANUSGRAPH_PORT = int(os.getenv('JANUSGRAPH_PORT', '8182'))
gc = client.Client(f'ws://{JANUSGRAPH_HOST}:{JANUSGRAPH_PORT}/gremlin', 'g')
```

---

### 2. No Python Environment Validation (🔴 CRITICAL)

**Issue:** Scripts don't validate Python environment before execution

**Technical Confrontation Analysis (Section 1.1):**
- Python 3.11 required in conda environment
- Scripts should fail fast if wrong environment

**Impact:**
- May run with wrong Python version
- Dependency issues not caught early
- Silent failures possible

**Correction Required:**
```python
#!/usr/bin/env python3
"""
Script header with environment validation
"""
import sys
import os

# Validate Python version
if sys.version_info < (3, 11):
    print(f"❌ ERROR: Python 3.11+ required, found {sys.version_info.major}.{sys.version_info.minor}")
    sys.exit(1)

# Validate conda environment
if 'CONDA_DEFAULT_ENV' not in os.environ:
    print("❌ ERROR: No conda environment active")
    print("   Run: conda activate janusgraph-analysis")
    sys.exit(1)

if os.environ['CONDA_DEFAULT_ENV'] != 'janusgraph-analysis':
    print(f"❌ ERROR: Wrong conda environment: {os.environ['CONDA_DEFAULT_ENV']}")
    print("   Run: conda activate janusgraph-analysis")
    sys.exit(1)
```

---

### 3. Schema Misalignment with Technical Specifications (🔴 CRITICAL)

**Issue:** Generated data schema doesn't match technical specifications

**generate_structuring_data.py** creates:
```python
person = {
    'person_id': ...,
    'first_name': ...,
    'last_name': ...,
    'ssn': ...,
    'date_of_birth': ...,
    'risk_score': ...,  # Float 0.0-1.0
    'flagged': ...,
    'flag_reason': ...
}
```

**Technical Specifications (Section 2.2.1)** requires:
```python
person = {
    'personId': ...,        # UUID format
    'firstName': ...,
    'lastName': ...,
    'middleName': ...,      # MISSING
    'dateOfBirth': ...,
    'ssn': ...,
    'email': ...,           # LIST
    'phone': ...,           # LIST
    'nationality': ...,     # MISSING
    'occupation': ...,      # MISSING
    'riskScore': ...,       # Integer 0-100, not float
    'riskLevel': ...,       # Enum: low/medium/high/critical
    'pepStatus': ...,
    'sanctioned': ...,
    'createdAt': ...,       # MISSING
    'updatedAt': ...,       # MISSING
    'metadata': ...         # MISSING
}
```

**Impact:**
- Data won't load correctly into JanusGraph
- Queries will fail (missing properties)
- Indexes won't work (wrong property names)

**Correction Required:**
1. Update `generate_structuring_data.py` to match spec schema
2. Convert `risk_score` from float to integer (0-100)
3. Add `riskLevel` enum calculation
4. Add missing properties
5. Use camelCase for property names (JanusGraph convention)

---

### 4. No Container Awareness (🔴 CRITICAL)

**Issue:** Scripts assume local deployment, not containerized

**Current:**
```python
# Hardcoded localhost
gc = client.Client('ws://localhost:18182/gremlin', 'g')
```

**Technical Specifications (Section 1.2, 4.1):**
- Services run in pods with project prefixes
- Container names: `janusgraph-demo-janusgraph-server`
- Network: `janusgraph-demo-network`

**Impact:**
- Scripts fail when run from host (can't reach containers)
- No support for remote deployment
- Breaks pod-based architecture

**Correction Required:**
```python
import os

# Support both local and containerized deployment
JANUSGRAPH_HOST = os.getenv('JANUSGRAPH_HOST', 'localhost')
JANUSGRAPH_PORT = int(os.getenv('JANUSGRAPH_PORT', '8182'))
JANUSGRAPH_SSL = os.getenv('JANUSGRAPH_SSL', 'false').lower() == 'true'

protocol = 'wss' if JANUSGRAPH_SSL else 'ws'
url = f'{protocol}://{JANUSGRAPH_HOST}:{JANUSGRAPH_PORT}/gremlin'

gc = client.Client(url, 'g')
```

---

### 5. Missing Error Handling and Retry Logic (🟠 HIGH)

**Issue:** No retry logic for transient failures

**Current (load_structuring_data.py line 89):**
```python
try:
    self.gc.submit(query, bindings).all().result()
    self.stats['persons'] += 1
except GremlinServerError as e:
    print(f"\n❌ Error loading person {person['person_id']}: {e}")
    # Continues to next person, no retry
```

**Technical Specifications (Section 3.4):**
- Error code 503: Service Unavailable - Wait and retry
- Implement exponential backoff

**Impact:**
- Transient network errors cause data loss
- No way to resume failed loads
- Poor reliability

**Correction Required:**
```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, backoff_factor=2):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except GremlinServerError as e:
                    if attempt == max_retries - 1:
                        raise
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
        return wrapper
    return decorator

@retry_on_failure(max_retries=3)
def load_person(self, person):
    # Load logic here
    pass
```

---

### 6. No Batch Processing Optimization (🟠 HIGH)

**Issue:** Loading one vertex at a time (inefficient)

**Current (load_structuring_data.py):**
```python
for person in tqdm(persons, desc="Persons"):
    query = "g.addV('person')..."
    self.gc.submit(query, bindings).all().result()
    # One network round-trip per person
```

**Technical Specifications (Section 5.2.3):**
- Use batch operations for bulk inserts
- Batch size: 1000 vertices

**Impact:**
- Slow loading (1000+ network round-trips)
- Cannot meet performance targets
- Inefficient resource usage

**Correction Required:**
```python
def load_persons_batch(self, persons, batch_size=1000):
    """Load persons in batches for better performance"""
    for i in range(0, len(persons), batch_size):
        batch = persons[i:i+batch_size]
        
        # Build batch query
        query = "g"
        for j, person in enumerate(batch):
            query += f"""
            .addV('person')
                .property('personId', person{j}_id)
                .property('firstName', person{j}_first)
                .property('lastName', person{j}_last)
                .property('riskScore', person{j}_risk)
            """
        
        # Create bindings for entire batch
        bindings = {}
        for j, person in enumerate(batch):
            bindings[f'person{j}_id'] = person['person_id']
            bindings[f'person{j}_first'] = person['first_name']
            bindings[f'person{j}_last'] = person['last_name']
            bindings[f'person{j}_risk'] = person['risk_score']
        
        # Execute batch
        self.gc.submit(query, bindings).all().result()
```

---

### 7. Hardcoded File Paths (🟠 HIGH)

**Issue:** File paths hardcoded, not configurable

**Current (generate_structuring_data.py line 466):**
```python
generator.export_to_json('banking/data/aml/aml_structuring_data.json')
generator.export_to_csv('banking/data/aml/aml_data')
```

**Technical Specifications (Section 9.1):**
- Support multiple environments (dev/staging/prod)
- Use environment variables for paths

**Impact:**
- Cannot run from different directories
- Breaks in containerized environment
- No environment separation

**Correction Required:**
```python
import os
from pathlib import Path

# Use environment variables with defaults
DATA_DIR = Path(os.getenv('DATA_DIR', 'banking/data/aml'))
OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'aml_structuring_data.json')

# Ensure directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Export with configurable paths
generator.export_to_json(DATA_DIR / OUTPUT_FILE)
generator.export_to_csv(DATA_DIR / 'aml_data')
```

---

### 8. No Logging Infrastructure (🟠 HIGH)

**Issue:** Using print() instead of proper logging

**Current:**
```python
print("🔧 Generating AML synthetic data...")
print(f"  Creating {self.num_beneficiaries} beneficiaries...")
```

**Technical Specifications (Section 8.2):**
- Use structured logging (JSON format)
- Log levels: ERROR, WARN, INFO, DEBUG
- Include timestamps, service name

**Impact:**
- Cannot integrate with monitoring
- No log aggregation
- Difficult to debug production issues

**Correction Required:**
```python
import logging
import json
from datetime import datetime

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

class StructuredLogger:
    """Structured JSON logger"""
    
    @staticmethod
    def log(level, message, **kwargs):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'service': 'data-generator',
            'message': message,
            **kwargs
        }
        print(json.dumps(log_entry))

# Usage
StructuredLogger.log('INFO', 'Generating AML data', 
                     num_beneficiaries=2, 
                     num_mule_accounts=10)
```

---

## Corrected Scripts

### Corrected: generate_structuring_data.py

**Key Changes:**
1. Add environment validation
2. Update schema to match technical specifications
3. Add structured logging
4. Make paths configurable
5. Add proper error handling

**Implementation:** See `banking/data/aml/generate_structuring_data_v2.py` (to be created)

---

### Corrected: load_structuring_data.py

**Key Changes:**
1. Fix port configuration (8182 not 18182)
2. Add container awareness
3. Implement batch loading
4. Add retry logic
5. Add structured logging

**Implementation:** See `banking/data/aml/load_structuring_data_v3.py` (to be created)

---

### Corrected: load_production_data.py

**Key Changes:**
1. Fix JanusGraph port
2. Add environment validation
3. Add container support
4. Improve error handling

**Implementation:** Update in place

---

### Corrected: load_data.py

**Key Changes:**
1. Fix port configuration
2. Add environment variables
3. Update to match schema
4. Add proper logging

**Implementation:** Update in place

---

## Validation Requirements

### Unit Tests Required
```python
# tests/unit/test_data_generators.py
def test_person_schema_matches_spec():
    """Verify generated person matches technical spec"""
    generator = AMLDataGenerator()
    person = generator.create_person()
    
    # Required fields from spec
    assert 'personId' in person
    assert 'firstName' in person
    assert 'lastName' in person
    assert 'riskScore' in person
    assert isinstance(person['riskScore'], int)
    assert 0 <= person['riskScore'] <= 100
    assert person['riskLevel'] in ['low', 'medium', 'high', 'critical']
```

### Integration Tests Required
```python
# tests/integration/test_data_loading.py
def test_load_to_janusgraph():
    """Verify data loads correctly into JanusGraph"""
    # Generate test data
    generator = AMLDataGenerator(num_normal_customers=10)
    data = generator.generate_all_data()
    
    # Load into JanusGraph
    loader = AMLDataLoader()
    loader.connect()
    loader.load_all(data)
    
    # Verify
    person_count = loader.gc.submit("g.V().hasLabel('person').count()").all().result()[0]
    assert person_count == 10
```

---

## Remediation Roadmap

### Phase 1: Critical Fixes (Week 1)
- [ ] Fix port configuration (8182)
- [ ] Add environment validation
- [ ] Update schema to match specs
- [ ] Add container awareness

### Phase 2: Performance (Week 2)
- [ ] Implement batch loading
- [ ] Add retry logic
- [ ] Optimize queries

### Phase 3: Observability (Week 3)
- [ ] Add structured logging
- [ ] Add metrics collection
- [ ] Add error tracking

### Phase 4: Testing (Week 4)
- [ ] Unit tests for generators
- [ ] Integration tests for loaders
- [ ] Schema validation tests
- [ ] Performance benchmarks

---

## Configuration Template

### Environment Variables Required

```bash
# .env.data-scripts
# JanusGraph Configuration
JANUSGRAPH_HOST=localhost
JANUSGRAPH_PORT=8182
JANUSGRAPH_SSL=false
JANUSGRAPH_USERNAME=admin
JANUSGRAPH_PASSWORD=${JANUSGRAPH_PASSWORD}

# Data Paths
DATA_DIR=banking/data/aml
OUTPUT_FILE=aml_structuring_data.json

# Python Environment
CONDA_ENV=janusgraph-analysis
PYTHON_VERSION=3.11

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Performance
BATCH_SIZE=1000
MAX_RETRIES=3
RETRY_BACKOFF=2
```

---

## Documentation Updates Required

### Technical Specifications (Section 2.2)
- Add data generation schema examples
- Document property naming conventions
- Add validation rules

### Remediation Plan (Phase 4-6)
- Add data script corrections
- Document environment variables
- Add testing requirements

### README Files
- `banking/data/aml/README.md` - Usage instructions
- `scripts/deployment/README.md` - Deployment procedures

---

## Conclusion

The data generation and loading scripts have **8 critical issues** that prevent them from working with the containerized architecture defined in the technical specifications. The most critical issues are:

1. **Wrong port (18182 vs 8182)** - Scripts will fail immediately
2. **Schema misalignment** - Data won't load correctly
3. **No container awareness** - Can't work with pods
4. **No environment validation** - Silent failures possible

**Recommendation:** Do NOT use these scripts until corrected. They will fail in the current deployment architecture.

**Timeline:** 4 weeks to fully correct and test all scripts.

---

**Status:** Audit complete, corrections required before use  
**Priority:** CRITICAL - Scripts are currently broken  
**Next Steps:** Implement Phase 1 corrections immediately
