# Week 6: Post-Production Enhancement Plan

**Date:** 2026-02-11
**Status:** Planning
**Duration:** 33 hours (5 days)
**Objective:** Address enhancement areas identified in comprehensive codebase reviews

---

## Executive Summary

Week 6 focuses on **optional enhancements** to improve the already production-ready system from **A (95/100) to A+ (100/100)**. All tasks are non-blocking and can be executed post-deployment.

### Enhancement Categories

1. **Immediate Cleanup** (15 minutes) - Housekeeping
2. **Code Quality** (3 hours) - Technical debt reduction
3. **Testing** (16 hours) - Coverage expansion
4. **Security** (8 hours) - MFA implementation
5. **Performance** (6 hours) - Optimization

**Total Time:** 33 hours (5 working days)

---

## Day 28: Immediate Cleanup & Code Quality

**Duration:** 3.25 hours
**Objective:** Quick wins and code quality improvements

### Task 1: Immediate Cleanup ✅

**Priority:** 🟢 Low (Housekeeping)
**Time:** 15 minutes
**Impact:** Repository cleanliness

#### Subtask 1.1: Remove htmlcov/ from Git (5 min)

**Current State:**
```bash
# 298+ HTML files in htmlcov/ tracked by git
htmlcov/
├── index.html
├── status.json
├── *.html (coverage reports)
└── ...
```

**Actions:**
```bash
# 1. Remove from git tracking
git rm -r --cached htmlcov/

# 2. Update .gitignore
cat >> .gitignore << 'EOF'

# Coverage reports
htmlcov/
.coverage
.coverage.*
coverage.xml
*.cover
.pytest_cache/
EOF

# 3. Commit changes
git add .gitignore
git commit -m "chore: remove htmlcov/ from git tracking"
```

**Acceptance Criteria:**
- [ ] htmlcov/ removed from git tracking
- [ ] .gitignore updated with Python coverage patterns
- [ ] `git status` shows clean working directory
- [ ] Coverage reports still generated locally

#### Subtask 1.2: Organize Scan/Report Files (10 min)

**Current State:**
```
project_root/
├── security_scan_bandit.json
├── production_readiness_validation.json
├── docs_issues_analysis.json
├── docs_validation_report.txt
└── ...
```

**Actions:**
```bash
# 1. Create reports directory structure
mkdir -p reports/{security,validation,documentation}

# 2. Move scan files
mv security_scan_bandit.json reports/security/
mv security_scan_*.json reports/security/
mv production_readiness_validation.json reports/validation/
mv docs_*.{json,txt} reports/documentation/

# 3. Update .gitignore
cat >> .gitignore << 'EOF'

# Reports (keep structure, ignore content)
reports/**/*.json
reports/**/*.txt
reports/**/*.html
!reports/.gitkeep
EOF

# 4. Create .gitkeep files
touch reports/{security,validation,documentation}/.gitkeep

# 5. Update documentation references
grep -r "security_scan_bandit.json" docs/ | \
  xargs sed -i '' 's|security_scan_bandit.json|reports/security/security_scan_bandit.json|g'
```

**Acceptance Criteria:**
- [ ] reports/ directory structure created
- [ ] All scan/report files moved from root
- [ ] Documentation references updated
- [ ] .gitignore configured to ignore report content
- [ ] .gitkeep files preserve directory structure

**Deliverables:**
- Clean project root
- Organized reports/ directory
- Updated .gitignore
- Updated documentation references

---

### Task 2: Code Quality Improvements ✅

**Priority:** 🟡 Medium
**Time:** 3 hours
**Impact:** Maintainability, consistency

#### Subtask 2.1: Unify Config Access (1 hour)

**Issue:** `JanusGraphClient.__init__` uses `os.getenv()` directly instead of centralized `Settings`

**Current Code (src/python/client/janusgraph_client.py:55):**
```python
def __init__(self, host: str = "localhost", port: int = 8182):
    self.host = host
    self.port = int(os.getenv("JANUSGRAPH_PORT", port))  # ❌ Direct env access
```

**Target Code:**
```python
from src.python.config.settings import get_settings

def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
    settings = get_settings()
    self.host = host or settings.janusgraph_host
    self.port = port or settings.janusgraph_port
```

**Implementation Steps:**

1. **Update Settings class** (15 min)
   ```python
   # src/python/config/settings.py
   class Settings(BaseSettings):
       # Add if not present
       janusgraph_host: str = Field(default="localhost", env="JANUSGRAPH_HOST")
       janusgraph_port: int = Field(default=8182, env="JANUSGRAPH_PORT")
       janusgraph_use_ssl: bool = Field(default=False, env="JANUSGRAPH_USE_SSL")
   ```

