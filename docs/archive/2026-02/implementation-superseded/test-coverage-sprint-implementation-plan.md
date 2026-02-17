# Test Coverage Sprint Implementation Plan

**Date:** 2026-02-11  
**Duration:** 2 weeks  
**Goal:** Increase test coverage from 35% to 60%+ overall  
**Status:** Ready for execution

---

## Sprint Overview

### Objectives

| Module | Current Coverage | Target Coverage | Priority | Effort |
|--------|------------------|-----------------|----------|--------|
| **Analytics** | 0% | 60% | P0 | 3 days |
| **Fraud** | 23% | 60% | P0 | 2 days |
| **AML** | 25% | 60% | P0 | 2 days |
| **Streaming** | 28% | 60% | P1 | 3 days (Week 2) |

### Week 1: Domain Module Testing (Days 1-5)

**Days 1-3:** Analytics Module (0% → 60%)  
**Days 4-5:** Fraud + AML Modules (23%/25% → 60%)

### Week 2: Infrastructure & Validation (Days 6-10)

**Days 6-7:** Resolve TODOs + MFA  
**Day 8:** DR Drill  
**Days 9-10:** Final Validation

---

## Week 1, Day 1-3: Analytics Module Tests

### Target: `src/python/analytics/ubo_discovery.py`

**Current State:**
- 602 lines of code
- 0% test coverage
- Complex UBO discovery logic
- Regulatory compliance requirements

**Test Strategy:**
- Unit tests for each method
- Integration tests for graph traversals
- Property-based tests for ownership calculations
- Mock JanusGraph connections for unit tests

### Test Files to Create

#### 1. `tests/unit/analytics/__init__.py`

```python
"""Unit tests for analytics module"""
```

#### 2. `tests/unit/analytics/test_ubo_discovery.py`

**Test Coverage Plan (60%+ target):**

