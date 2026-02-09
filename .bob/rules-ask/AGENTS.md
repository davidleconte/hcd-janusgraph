# Project Documentation Rules (Non-Obvious Only)

## Directory Structure Gotchas

**config/compose/ contains docker-compose files** - not in project root:

```
config/
├── compose/              # Docker compose files HERE
│   ├── docker-compose.yml
│   └── docker-compose.banking.yml
├── janusgraph/          # JanusGraph configs
└── monitoring/          # Prometheus/Grafana configs
```

**banking/ contains both AML modules AND data generators** - two separate systems:

```
banking/
├── aml/                 # AML detection modules (sanctions, structuring, fraud)
├── data_generators/     # Synthetic data generation framework
├── notebooks/           # Jupyter notebooks for demos
└── docs/                # Banking-specific documentation
```

## Documentation Location Patterns

**API documentation in docs/banking/** - not docs/api/:

```
docs/
├── banking/             # Banking use case docs HERE
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md
│   └── USER_GUIDE.md
├── api/                 # General API docs (Gremlin, OpenAPI)
└── architecture/        # ADRs and architecture decisions
```

**Test documentation in test directories** - not centralized:

```
banking/data_generators/tests/
├── README.md            # Test documentation HERE
├── conftest.py
└── run_tests.sh
```

## Deployment Command Context

**Deploy commands must run from specific directories** - not project root:

```bash
# Deploy requires config/compose/ directory
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh

# NOT from project root
```

## Testing Context

**Data generator tests run from tests directory** - pytest path resolution:

```bash
# Must CD into tests directory first
cd banking/data_generators/tests
./run_tests.sh smoke

# NOT from project root
```

## Module Organization

**banking.data_generators has 4 sub-packages** - specific import structure:

```python
banking.data_generators/
├── core/          # PersonGenerator, CompanyGenerator, AccountGenerator
├── events/        # TransactionGenerator, CommunicationGenerator, etc.
├── patterns/      # Pattern generators (InsiderTrading, TBML, etc.)
├── orchestration/ # MasterOrchestrator, GenerationConfig
└── utils/         # Helpers, constants, data models
```

## Configuration Files

**pyproject.toml excludes notebooks and hcd-1.2.3** - not obvious from structure:

```toml
extend-exclude = '''
/(
  | notebooks
  | hcd-1.2.3
)/
'''
```

**Line length is 100** - non-standard for Black (usually 88):

```toml
[tool.black]
line-length = 100  # Not 88!
```

## Security Documentation

**JMX ports intentionally not exposed** - documented in docker-compose.yml comments:

```yaml
# SECURITY: JMX and management ports not exposed publicly
# Access via SSH tunnel: ssh -L 7199:localhost:7199 user@host
# - "7199:7199"  # JMX - Use SSH tunnel
```

## Phase Documentation

**Phase 8 documentation in docs/banking/** - comprehensive implementation guides:

```
docs/banking/
├── PHASE8_COMPLETE.md              # Final handoff
├── PHASE8_IMPLEMENTATION_GUIDE.md  # Implementation guide
├── PHASE8D_WEEK7_COMPLETE.md       # Testing framework
└── PHASE8D_WEEK8_PLAN.md           # Documentation plan
```

## Test Markers

**Pytest markers defined in conftest.py** - not pytest.ini:

```python
# conftest.py defines custom markers
@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.benchmark