2. **Refactor JanusGraphClient** (30 min)
   ```python
   # src/python/client/janusgraph_client.py
   from src.python.config.settings import get_settings
   
   class JanusGraphClient:
       def __init__(
           self,
           host: Optional[str] = None,
           port: Optional[int] = None,
           use_ssl: Optional[bool] = None
       ):
           settings = get_settings()
           self.host = host or settings.janusgraph_host
           self.port = port or settings.janusgraph_port
           self.use_ssl = use_ssl if use_ssl is not None else settings.janusgraph_use_ssl
   ```

3. **Update Tests** (15 min)
   ```python
   # tests/unit/client/test_janusgraph_client_unit.py
   def test_client_uses_settings(mock_settings):
       mock_settings.janusgraph_host = "test-host"
       mock_settings.janusgraph_port = 9999
       
       client = JanusGraphClient()
       assert client.host == "test-host"
       assert client.port == 9999
   ```

**Acceptance Criteria:**
- [ ] Settings class has janusgraph_* fields
- [ ] JanusGraphClient uses get_settings()
- [ ] No direct os.getenv() calls in client
- [ ] All existing tests pass
- [ ] New tests validate settings integration

#### Subtask 2.2: Deprecate Validation Aliases (1 hour)

**Issue:** 23 module-level backward-compat aliases in `src/python/utils/validation.py` (lines 860-883)

**Current Code:**
```python
# Backward compatibility aliases (lines 860-883)
validate_account_number = Validator.validate_account_number
validate_amount = Validator.validate_amount
validate_email = Validator.validate_email
# ... 20 more aliases
```

**Implementation Steps:**

1. **Add Deprecation Warnings** (30 min)
   ```python
   # src/python/utils/validation.py
   import warnings
   from functools import wraps
   
   def _deprecated_alias(func_name: str):
       """Decorator for deprecated module-level aliases."""
       def decorator(func):
           @wraps(func)
           def wrapper(*args, **kwargs):
               warnings.warn(
                   f"{func_name}() is deprecated. "
                   f"Use Validator.{func_name}() instead. "
                   f"This alias will be removed in version 3.0.0",
                   DeprecationWarning,
                   stacklevel=2
               )
               return func(*args, **kwargs)
           return wrapper
       return decorator
   
   # Apply to all aliases
   validate_account_number = _deprecated_alias("validate_account_number")(
       Validator.validate_account_number
   )
   ```

2. **Create Migration Guide** (20 min)
   ```markdown
   # docs/migration/validation-api-v3.md
   
   ## Validation API Migration Guide
   
   ### Deprecated: Module-level functions
   ```python
   # ❌ Deprecated (will be removed in v3.0.0)
   from src.python.utils.validation import validate_email
   validate_email("test@example.com")
   ```
   
   ### Recommended: Validator class methods
   ```python
   # ✅ Recommended
   from src.python.utils.validation import Validator
   Validator.validate_email("test@example.com")
   ```
   ```

3. **Update Documentation** (10 min)
   - Add deprecation notice to CHANGELOG.md
   - Update API documentation
   - Add migration guide link to README.md

**Acceptance Criteria:**
- [ ] All 23 aliases have deprecation warnings
- [ ] Migration guide created
- [ ] CHANGELOG.md updated
- [ ] Tests verify warnings are raised
- [ ] Documentation updated

#### Subtask 2.3: Remove Code Duplication (1 hour)

**Issue:** `_flatten_value_map` exists as both module-level function AND static method

**Current Code:**
```python
# Module-level function
def _flatten_value_map(value_map: Dict) -> Dict:
    """Flatten Gremlin valueMap results."""
    # Implementation...

# GraphRepository static method
class GraphRepository:
    @staticmethod
    def flatten_value_map(value_map: Dict) -> Dict:
        """Flatten Gremlin valueMap results."""
        # Same implementation...
```

**Implementation Steps:**

1. **Consolidate to Utility Module** (30 min)
   ```python
   # src/python/utils/gremlin_utils.py (new file)
   from typing import Dict, Any, List
   
   def flatten_value_map(value_map: Dict[str, List[Any]]) -> Dict[str, Any]:
       """Flatten Gremlin valueMap results.
       
       Gremlin returns properties as {key: [value]} format.
       This flattens to {key: value} for easier consumption.
       
       Args:
           value_map: Gremlin valueMap result
           
       Returns:
           Flattened dictionary
           
       Example:
           >>> flatten_value_map({"name": ["John"], "age": [30]})
           {"name": "John", "age": 30}
       """
       return {
           key: value[0] if isinstance(value, list) and value else value
           for key, value in value_map.items()
       }
   ```

2. **Update GraphRepository** (15 min)
   ```python
   # src/python/repository/graph_repository.py
   from src.python.utils.gremlin_utils import flatten_value_map
   
   class GraphRepository:
       # Remove static method, use imported function
       def get_vertex_by_id(self, vertex_id: str) -> Optional[Dict]:
           result = self.g.V(vertex_id).valueMap(True).next()
           return flatten_value_map(result) if result else None
   ```