```python
"""
Unit tests for UBO Discovery module

Test Coverage Target: 60%+
Total Tests: 25+
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal

from src.python.analytics.ubo_discovery import (
    UBODiscovery,
    OwnershipType,
    OwnershipLink,
    UBOResult,
    discover_ubos
)


class TestOwnershipType:
    """Test OwnershipType enum (5 tests)"""
    
    def test_ownership_type_values(self):
        """Test all ownership type values exist"""
        assert OwnershipType.DIRECT == "direct"
        assert OwnershipType.INDIRECT == "indirect"
        assert OwnershipType.NOMINEE == "nominee"
        assert OwnershipType.TRUST == "trust"
        assert OwnershipType.BEARER == "bearer"
    
    def test_ownership_type_is_string_enum(self):
        """Test OwnershipType inherits from str"""
        assert isinstance(OwnershipType.DIRECT, str)
    
    def test_ownership_type_comparison(self):
        """Test ownership type string comparison"""
        assert OwnershipType.DIRECT == "direct"
        assert OwnershipType.DIRECT != "indirect"
    
    def test_ownership_type_iteration(self):
        """Test can iterate over ownership types"""
        types = list(OwnershipType)
        assert len(types) == 5
    
    def test_ownership_type_membership(self):
        """Test membership checking"""
        assert "direct" in [t.value for t in OwnershipType]


class TestOwnershipLink:
    """Test OwnershipLink dataclass (5 tests)"""
    
    def test_ownership_link_creation(self):
        """Test creating ownership link with required fields"""
        link = OwnershipLink(
            entity_id="p-123",
            entity_type="person",
            entity_name="John Doe",
            ownership_percentage=30.0,
            ownership_type=OwnershipType.DIRECT
        )
        assert link.entity_id == "p-123"
        assert link.ownership_percentage == 30.0
    
    def test_ownership_link_optional_fields(self):
        """Test optional fields have defaults"""
        link = OwnershipLink(
            entity_id="p-123",
            entity_type="person",
            entity_name="John Doe",
            ownership_percentage=30.0,
            ownership_type=OwnershipType.DIRECT
        )
        assert link.jurisdiction is None
        assert link.is_pep is False
        assert link.is_sanctioned is False
    
    def test_ownership_link_with_all_fields(self):
        """Test creating link with all fields"""
        link = OwnershipLink(
            entity_id="p-123",
            entity_type="person",
            entity_name="John Doe",
            ownership_percentage=30.0,
            ownership_type=OwnershipType.DIRECT,
            jurisdiction="US",
            is_pep=True,
            is_sanctioned=False
        )
        assert link.jurisdiction == "US"
        assert link.is_pep is True
    
    def test_ownership_link_high_risk_indicators(self):
        """Test high-risk ownership link"""
        link = OwnershipLink(
            entity_id="p-456",
            entity_type="person",
            entity_name="Sanctioned Person",
            ownership_percentage=50.0,
            ownership_type=OwnershipType.BEARER,
            jurisdiction="VG",
            is_sanctioned=True
        )
        assert link.is_sanctioned is True
        assert link.ownership_type == OwnershipType.BEARER
    
    def test_ownership_link_dataclass_equality(self):
        """Test dataclass equality"""
        link1 = OwnershipLink("p-1", "person", "John", 30.0, OwnershipType.DIRECT)
        link2 = OwnershipLink("p-1", "person", "John", 30.0, OwnershipType.DIRECT)
        assert link1 == link2


class TestUBOResult:
    """Test UBOResult dataclass (3 tests)"""
    
    def test_ubo_result_creation(self):
        """Test creating UBO result"""
        result = UBOResult(
            target_entity_id="c-123",
            target_entity_name="ACME Corp",
            ubos=[],
            ownership_chains=[],
            total_layers=0,
            high_risk_indicators=[],
            risk_score=0.0
        )
        assert result.target_entity_id == "c-123"
        assert result.risk_score == 0.0
    
    def test_ubo_result_with_ubos(self):
        """Test UBO result with discovered UBOs"""
        ubos = [
            {"person_id": "p-1", "name": "John Doe", "ownership": 30.0},
            {"person_id": "p-2", "name": "Jane Smith", "ownership": 40.0}
        ]
        result = UBOResult(
            target_entity_id="c-123",
            target_entity_name="ACME Corp",
            ubos=ubos,
            ownership_chains=[],
            total_layers=2,
            high_risk_indicators=["offshore_jurisdiction"],
            risk_score=0.6
        )
        assert len(result.ubos) == 2
        assert result.total_layers == 2
    
    def test_ubo_result_high_risk(self):
        """Test high-risk UBO result"""
        result = UBOResult(
            target_entity_id="c-456",
            target_entity_name="Shell Corp",
            ubos=[],
            ownership_chains=[],
            total_layers=5,
            high_risk_indicators=["bearer_shares", "sanctioned_owner", "tax_haven"],
            risk_score=0.9
        )
        assert result.risk_score > 0.8
        assert len(result.high_risk_indicators) == 3


class TestUBODiscoveryInit:
    """Test UBODiscovery initialization (4 tests)"""
    
    def test_init_default_parameters(self):
        """Test initialization with default parameters"""
        ubo = UBODiscovery()
        assert ubo.host == "localhost"
        assert ubo.port == 18182
        assert ubo.ownership_threshold == 25.0
    
    def test_init_custom_parameters(self):
        """Test initialization with custom parameters"""
        ubo = UBODiscovery(host="remote-host", port=8182, ownership_threshold=10.0)
        assert ubo.host == "remote-host"
        assert ubo.port == 8182
        assert ubo.ownership_threshold == 10.0
    
    def test_init_regulatory_thresholds(self):
        """Test regulatory threshold constants"""
        assert UBODiscovery.DEFAULT_OWNERSHIP_THRESHOLD == 25.0
        assert UBODiscovery.MAX_TRAVERSAL_DEPTH == 10
    
    def test_init_high_risk_jurisdictions(self):
        """Test high-risk jurisdiction list"""
        assert "VG" in UBODiscovery.HIGH_RISK_JURISDICTIONS  # British Virgin Islands
        assert "KY" in UBODiscovery.HIGH_RISK_JURISDICTIONS  # Cayman Islands
        assert "US" not in UBODiscovery.HIGH_RISK_JURISDICTIONS


class TestUBODiscoveryConnection:
    """Test connection management (3 tests)"""
    
    @patch('src.python.analytics.ubo_discovery.DriverRemoteConnection')
    @patch('src.python.analytics.ubo_discovery.traversal')
    def test_connect_success(self, mock_traversal, mock_connection):
        """Test successful connection"""
        ubo = UBODiscovery()
        result = ubo.connect()
        assert result is True
        mock_connection.assert_called_once()
    
    @patch('src.python.analytics.ubo_discovery.DriverRemoteConnection')
    def test_connect_failure(self, mock_connection):
        """Test connection failure handling"""
        mock_connection.side_effect = Exception("Connection failed")
        ubo = UBODiscovery()
        result = ubo.connect()
        assert result is False
    
    def test_close_connection(self):
        """Test closing connection"""
        ubo = UBODiscovery()
        ubo.connection = Mock()
        ubo.close()
        ubo.connection.close.assert_called_once()


class TestUBODiscoveryHelperMethods:
    """Test helper methods (5 tests)"""
    
    def test_flatten_value_map_simple(self):
        """Test flattening simple value map"""
        ubo = UBODiscovery()
        value_map = {"name": ["John Doe"], "age": [30]}
        result = ubo._flatten_value_map(value_map)
        assert result == {"name": "John Doe", "age": 30}
    
    def test_flatten_value_map_empty(self):
        """Test flattening empty value map"""
        ubo = UBODiscovery()
        result = ubo._flatten_value_map({})
        assert result == {}
    
    def test_calculate_effective_ownership_direct(self):
        """Test calculating direct ownership"""
        ubo = UBODiscovery()
        chain = [
            OwnershipLink("p-1", "person", "John", 50.0, OwnershipType.DIRECT)
        ]
        result = ubo._calculate_effective_ownership(chain)
        assert result == 50.0
    
    def test_calculate_effective_ownership_chain(self):
        """Test calculating ownership through chain"""
        ubo = UBODiscovery()
        chain = [
            OwnershipLink("c-1", "company", "HoldCo", 60.0, OwnershipType.DIRECT),
            OwnershipLink("p-1", "person", "John", 50.0, OwnershipType.INDIRECT)
        ]
        result = ubo._calculate_effective_ownership(chain)
        assert result == 30.0  # 60% * 50%
    
    def test_calculate_risk_score(self):
        """Test risk score calculation"""
        ubo = UBODiscovery()
        indicators = ["bearer_shares", "tax_haven", "sanctioned_owner"]
        score = ubo._calculate_risk_score(indicators, layers=5, has_pep=True)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be high risk


# Add 5 more test classes for remaining methods...
# Total: 25+ tests covering 60%+ of the module
```

