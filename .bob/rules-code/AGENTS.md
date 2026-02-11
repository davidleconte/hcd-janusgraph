# Project Coding Rules (Non-Obvious Only)

## Generator Pattern Requirements

**All generators MUST inherit from BaseGenerator** - provides seed management and Faker initialization:

```python
class CustomGenerator(BaseGenerator):
    def __init__(self, seed: Optional[int] = None):
        super().__init__(seed)  # Critical - initializes Faker with seed
```

**Pattern generators require complete entity context** - partial lists will cause silent failures:

```python
# WRONG - will fail silently
pattern_gen.inject_pattern(persons=persons, accounts=accounts)

# CORRECT - all entity types required
pattern_gen.inject_pattern(
    persons=persons,
    companies=companies,
    accounts=accounts,
    trades=trades,
    communications=communications
)
```

## Import Path Gotchas

**Test files modify sys.path** - conftest.py line 18 adds parent to path, don't duplicate:

```python
# Already done in conftest.py, don't add again:
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

**Banking generators use specific import structure**:

```python
# Core generators
from banking.data_generators.core import PersonGenerator, CompanyGenerator

# Orchestration
from banking.data_generators.orchestration import MasterOrchestrator, GenerationConfig

# NOT from banking.data_generators.core.person_generator import PersonGenerator
```

## Docker Context Paths

**Dockerfile paths in compose files are relative to compose file location** - not project root:

```yaml
# In config/compose/docker-compose.yml:
build:
  context: .  # This is config/compose/, NOT project root
  dockerfile: ../../docker/hcd/Dockerfile  # Must navigate up
```

## Deployment Commands

**Deploy script must run from config/compose directory** - Makefile handles this:

```bash
# WRONG - will fail
bash scripts/deployment/deploy_full_stack.sh

# CORRECT - via Makefile
make deploy

# OR manually
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
```

## Testing Requirements

**Single test execution requires tests directory** - pytest path resolution:

```bash
# WRONG - will fail with import errors
pytest banking/data_generators/tests/test_core/test_person_generator.py

# CORRECT - run from tests directory
cd banking/data_generators/tests
pytest test_core/test_person_generator.py::TestClass::test_method -v
```

**Integration tests use pytest.skip() not skipif** - check service availability at runtime:

```python
@pytest.mark.integration
def test_janusgraph_connection(self):
    pytest.skip("Requires running JanusGraph instance")  # Runtime skip
    # NOT @pytest.mark.skipif
```

## Code Style Enforcement

**Line length is 100, not 88** - configured in pyproject.toml:

```python
# pyproject.toml
[tool.black]
line-length = 100  # Non-standard, not 88
```

**Type hints are mandatory** - mypy enforces this:

```python
# WRONG - will fail mypy
def generate():
    return Person()

# CORRECT
def generate() -> Person:
    return Person()
```

## Security Patterns

**JMX ports must not be exposed** - use SSH tunnel instead:

```yaml
# docker-compose.yml - ports commented for security
# - "7199:7199"  # JMX - Use SSH tunnel: ssh -L 7199:localhost:7199 user@host
```

No access to MCP tools or Browser in code mode.

## Documentation Naming Standards

**All documentation files MUST use kebab-case naming** - enforced by validation script and CI/CD:

```bash
# ✅ CORRECT - Use kebab-case (lowercase with hyphens)
docs/new-feature-guide.md
docs/api-reference-v2.md
docs/user-authentication-guide.md
docs/phase-8-complete.md

# ❌ WRONG - Do not use UPPERCASE, PascalCase, or snake_case
docs/New_Feature_Guide.md      # UPPERCASE with underscores
docs/API_REFERENCE_V2.md        # All UPPERCASE
docs/ApiReferenceV2.md          # PascalCase
docs/user_guide.md              # snake_case
docs/UserGuide.md               # PascalCase
```

**Approved exceptions (UPPERCASE allowed):**
- README.md, CONTRIBUTING.md, CHANGELOG.md, LICENSE
- CODE_OF_CONDUCT.md, SECURITY.md, AGENTS.md
- QUICKSTART.md, FAQ.md

**Validation:**
- Pre-commit hook: `.pre-commit-config.yaml`
- CI/CD workflow: `.github/workflows/validate-doc-naming.yml`
- Manual check: `bash scripts/validation/validate-kebab-case.sh`