3. **Add Comprehensive Tests** (15 min)
   ```python
   # tests/unit/utils/test_gremlin_utils.py
   import pytest
   from src.python.utils.gremlin_utils import flatten_value_map
   
   def test_flatten_value_map_basic():
       input_map = {"name": ["John"], "age": [30]}
       result = flatten_value_map(input_map)
       assert result == {"name": "John", "age": 30}
   
   def test_flatten_value_map_empty_list():
       input_map = {"name": [], "age": [30]}
       result = flatten_value_map(input_map)
       assert result == {"name": [], "age": 30}
   
   def test_flatten_value_map_non_list():
       input_map = {"name": "John", "age": 30}
       result = flatten_value_map(input_map)
       assert result == {"name": "John", "age": 30}
   ```

**Acceptance Criteria:**
- [ ] New gremlin_utils.py module created
- [ ] Single flatten_value_map implementation
- [ ] GraphRepository uses utility function
- [ ] Module-level function removed
- [ ] 100% test coverage for utility
- [ ] All existing tests pass

**Deliverables:**
- Unified config access pattern
- Deprecated validation aliases with migration guide
- Consolidated gremlin utilities
- Updated tests and documentation

---

## Day 29-30: Testing Infrastructure Enhancement

**Duration:** 16 hours (2 days)
**Objective:** Expand test coverage from 35% to ≥85%

### Task 3: Test Coverage Expansion ✅

**Priority:** 🟡 Medium
**Time:** 8 hours
**Impact:** Quality assurance, confidence

#### Coverage Analysis

**Current Coverage (35%):**
```
Module                          Coverage    Gap to 85%
──────────────────────────────────────────────────────
python.config                   98%         ✅ Excellent
python.client                   97%         ✅ Excellent
python.utils                    88%         ✅ Good
python.api                      75%         +10% needed
data_generators.utils           76%         +9% needed
streaming                       28%         +57% needed
aml                             25%         +60% needed
compliance                      25%         +60% needed
fraud                           23%         +62% needed
data_generators.patterns        13%         +72% needed
analytics                        0%         +85% needed
```

#### Subtask 3.1: Analytics Module Tests (2 hours)

**Target:** 0% → 85% coverage

**Files to Test:**
- `banking/analytics/ubo_discovery.py`
- `banking/analytics/graph_analytics.py`

**Test Plan:**
```python
# tests/unit/analytics/test_ubo_discovery.py
import pytest
from banking.analytics.ubo_discovery import UBODiscovery

class TestUBODiscovery:
    def test_find_ultimate_beneficial_owners(self, mock_graph):
        """Test UBO discovery algorithm."""
        ubo = UBODiscovery(mock_graph)
        result = ubo.find_ubos("company-123")
        assert len(result) > 0
        assert all("ownership_percentage" in r for r in result)
    
    def test_ownership_threshold(self, mock_graph):
        """Test ownership threshold filtering."""
        ubo = UBODiscovery(mock_graph, threshold=0.25)
        result = ubo.find_ubos("company-123")
        assert all(r["ownership_percentage"] >= 0.25 for r in result)
    
    def test_circular_ownership_detection(self, mock_graph):
        """Test handling of circular ownership structures."""
        # Setup circular ownership
        # Test detection and handling
    
    def test_multi_level_ownership(self, mock_graph):
        """Test ownership calculation through multiple levels."""
        # Test 3+ level ownership chains
```

**Acceptance Criteria:**
- [ ] ≥85% coverage for analytics module
- [ ] All edge cases tested
- [ ] Mock fixtures for graph data
- [ ] Performance tests for large graphs

#### Subtask 3.2: Streaming Module Tests (2 hours)

**Target:** 28% → 85% coverage

**Focus Areas:**
- Event producers (EntityProducer)
- Event consumers (GraphConsumer, VectorConsumer)
- DLQ handling
- Metrics collection

**Test Plan:**
```python
# tests/unit/streaming/test_producer_enhanced.py
import pytest
from banking.streaming.producer import EntityProducer
from banking.streaming.events import create_person_event

class TestEntityProducer:
    def test_send_event_success(self, mock_pulsar):
        """Test successful event publishing."""
        producer = EntityProducer(pulsar_url="mock://localhost")
        event = create_person_event("p-123", "John Doe", {})
        result = producer.send(event)
        assert result.success is True
    
    def test_send_event_retry_on_failure(self, mock_pulsar):
        """Test retry logic on transient failures."""
        # Mock transient failure then success
        # Verify retry behavior
    
    def test_batch_send_optimization(self, mock_pulsar):
        """Test batch sending for performance."""
        # Test batch vs individual sends
```