### Execution Steps

1. **Create test directory structure:**
```bash
mkdir -p tests/unit/analytics
touch tests/unit/analytics/__init__.py
```

2. **Create test file:**
```bash
# Copy the test template above to:
tests/unit/analytics/test_ubo_discovery.py
```

3. **Run tests:**
```bash
conda activate janusgraph-analysis
pytest tests/unit/analytics/test_ubo_discovery.py -v --cov=src/python/analytics
```

4. **Verify coverage:**
```bash
pytest tests/unit/analytics/ -v --cov=src/python/analytics --cov-report=term-missing
```

**Success Criteria:**
- ✅ 25+ tests passing
- ✅ 60%+ coverage for `src/python/analytics/ubo_discovery.py`
- ✅ All critical methods tested
- ✅ No test failures

---

## Week 1, Day 4-5: Fraud & AML Module Tests

### Fraud Detection Module

**Target:** `banking/fraud/` (currently 23% coverage)

**Gap Analysis:**
- Need tests for edge cases
- Need property-based tests
- Need integration tests

**Test Files to Enhance:**
1. `banking/fraud/tests/test_fraud_detector.py` - Add 10+ tests
2. `banking/fraud/tests/test_integration_fraud.py` - Add 5+ tests

**New Tests Needed:**
```python
# Add to existing test files:

class TestFraudDetectorEdgeCases:
    """Test edge cases (10 tests)"""
    
    def test_fraud_detection_zero_amount(self):
        """Test handling zero transaction amount"""
        pass
    
    def test_fraud_detection_negative_amount(self):
        """Test handling negative amount"""
        pass
    
    def test_fraud_detection_very_large_amount(self):
        """Test handling very large amounts"""
        pass
    
    # ... 7 more edge case tests
```

### AML Detection Module

**Target:** `banking/aml/` (currently 25% coverage)

**Gap Analysis:**
- Need tests for structuring detection
- Need tests for SAR generation
- Need integration tests

**Test Files to Enhance:**
1. `banking/aml/tests/test_aml_detector.py` - Add 10+ tests
2. `banking/aml/tests/test_structuring.py` - Add 5+ tests

---

## Week 2, Day 6-7: Resolve TODOs & MFA

### TODO Resolution

**Location:** `scripts/` directory

**TODOs to Resolve:**

1. **TODO 1: Credential Rotation Framework**
   - File: `scripts/security/rotate_credentials.sh`
   - Action: Implement automated credential rotation
   - Effort: 4 hours

