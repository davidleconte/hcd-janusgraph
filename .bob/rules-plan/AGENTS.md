# Project Architecture Rules (Non-Obvious Only)

## Generator Architecture Constraints

**All generators must be stateless** - orchestrator assumes no state between calls:
```python
# WRONG - state between calls breaks orchestrator
class PersonGenerator(BaseGenerator):
    def __init__(self, seed):
        super().__init__(seed)
        self.generated_count = 0  # State - breaks orchestrator assumptions

# CORRECT - stateless
class PersonGenerator(BaseGenerator):
    def generate(self) -> Person:
        return Person(...)  # No state
```

**Pattern generators require complete entity context** - hidden coupling:
```python
# Pattern generators have hidden dependencies on ALL entity types
# Missing any entity type causes silent failures
pattern_gen.inject_pattern(
    persons=persons,      # Required - pattern needs person context
    companies=companies,  # Required - pattern needs company context
    accounts=accounts,    # Required - pattern needs account relationships
    trades=trades,        # Required - pattern needs trade history
    communications=communications  # Required - pattern needs communication graph
)
```

## Docker Compose Architecture

**Compose files use relative context paths** - counterintuitive:
```yaml
# In config/compose/docker-compose.yml
build:
  context: .  # This is config/compose/, NOT project root!
  dockerfile: ../../docker/hcd/Dockerfile  # Navigate up to find docker/
```

**Services must start in specific order** - hidden dependencies:
```yaml
# HCD must be healthy before JanusGraph starts
janusgraph:
  depends_on:
    hcd:
      condition: service_healthy  # Critical - not just service_started
```

## Testing Architecture

**Test fixtures modify sys.path** - affects import resolution:
```python
# conftest.py line 18 - modifies path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
# This means imports work differently in tests vs production
```

**Integration tests use runtime skip** - not compile-time:
```python
# Tests check service availability at runtime, not via skipif
@pytest.mark.integration
def test_janusgraph(self):
    pytest.skip("Requires running JanusGraph")  # Runtime decision
```

## Deployment Architecture

**Deploy script must run from config/compose/** - path-dependent:
```bash
# Script assumes it's run from config/compose/ directory
# Makefile handles this, but manual execution requires CD
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
```

## Security Architecture

**JMX ports intentionally not exposed** - security by design:
```yaml
# Management ports commented out - not an oversight
# - "7199:7199"  # JMX - Use SSH tunnel instead
# This is intentional security architecture
```

## Module Coupling

**banking.data_generators has circular dependency on utils** - intentional:
```python
# All generators depend on utils.data_models
# utils.data_models is shared across all generators
# This circular dependency is by design for type consistency
```

**Orchestrator coordinates but doesn't own generators** - loose coupling:
```python
# MasterOrchestrator creates generator instances
# But generators are independent and can be used standalone
# This allows flexible composition
```

## Performance Architecture

**Generators use Faker with seed** - performance implication:
```python
# Faker initialization with seed is expensive
# Reuse generator instances, don't create new ones per call
generator = PersonGenerator(seed=42)
persons = [generator.generate() for _ in range(1000)]  # Efficient

# NOT
persons = [PersonGenerator(seed=42).generate() for _ in range(1000)]  # Slow
```

## Data Flow Architecture

**Pattern injection modifies entities in-place** - side effects:
```python
# Pattern generators modify the entity lists passed to them
# This is intentional for memory efficiency
# But means you can't reuse entity lists after pattern injection
pattern_gen.inject_pattern(persons=persons, ...)  # persons is modified!
```

## Type System Architecture

**Type hints are mandatory** - enforced by mypy:
```python
# mypy config: disallow_untyped_defs = true
# All functions must have type hints
# This is stricter than typical Python projects
def generate() -> Person:  # Type hint required
    return Person()