**Acceptance Criteria:**
- [ ] ≥85% coverage for streaming module
- [ ] Producer tests with mocks
- [ ] Consumer tests with test containers
- [ ] DLQ handling verified
- [ ] Metrics collection tested

#### Subtask 3.3: AML/Fraud/Compliance Tests (2 hours)

**Target:** 23-25% → 85% coverage

**Test Plan:**
```python
# tests/unit/aml/test_structuring_detection.py
import pytest
from banking.aml.structuring import StructuringDetector

class TestStructuringDetector:
    def test_detect_structuring_pattern(self):
        """Test detection of structuring (smurfing) pattern."""
        detector = StructuringDetector()
        transactions = [
            {"amount": 9000, "timestamp": "2026-01-01T10:00:00"},
            {"amount": 9500, "timestamp": "2026-01-01T11:00:00"},
            {"amount": 9800, "timestamp": "2026-01-01T12:00:00"},
        ]
        result = detector.detect(transactions)
        assert result.is_suspicious is True
        assert result.confidence > 0.8
    
    def test_false_positive_handling(self):
        """Test legitimate transaction patterns."""
        # Test normal business transactions
        # Verify no false positives
```

**Acceptance Criteria:**
- [ ] ≥85% coverage for aml, fraud, compliance
- [ ] Pattern detection tests
- [ ] False positive/negative tests
- [ ] Edge case handling

#### Subtask 3.4: Data Generator Pattern Tests (2 hours)

**Target:** 13% → 85% coverage

**Test Plan:**
```python
# tests/unit/data_generators/patterns/test_fraud_patterns.py
import pytest
from banking.data_generators.patterns.fraud import FraudPatternInjector

class TestFraudPatternInjector:
    def test_inject_card_fraud_pattern(self, sample_data):
        """Test card fraud pattern injection."""
        injector = FraudPatternInjector(seed=42)
        result = injector.inject_card_fraud(sample_data)
        assert result.pattern_count > 0
        assert all(t["is_fraudulent"] for t in result.flagged_transactions)
    
    def test_pattern_distribution(self, sample_data):
        """Test pattern distribution matches specification."""
        # Verify pattern frequency
        # Check randomization
```

**Acceptance Criteria:**
- [ ] ≥85% coverage for pattern generators
- [ ] All pattern types tested
- [ ] Seed reproducibility verified
- [ ] Distribution validation

**Deliverables:**
- 500+ new unit tests
- Coverage reports showing ≥85%
- Mock fixtures and test utilities
- Updated test documentation

---

### Task 4: Lightweight Integration Tests ✅

**Priority:** 🟡 Medium
**Time:** 8 hours
**Impact:** Faster feedback, easier testing

#### Current State

**Problem:** Integration tests require full stack deployment (90+ seconds startup)

```bash
# Current integration test setup
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
sleep 90  # Wait for all services
pytest tests/integration/ -v
```

#### Target State

**Solution:** Lightweight integration tests using testcontainers

```python
# tests/integration_lite/test_janusgraph_connectivity.py
import pytest
from testcontainers.compose import DockerCompose

@pytest.fixture(scope="module")
def janusgraph_container():
    """Lightweight JanusGraph container for testing."""
    with DockerCompose(
        "tests/integration_lite",
        compose_file_name="docker-compose.lite.yml",
        pull=True
    ) as compose:
        compose.wait_for("http://localhost:8182/health")
        yield compose

def test_janusgraph_connection(janusgraph_container):
    """Test basic JanusGraph connectivity."""
    client = JanusGraphClient()
    result = client.execute("g.V().count()")
    assert result >= 0
```

#### Implementation Steps

1. **Create Lite Compose File** (1 hour)
   ```yaml
   # tests/integration_lite/docker-compose.lite.yml
   version: '3.8'
   services:
     janusgraph-lite:
       image: janusgraph/janusgraph:latest
       ports:
         - "8182:8182"
       environment:
         - JANUS_PROPS_TEMPLATE=inmemory
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8182/health"]
         interval: 10s
         timeout: 5s
         retries: 3
   ```

2. **Install Testcontainers** (15 min)
   ```bash
   uv pip install testcontainers pytest-testcontainers
   ```

3. **Create Lite Test Suite** (4 hours)
   ```python
   # tests/integration_lite/test_graph_operations.py
   import pytest
   from testcontainers.compose import DockerCompose
   
   @pytest.fixture(scope="module")
   def lite_stack():
       with DockerCompose("tests/integration_lite") as compose:
           compose.wait_for("janusgraph-lite", 8182)
           yield compose
   
   def test_vertex_creation(lite_stack):
       """Test vertex creation and retrieval."""
       # Test basic CRUD operations
   
   def test_edge_creation(lite_stack):
       """Test edge creation and traversal."""
       # Test relationship operations
   
   def test_query_performance(lite_stack):
       """Test query performance benchmarks."""
       # Test query latency
   ```