2. **TODO 2: Connection Manager Refactor**
   - File: `scripts/deployment/connection_manager.py`
   - Action: Refactor to use connection pooling
   - Effort: 3 hours

3. **TODO 3: Backup Encryption**
   - File: `scripts/backup/backup_janusgraph.sh`
   - Action: Add encryption to backup process
   - Effort: 2 hours

### MFA Implementation

**Target:** Complete MFA framework

**Files to Modify:**
1. `src/python/utils/auth.py` - Add MFA verification
2. `src/python/api/routers/auth.py` - Add MFA endpoints
3. `tests/unit/test_auth.py` - Add MFA tests

**Implementation Steps:**

```python
# src/python/utils/auth.py

import pyotp
import qrcode
from io import BytesIO

class MFAManager:
    """Multi-Factor Authentication Manager"""
    
    def generate_secret(self, user_id: str) -> str:
        """Generate TOTP secret for user"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_id: str, secret: str) -> bytes:
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_id,
            issuer_name="JanusGraph Banking"
        )
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    
    def verify_token(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
```

---

## Week 2, Day 8: DR Drill

### Disaster Recovery Drill Plan

**Objective:** Validate disaster recovery procedures

**Scenario:** Complete data center failure

**Steps:**

1. **Backup Verification (30 min)**
```bash
# Verify backups exist
ls -lh /backups/janusgraph/
ls -lh /backups/hcd/

# Test backup integrity
./scripts/backup/verify_backup.sh
```

2. **Simulated Failure (15 min)**
```bash
# Stop all services
cd config/compose
podman-compose -p janusgraph-demo -f docker-compose.full.yml down

# Remove data volumes (CAUTION: Test environment only!)
podman volume rm janusgraph-demo_hcd-data
podman volume rm janusgraph-demo_janusgraph-data
```

3. **Recovery Execution (60 min)**
```bash
# Restore from backup
./scripts/backup/restore_janusgraph.sh /backups/janusgraph/latest.tar.gz
./scripts/backup/restore_hcd.sh /backups/hcd/latest.tar.gz

# Restart services
cd config/compose
podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d

# Wait for services
sleep 90
```

4. **Validation (30 min)**
```bash
# Verify data integrity
python scripts/validation/verify_data_integrity.py

# Run smoke tests
pytest tests/integration/test_smoke.py -v

# Verify monitoring
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3001/api/health  # Grafana
```

5. **Documentation (30 min)**
- Document recovery time (RTO)
- Document data loss (RPO)
- Update DR procedures based on findings

**Success Criteria:**
- ✅ RTO < 2 hours
- ✅ RPO < 1 hour
- ✅ All services restored
- ✅ Data integrity verified
- ✅ Monitoring operational

---

## Week 2, Day 9-10: Final Validation

### Validation Checklist

#### 1. Test Coverage Validation

```bash
# Run full test suite
pytest -v --cov=src --cov=banking --cov-report=html --cov-report=term

# Verify coverage targets
# - Analytics: ≥60%
# - Fraud: ≥60%
# - AML: ≥60%
# - Overall: ≥60%
```

#### 2. Code Quality Validation

```bash
# Run all quality checks
pre-commit run --all-files

# Type checking
mypy src/ banking/

# Linting
ruff check src/ banking/

# Security scan
bandit -r src/ banking/ -ll
```

#### 3. Integration Testing

```bash
# Deploy full stack
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh

# Run integration tests
pytest tests/integration/ -v

# Run E2E tests
pytest tests/integration/test_e2e_*.py -v
```

#### 4. Performance Validation

```bash
# Run performance benchmarks
pytest tests/benchmarks/ -v

# Verify performance targets:
# - Bulk insert: >10 v/s
# - Query latency: <100ms
# - Traversal: <200ms
```

#### 5. Security Validation

```bash
# Verify MFA implementation
pytest tests/unit/test_auth.py -v -k mfa

# Verify startup validation
python -c "from src.python.utils.startup_validation import validate_environment; validate_environment()"

# Verify no default passwords
grep -r "changeit" config/ || echo "No default passwords found"
```

#### 6. Documentation Validation

```bash
# Validate documentation links
./scripts/validation/validate-doc-links.sh

# Verify kebab-case compliance
./scripts/validation/validate-kebab-case.sh

# Check for broken links
find docs -name "*.md" -exec markdown-link-check {} \;
```