4. **Add CI Integration** (1 hour)
   ```yaml
   # .github/workflows/integration-lite.yml
   name: Lightweight Integration Tests
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Run lite integration tests
           run: |
             pytest tests/integration_lite/ -v --tb=short
   ```

5. **Documentation** (1 hour)
   ```markdown
   # docs/testing/lightweight-integration-tests.md
   
   ## Lightweight Integration Tests
   
   Fast integration tests using testcontainers (30-60 seconds vs 90+ seconds).
   
   ### Running Tests
   ```bash
   # Run lite integration tests
   pytest tests/integration_lite/ -v
   
   # Run full integration tests
   pytest tests/integration/ -v
   ```
   ```

6. **Update Test Markers** (1 hour)
   ```python
   # tests/conftest.py
   def pytest_configure(config):
       config.addinivalue_line(
           "markers",
           "integration_lite: lightweight integration tests (testcontainers)"
       )
   ```

**Acceptance Criteria:**
- [ ] Lite compose file with minimal services
- [ ] Testcontainers integration working
- [ ] 20+ lite integration tests
- [ ] Startup time <60 seconds
- [ ] CI workflow configured
- [ ] Documentation complete

**Deliverables:**
- docker-compose.lite.yml
- 20+ lightweight integration tests
- CI workflow for lite tests
- Testing documentation

---

## Day 31: Security Hardening

**Duration:** 8 hours
**Objective:** Complete MFA implementation

### Task 5: Multi-Factor Authentication ✅

**Priority:** 🟡 Medium
**Time:** 8 hours
**Impact:** Security 92% → 100%

#### Current State

**Existing:** Basic API key authentication
**Missing:** Multi-factor authentication (TOTP)

#### Implementation Steps

#### Subtask 5.1: TOTP Backend (3 hours)

1. **Install Dependencies** (15 min)
   ```bash
   uv pip install pyotp qrcode[pil]
   ```

2. **Create MFA Module** (2 hours)
   ```python
   # src/python/security/mfa.py
   import pyotp
   import qrcode
   from typing import Tuple, Optional
   from datetime import datetime, timedelta
   
   class MFAManager:
       """Multi-Factor Authentication manager using TOTP."""
       
       def generate_secret(self) -> str:
           """Generate new TOTP secret."""
           return pyotp.random_base32()
       
       def generate_qr_code(
           self,
           secret: str,
           user_email: str,
           issuer: str = "JanusGraph Banking"
       ) -> bytes:
           """Generate QR code for TOTP setup."""
           totp = pyotp.TOTP(secret)
           uri = totp.provisioning_uri(
               name=user_email,
               issuer_name=issuer
           )
           qr = qrcode.QRCode(version=1, box_size=10, border=5)
           qr.add_data(uri)
           qr.make(fit=True)
           img = qr.make_image(fill_color="black", back_color="white")
           # Convert to bytes
           return img.tobytes()
       
       def verify_token(
           self,
           secret: str,
           token: str,
           window: int = 1
       ) -> bool:
           """Verify TOTP token."""
           totp = pyotp.TOTP(secret)
           return totp.verify(token, valid_window=window)
       
       def generate_backup_codes(self, count: int = 10) -> List[str]:
           """Generate backup codes for account recovery."""
           return [pyotp.random_base32()[:8] for _ in range(count)]
   ```

3. **Add Database Schema** (45 min)
   ```python
   # src/python/models/user_mfa.py
   from pydantic import BaseModel, Field
   from typing import List, Optional
   from datetime import datetime
   
   class UserMFA(BaseModel):
       """User MFA configuration."""
       user_id: str
       mfa_enabled: bool = False
       totp_secret: Optional[str] = None
       backup_codes: List[str] = Field(default_factory=list)
       last_used: Optional[datetime] = None
       created_at: datetime = Field(default_factory=datetime.utcnow)
   ```

#### Subtask 5.2: API Endpoints (2 hours)