---

## Success Metrics

### Coverage Targets

| Module | Before | Target | Status |
|--------|--------|--------|--------|
| Analytics | 0% | 60% | ⏳ Pending |
| Fraud | 23% | 60% | ⏳ Pending |
| AML | 25% | 60% | ⏳ Pending |
| Streaming | 28% | 60% | ⏳ P1 (Week 2) |
| **Overall** | **35%** | **60%** | ⏳ **Pending** |

### Quality Gates

- ✅ All tests passing (100% pass rate)
- ✅ No critical security issues (bandit)
- ✅ No type errors (mypy)
- ✅ No linting errors (ruff)
- ✅ All pre-commit hooks passing
- ✅ DR drill successful (RTO < 2h)
- ✅ MFA implementation complete
- ✅ All TODOs resolved

---

## Risk Mitigation

### Potential Risks

1. **Test Complexity**
   - Risk: UBO discovery tests may be complex
   - Mitigation: Use mocks for graph connections, focus on logic

2. **Integration Test Failures**
   - Risk: Services may not be available
   - Mitigation: Use pytest.skip() when services unavailable

3. **Time Overruns**
   - Risk: Tasks may take longer than estimated
   - Mitigation: Prioritize P0 items, defer P1 to Week 3

4. **DR Drill Issues**
   - Risk: Recovery may fail
   - Mitigation: Test in isolated environment first

---

## Execution Tracking

### Daily Standup Template

**What was completed yesterday:**
- [ ] List completed tasks

**What will be done today:**
- [ ] List planned tasks

**Blockers:**
- [ ] List any blockers

### Progress Tracking

Create `docs/implementation/sprint-progress.md`:

```markdown
# Sprint Progress Tracker

## Week 1

### Day 1 (2026-02-12)
- [ ] Analytics tests: OwnershipType (5 tests)
- [ ] Analytics tests: OwnershipLink (5 tests)
- [ ] Analytics tests: UBOResult (3 tests)

### Day 2 (2026-02-13)
- [ ] Analytics tests: UBODiscovery init (4 tests)
- [ ] Analytics tests: Connection management (3 tests)
- [ ] Analytics tests: Helper methods (5 tests)

### Day 3 (2026-02-14)
- [ ] Analytics tests: Remaining methods (10+ tests)
- [ ] Verify 60%+ coverage
- [ ] Fix any failing tests

### Day 4 (2026-02-15)
- [ ] Fraud tests: Edge cases (10 tests)
- [ ] Fraud tests: Integration (5 tests)
- [ ] Verify 60%+ coverage

### Day 5 (2026-02-16)
- [ ] AML tests: Structuring (10 tests)
- [ ] AML tests: SAR generation (5 tests)
- [ ] Verify 60%+ coverage

## Week 2

### Day 6 (2026-02-17)
- [ ] Resolve TODO 1: Credential rotation
- [ ] Resolve TODO 2: Connection manager
- [ ] Resolve TODO 3: Backup encryption

### Day 7 (2026-02-18)
- [ ] MFA implementation
- [ ] MFA tests
- [ ] MFA documentation

### Day 8 (2026-02-19)
- [ ] DR drill execution
- [ ] DR drill documentation
- [ ] Update DR procedures

### Day 9 (2026-02-20)
- [ ] Full test suite validation
- [ ] Code quality validation
- [ ] Integration testing

### Day 10 (2026-02-21)
- [ ] Performance validation
- [ ] Security validation
- [ ] Documentation validation
- [ ] Sprint retrospective
```

---

## Completion Criteria

### Sprint Complete When:

1. ✅ **Test Coverage ≥60%**
   - Analytics: ≥60%
   - Fraud: ≥60%
   - AML: ≥60%

2. ✅ **All Quality Gates Pass**
   - 100% test pass rate
   - No critical issues
   - All pre-commit hooks pass

3. ✅ **Infrastructure Complete**
   - 3 TODOs resolved
   - MFA implemented
   - DR drill successful

4. ✅ **Documentation Updated**
   - Test documentation complete
   - DR procedures updated
   - Sprint retrospective documented

---

## Next Steps After Sprint

### Week 3: Production Deployment Preparation

1. External security audit
2. Stakeholder review
3. Production deployment planning
4. Post-deployment monitoring setup

---

**Plan Created:** 2026-02-11  
**Sprint Start:** 2026-02-12  
**Sprint End:** 2026-02-21  
**Status:** Ready for execution