```python
# src/python/api/routers/mfa.py
from fastapi import APIRouter, Depends, HTTPException, status
from src.python.security.mfa import MFAManager
from src.python.api.dependencies import get_current_user

router = APIRouter(prefix="/mfa", tags=["mfa"])
mfa_manager = MFAManager()

@router.post("/setup")
async def setup_mfa(user = Depends(get_current_user)):
    """Initialize MFA setup for user."""
    secret = mfa_manager.generate_secret()
    qr_code = mfa_manager.generate_qr_code(secret, user.email)
    backup_codes = mfa_manager.generate_backup_codes()
    
    # Store secret and backup codes (encrypted)
    # Return QR code and backup codes
    
    return {
        "qr_code": qr_code,
        "backup_codes": backup_codes,
        "secret": secret  # For manual entry
    }

@router.post("/verify")
async def verify_mfa_setup(
    token: str,
    secret: str,
    user = Depends(get_current_user)
):
    """Verify MFA setup with first token."""
    if not mfa_manager.verify_token(secret, token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    # Enable MFA for user
    # Store encrypted secret
    
    return {"message": "MFA enabled successfully"}

@router.post("/authenticate")
async def authenticate_with_mfa(
    token: str,
    user = Depends(get_current_user)
):
    """Authenticate using MFA token."""
    if not user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not enabled for this user"
        )
    
    if not mfa_manager.verify_token(user.totp_secret, token):
        # Check backup codes
        if token not in user.backup_codes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA token"
            )
        # Remove used backup code
    
    return {"message": "MFA authentication successful"}

@router.post("/disable")
async def disable_mfa(
    token: str,
    user = Depends(get_current_user)
):
    """Disable MFA for user."""
    if not mfa_manager.verify_token(user.totp_secret, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA token"
        )
    
    # Disable MFA
    # Clear secret and backup codes
    
    return {"message": "MFA disabled successfully"}
```

#### Subtask 5.3: Middleware Integration (1 hour)

```python
# src/python/api/middleware/mfa_middleware.py
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

class MFAMiddleware(BaseHTTPMiddleware):
    """Enforce MFA for sensitive operations."""
    
    SENSITIVE_PATHS = [
        "/api/v1/admin",
        "/api/v1/compliance/reports",
        "/api/v1/users/delete"
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Check if path requires MFA
        if any(request.url.path.startswith(p) for p in self.SENSITIVE_PATHS):
            # Verify MFA token in header
            mfa_token = request.headers.get("X-MFA-Token")
            if not mfa_token:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="MFA required for this operation"
                )
            
            # Verify token
            # ...
        
        response = await call_next(request)
        return response
```

#### Subtask 5.4: Testing (1 hour)

```python
# tests/unit/security/test_mfa.py
import pytest
from src.python.security.mfa import MFAManager

class TestMFAManager:
    def test_generate_secret(self):
        """Test TOTP secret generation."""
        manager = MFAManager()
        secret = manager.generate_secret()
        assert len(secret) == 32
        assert secret.isalnum()
    
    def test_verify_token_valid(self):
        """Test valid token verification."""
        manager = MFAManager()
        secret = manager.generate_secret()
        # Generate current token
        import pyotp
        totp = pyotp.TOTP(secret)
        token = totp.now()
        
        assert manager.verify_token(secret, token) is True
    
    def test_verify_token_invalid(self):
        """Test invalid token rejection."""
        manager = MFAManager()
        secret = manager.generate_secret()
        
        assert manager.verify_token(secret, "000000") is False
    
    def test_backup_codes_generation(self):
        """Test backup code generation."""
        manager = MFAManager()
        codes = manager.generate_backup_codes(10)
        assert len(codes) == 10
        assert len(set(codes)) == 10  # All unique
```

#### Subtask 5.5: Documentation (1 hour)

```markdown
# docs/security/mfa-setup-guide.md

## Multi-Factor Authentication Setup

### User Enrollment

1. **Enable MFA**
   ```bash
   POST /api/v1/mfa/setup
   Authorization: Bearer <token>
   ```

2. **Scan QR Code**
   - Use authenticator app (Google Authenticator, Authy, etc.)
   - Scan QR code from response

3. **Verify Setup**
   ```bash
   POST /api/v1/mfa/verify
   {
     "token": "123456",
     "secret": "<secret>"
   }
   ```

4. **Save Backup Codes**
   - Store backup codes securely
   - Use for account recovery

### Authentication

```bash
POST /api/v1/mfa/authenticate
Authorization: Bearer <token>
{
  "token": "123456"
}
```

### Sensitive Operations

Operations requiring MFA:
- Admin panel access
- Compliance report generation
- User deletion
- Credential rotation

Include MFA token in header:
```bash
X-MFA-Token: 123456
```
```

**Acceptance Criteria:**
- [ ] TOTP generation and verification working
- [ ] QR code generation functional
- [ ] Backup codes generated and validated
- [ ] API endpoints implemented
- [ ] Middleware enforces MFA for sensitive ops
- [ ] 100% test coverage for MFA module
- [ ] Documentation complete
- [ ] Audit logging for MFA events

**Deliverables:**
- Complete MFA implementation
- API endpoints for enrollment/verification
- Middleware for enforcement
- Comprehensive tests
- User documentation

---

## Day 32: Performance Optimization

**Duration:** 6 hours
**Objective:** Achieve 18-30% cumulative performance improvement

### Task 6: Performance Optimizations ✅

**Priority:** 🟢 Low (Optional)
**Time:** 6 hours
**Impact:** 18-30% performance improvement

#### Subtask 6.1: Faker Instance Caching (2 hours)

**Current Issue:** Faker initialization is expensive, repeated for each test

**Measurement:**
```python
# Current: ~500ms for 1000 person generation
import time
from banking.data_generators.core import PersonGenerator

start = time.time()
generator = PersonGenerator(seed=42)
persons = [generator.generate() for _ in range(1000)]
elapsed = time.time() - start
print(f"Time: {elapsed:.2f}s")  # ~500ms
```

**Implementation:**

1. **Create Faker Cache** (1 hour)
   ```python
   # banking/data_generators/utils/faker_cache.py
   from functools import lru_cache
   from faker import Faker
   from typing import Optional
   
   @lru_cache(maxsize=10)
   def get_faker_instance(locale: str = "en_US", seed: Optional[int] = None) -> Faker:
       """Get cached Faker instance.
       
       Args:
           locale: Faker locale
           seed: Random seed for reproducibility
           
       Returns:
           Cached Faker instance
       """
       fake = Faker(locale)
       if seed is not None:
           Faker.seed(seed)
       return fake
   ```

2. **Update Generators** (30 min)
   ```python
   # banking/data_generators/core/person_generator.py
   from banking.data_generators.utils.faker_cache import get_faker_instance
   
   class PersonGenerator(BaseGenerator[Person]):
       def __init__(self, seed: Optional[int] = None):
           super().__init__(seed)
           self.fake = get_faker_instance(seed=seed)  # Use cached instance
   ```

3. **Benchmark Improvement** (30 min)
   ```python
   # tests/benchmarks/test_faker_caching.py
   import pytest
   from banking.data_generators.core import PersonGenerator
   
   def test_faker_caching_performance(benchmark):
       """Benchmark Faker caching improvement."""
       def generate_persons():
           generator = PersonGenerator(seed=42)
           return [generator.generate() for _ in range(1000)]
       
       result = benchmark(generate_persons)
       # Target: <425ms (15% improvement from 500ms)
       assert result.stats.mean < 0.425
   ```

**Expected Improvement:** 10-15% (500ms → 425-450ms)

**Acceptance Criteria:**
- [ ] Faker instance caching implemented
- [ ] All generators use cached instances
- [ ] Benchmark shows ≥10% improvement
- [ ] Seed reproducibility maintained

#### Subtask 6.2: Batch Size Tuning (2 hours)

**Current Issue:** Suboptimal batch sizes for JanusGraph operations

**Implementation:**

1. **Profile Current Performance** (30 min)
   ```python
   # scripts/performance/profile_batch_sizes.py
   import time
   from src.python.client.janusgraph_client import JanusGraphClient
   
   def test_batch_size(batch_size: int, total: int = 10000):
       """Test batch insert performance."""
       client = JanusGraphClient()
       batches = total // batch_size
       
       start = time.time()
       for i in range(batches):
           # Insert batch
           vertices = [{"id": f"v-{j}", "name": f"Name {j}"} 
                      for j in range(i * batch_size, (i + 1) * batch_size)]
           client.batch_insert_vertices(vertices)
       elapsed = time.time() - start
       
       return elapsed, total / elapsed  # throughput
   
   # Test different batch sizes
   for size in [10, 50, 100, 200, 500, 1000]:
       elapsed, throughput = test_batch_size(size)
       print(f"Batch {size}: {elapsed:.2f}s, {throughput:.0f} vertices/s")
   ```

2. **Implement Optimal Batch Size** (1 hour)
   ```python
   # src/python/client/janusgraph_client.py
   class JanusGraphClient:
       # Optimal batch size from profiling
       DEFAULT_BATCH_SIZE = 200  # Adjust based on profiling
       
       def batch_insert_vertices(
           self,
           vertices: List[Dict],
           batch_size: Optional[int] = None
       ):
           """Insert vertices in optimized batches."""
           batch_size = batch_size or self.DEFAULT_BATCH_SIZE
           
           for i in range(0, len(vertices), batch_size):
               batch = vertices[i:i + batch_size]
               # Insert batch with optimized size
   ```

3. **Benchmark Improvement** (30 min)
   ```python
   # tests/benchmarks/test_batch_operations.py
   def test_optimized_batch_size(benchmark):
       """Benchmark optimized batch operations."""
       def batch_insert():
           client = JanusGraphClient()
           vertices = [{"id": f"v-{i}"} for i in range(1000)]
           client.batch_insert_vertices(vertices)
       
       result = benchmark(batch_insert)
       # Target: 5-10% improvement
   ```

**Expected Improvement:** 5-10%

**Acceptance Criteria:**
- [ ] Batch size profiling complete
- [ ] Optimal batch size determined
- [ ] Client uses optimized batch size
- [ ] Benchmark shows ≥5% improvement

#### Subtask 6.3: Lazy Validation (2 hours)

**Current Issue:** Validation performed even when not needed

**Implementation:**

1. **Identify Validation Hotspots** (30 min)
   ```python
   # Use cProfile to identify expensive validations
   import cProfile
   import pstats
   
   profiler = cProfile.Profile()
   profiler.enable()
   
   # Run typical workload
   generator = PersonGenerator(seed=42)
   persons = [generator.generate() for _ in range(1000)]
   
   profiler.disable()
   stats = pstats.Stats(profiler)
   stats.sort_stats('cumulative')
   stats.print_stats(20)
   ```

2. **Implement Lazy Validation** (1 hour)
   ```python
   # src/python/utils/validation.py
   class Validator:
       @staticmethod
       def validate_email(
           email: str,
           strict: bool = True,
           lazy: bool = False
       ) -> bool:
           """Validate email address.
           
           Args:
               email: Email to validate
               strict: Perform strict validation
               lazy: Skip validation if not critical
               
           Returns:
               True if valid
           """
           if lazy and not strict:
               # Quick check only
               return "@" in email and "." in email
           
           # Full validation
           return email_regex.match(email) is not None
   ```

3. **Update Generators** (30 min)
   ```python
   # banking/data_generators/core/person_generator.py
   class PersonGenerator:
       def generate(self, validate: bool = False) -> Person:
           """Generate person with optional validation.
           
           Args:
               validate: Perform validation (default: False for performance)
           """
           person = {
               "id": self.fake.uuid4(),
               "name": self.fake.name(),
               "email": self.fake.email()
           }
           
           if validate:
               # Perform validation
               Validator.validate_email(person["email"])
           
           return person
   ```

**Expected Improvement:** 3-5%

**Acceptance Criteria:**
- [ ] Validation hotspots identified
- [ ] Lazy validation implemented
- [ ] Generators use lazy validation
- [ ] Benchmark shows ≥3% improvement
- [ ] Strict validation still available

**Cumulative Performance Improvement:**
- Faker caching: 10-15%
- Batch size tuning: 5-10%
- Lazy validation: 3-5%
- **Total: 18-30% improvement**

**Deliverables:**
- Faker instance caching
- Optimized batch sizes
- Lazy validation pattern
- Performance benchmarks
- Profiling reports

---

## Summary & Deliverables

### Time Allocation

| Day | Tasks | Hours | Cumulative |
|-----|-------|-------|------------|
| 28 | Cleanup + Code Quality | 3.25 | 3.25 |
| 29-30 | Testing Enhancement | 16 | 19.25 |
| 31 | Security (MFA) | 8 | 27.25 |
| 32 | Performance | 6 | 33.25 |
| **Total** | **5 Categories** | **33.25** | **33.25** |

### Expected Outcomes

**Grade Progression:**
```
Current:  A  (95/100) ███████████████████
Target:   A+ (100/100) ████████████████████
```

**Category Improvements:**
- Code Quality: 94/100 → 98/100 (+4)
- Testing: 85/100 → 95/100 (+10)
- Security: 92/100 → 100/100 (+8)
- Performance: 100/100 → 100/100 (optimized)
- Documentation: 95/100 → 98/100 (+3)

### Acceptance Criteria

**Immediate Cleanup:**
- [ ] htmlcov/ removed from git
- [ ] reports/ directory organized
- [ ] .gitignore updated
- [ ] Documentation references updated

**Code Quality:**
- [ ] Config access unified
- [ ] Validation aliases deprecated
- [ ] Code duplication removed
- [ ] All tests passing

**Testing:**
- [ ] Coverage ≥85% overall
- [ ] 500+ new unit tests
- [ ] Lightweight integration tests
- [ ] Mutation testing configured

**Security:**
- [ ] MFA fully implemented
- [ ] API endpoints functional
- [ ] Middleware enforcing MFA
- [ ] Documentation complete

**Performance:**
- [ ] 18-30% cumulative improvement
- [ ] Benchmarks validate gains
- [ ] No regression in functionality

### Final Deliverables

1. **Code Changes**
   - 3 refactored modules
   - 500+ new tests
   - MFA implementation
   - Performance optimizations

2. **Documentation**
   - Migration guides
   - MFA setup guide
   - Performance reports
   - Updated architecture docs

3. **Reports**
   - Coverage reports (≥85%)
   - Performance benchmarks
   - Mutation testing results
   - Security audit results

4. **Infrastructure**
   - Lightweight test environment
   - CI/CD updates
   - Monitoring enhancements

---

**Plan Created:** 2026-02-11
**Target Completion:** Week 6 (5 days, 33 hours)
**Expected Grade:** A+ (100/100)
**Status:** Ready for execution