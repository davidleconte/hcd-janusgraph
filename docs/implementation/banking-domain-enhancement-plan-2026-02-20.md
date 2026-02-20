# Banking Domain Enhancement Implementation Plan

**Date:** 2026-02-20  
**Version:** 1.0  
**Status:** Active  
**Source:** [Banking Domain Audit 2026-02-20](audits/banking-domain-audit-2026-02-20.md)

## Executive Summary

This document provides a detailed implementation plan for Priority 1 (P1) and Priority 2 (P2) enhancements identified in the banking domain audit. The plan addresses documentation gaps, banking domain skills creation, test coverage improvements, and API documentation.

**Total Estimated Effort:** 73 hours (P1: 25 hours, P2: 48 hours)  
**Timeline:** 2-4 weeks  
**Team Size:** 2-3 developers

---

## Priority 1 (Immediate, 1-2 weeks) - 25 hours

### ✅ COMPLETED: Documentation Enhancements (5 hours)

**Status:** COMPLETE (2026-02-20)

1. ✅ **Compliance Module README** (2 hours) - DONE
   - Created 485-line comprehensive README
   - Documented 30+ audit event types
   - Added GDPR, SOC 2, BSA/AML, PCI DSS examples
   - Included API reference and troubleshooting

2. ✅ **Analytics Module README** (3 hours) - DONE
   - Expanded from 44 to 585 lines (13x increase)
   - Documented all 3 detectors (Insider Trading, TBML, AML)
   - Added performance benchmarks and algorithms
   - Included advanced usage and configuration

**Deliverables:** 
- `banking/compliance/README.md` (485 lines)
- `banking/analytics/README.md` (585 lines)

**Git Commits:**
- `8198238` - "docs: Add comprehensive READMEs for Compliance and Analytics modules"

---

### 🔄 IN PROGRESS: Banking Domain Skills (20-30 hours)

**Objective:** Create 6 repository-local skills for banking domain workflows

**Location:** `skills/banking/`

**Skills to Create:**

#### 1. Retail Fraud Detection Workflow (3-4 hours)

**File:** `skills/banking/retail-fraud-detection-workflow/SKILL.md`

**Purpose:** Guide analysts through retail fraud detection process

**Scope:**
- Fraud scoring workflow (velocity, network, merchant, behavioral)
- Alert triage and investigation
- Evidence collection for case management
- Integration with compliance reporting

**Components:**
```
skills/banking/retail-fraud-detection-workflow/
├── SKILL.md                    # Main skill definition
├── examples/
│   ├── fraud-alert-triage.md   # Alert triage workflow
│   ├── evidence-collection.md  # Evidence gathering
│   └── case-escalation.md      # Escalation procedures
└── templates/
    ├── fraud-report.md         # Report template
    └── investigation-log.md    # Investigation tracking
```

**Key Workflows:**
1. Alert reception and initial assessment
2. Fraud score analysis (4 components)
3. Transaction pattern review
4. Merchant risk assessment
5. Customer history analysis
6. Evidence documentation
7. Case escalation decision
8. Report generation

**Integration Points:**
- `banking/fraud/fraud_detection.py`
- `banking/compliance/audit_logger.py`
- Notebook 03: Fraud Detection

**Acceptance Criteria:**
- [ ] Complete workflow from alert to resolution
- [ ] Integration with fraud detection module
- [ ] Evidence collection templates
- [ ] Compliance reporting integration
- [ ] Example scenarios (3+)

---

#### 2. Corporate UBO Discovery Workflow (4-5 hours)

**File:** `skills/banking/corporate-ubo-discovery-workflow/SKILL.md`

**Purpose:** Guide analysts through Ultimate Beneficial Owner discovery

**Scope:**
- Multi-hop ownership traversal
- Beneficial ownership threshold detection (25%)
- Complex ownership structure analysis
- Regulatory compliance (FATF, EU 4AMLD)

**Components:**
```
skills/banking/corporate-ubo-discovery-workflow/
├── SKILL.md
├── examples/
│   ├── simple-ownership.md     # Direct ownership
│   ├── complex-chains.md       # Multi-hop chains
│   ├── circular-ownership.md   # Circular structures
│   └── offshore-entities.md    # Offshore analysis
└── templates/
    ├── ubo-report.md           # UBO report template
    └── ownership-diagram.md    # Visualization template
```

**Key Workflows:**
1. Company selection and initial analysis
2. Direct ownership identification
3. Multi-hop traversal (up to 5 levels)
4. Beneficial ownership calculation
5. Circular ownership detection
6. PEP (Politically Exposed Person) identification
7. High-risk jurisdiction flagging
8. UBO report generation

**Integration Points:**
- `banking/analytics/detect_ubo.py` (to be created)
- `banking/compliance/compliance_reporter.py`
- Notebook 10: UBO Discovery

**Acceptance Criteria:**
- [ ] Multi-hop traversal algorithm documented
- [ ] Beneficial ownership calculation examples
- [ ] Circular ownership handling
- [ ] PEP integration
- [ ] Regulatory compliance mapping
- [ ] Example scenarios (5+)

---

#### 3. AML Structuring Investigation (3-4 hours)

**File:** `skills/banking/aml-structuring-investigation/SKILL.md`

**Purpose:** Guide investigators through AML structuring (smurfing) analysis

**Scope:**
- CTR threshold monitoring ($10,000)
- Structuring pattern detection
- Transaction chain analysis
- SAR (Suspicious Activity Report) preparation

**Components:**
```
skills/banking/aml-structuring-investigation/
├── SKILL.md
├── examples/
│   ├── classic-structuring.md  # Multiple deposits <$10K
│   ├── rapid-succession.md     # Time-based patterns
│   ├── layering.md             # Multi-account chains
│   └── mule-accounts.md        # Account network analysis
└── templates/
    ├── sar-draft.md            # SAR template
    └── investigation-notes.md  # Investigation tracking
```

**Key Workflows:**
1. Transaction amount distribution analysis
2. Suspicious range identification ($9,000-$9,999)
3. Account-level pattern detection
4. High-volume account identification
5. Transaction chain analysis (layering)
6. Risk scoring and prioritization
7. SAR preparation and filing
8. Compliance documentation

**Integration Points:**
- `banking/analytics/aml_structuring_detector.py`
- `banking/compliance/audit_logger.py`
- Notebook 02: AML Structuring Detection

**Acceptance Criteria:**
- [ ] CTR threshold monitoring workflow
- [ ] Pattern detection algorithms explained
- [ ] SAR preparation guide
- [ ] Compliance documentation templates
- [ ] Example scenarios (4+)

---

#### 4. Sanctions Screening Workflow (3-4 hours)

**File:** `skills/banking/sanctions-screening-workflow/SKILL.md`

**Purpose:** Guide analysts through sanctions screening process

**Scope:**
- OFAC, UN, EU sanctions list screening
- Name matching algorithms (fuzzy matching)
- False positive reduction
- Escalation procedures

**Components:**
```
skills/banking/sanctions-screening-workflow/
├── SKILL.md
├── examples/
│   ├── exact-match.md          # Exact name matches
│   ├── fuzzy-match.md          # Fuzzy matching
│   ├── false-positive.md       # False positive handling
│   └── escalation.md           # Escalation procedures
└── templates/
    ├── screening-report.md     # Screening report
    └── match-analysis.md       # Match analysis template
```

**Key Workflows:**
1. Customer/transaction screening initiation
2. Multi-list screening (OFAC, UN, EU)
3. Name matching (exact and fuzzy)
4. Match score calculation
5. False positive analysis
6. True positive escalation
7. Compliance documentation
8. Periodic re-screening

**Integration Points:**
- `banking/aml/sanctions_screening.py`
- `banking/compliance/audit_logger.py`
- Notebook 01: Sanctions Screening

**Acceptance Criteria:**
- [ ] Multi-list screening workflow
- [ ] Fuzzy matching algorithm explained
- [ ] False positive reduction techniques
- [ ] Escalation procedures documented
- [ ] Example scenarios (4+)

---

#### 5. Customer 360 Profile Builder (3-4 hours)

**File:** `skills/banking/customer-360-profile-builder/SKILL.md`

**Purpose:** Guide analysts in building comprehensive customer profiles

**Scope:**
- Multi-source data aggregation
- Relationship mapping
- Risk assessment
- Profile visualization

**Components:**
```
skills/banking/customer-360-profile-builder/
├── SKILL.md
├── examples/
│   ├── retail-customer.md      # Retail customer profile
│   ├── corporate-customer.md   # Corporate customer profile
│   ├── high-risk-customer.md   # High-risk profile
│   └── pep-customer.md         # PEP profile
└── templates/
    ├── profile-report.md       # Profile report template
    └── risk-assessment.md      # Risk assessment template
```

**Key Workflows:**
1. Customer identification and selection
2. Account aggregation
3. Transaction history analysis
4. Relationship mapping (persons, companies)
5. Communication pattern analysis
6. Risk indicator identification
7. Profile visualization
8. Report generation

**Integration Points:**
- `banking/analytics/customer_360.py` (to be created)
- `banking/fraud/fraud_detection.py`
- `banking/aml/enhanced_structuring_detection.py`
- Notebooks 04 & 07: Customer 360

**Acceptance Criteria:**
- [ ] Multi-source aggregation workflow
- [ ] Relationship mapping algorithms
- [ ] Risk assessment framework
- [ ] Visualization examples
- [ ] Example scenarios (4+)

---

#### 6. Insider Trading Surveillance (4-5 hours)

**File:** `skills/banking/insider-trading-surveillance/SKILL.md`

**Purpose:** Guide analysts through insider trading detection and investigation

**Scope:**
- 6 detection methods (timing, coordinated, communication, network, volume, asymmetry)
- Corporate event correlation
- MNPI (Material Non-Public Information) identification
- SEC reporting

**Components:**
```
skills/banking/insider-trading-surveillance/
├── SKILL.md
├── examples/
│   ├── timing-correlation.md   # Pre-announcement trading
│   ├── coordinated-trading.md  # Multiple traders
│   ├── communication-based.md  # MNPI sharing
│   ├── network-analysis.md     # Insider connections
│   └── volume-anomaly.md       # Abnormal volume
└── templates/
    ├── investigation-report.md # Investigation report
    └── sec-filing.md           # SEC filing template
```

**Key Workflows:**
1. Corporate event identification
2. Pre-announcement window analysis (14 days)
3. Timing correlation detection
4. Coordinated trading identification
5. Communication pattern analysis
6. Network relationship mapping
7. Risk scoring and prioritization
8. Investigation and reporting

**Integration Points:**
- `banking/analytics/detect_insider_trading.py`
- `banking/compliance/compliance_reporter.py`
- Notebook 08: Insider Trading Detection

**Acceptance Criteria:**
- [ ] All 6 detection methods documented
- [ ] Corporate event correlation workflow
- [ ] MNPI identification guide
- [ ] SEC reporting procedures
- [ ] Example scenarios (6+)

---

### Banking Domain Skills: Implementation Timeline

**Week 1 (20 hours):**
- Day 1-2: Retail Fraud Detection Workflow (4 hours)
- Day 2-3: Corporate UBO Discovery Workflow (5 hours)
- Day 3-4: AML Structuring Investigation (4 hours)
- Day 4-5: Sanctions Screening Workflow (4 hours)
- Day 5: Review and testing (3 hours)

**Week 2 (10 hours):**
- Day 1-2: Customer 360 Profile Builder (4 hours)
- Day 3-4: Insider Trading Surveillance (5 hours)
- Day 5: Integration testing and documentation (1 hour)

**Total:** 30 hours (2 weeks)

**Deliverables:**
- 6 complete skill definitions in `skills/banking/`
- 30+ example scenarios across all skills
- 15+ templates for reports and workflows
- Integration with existing banking modules
- Testing and validation

---

## Priority 2 (Short-term, 2-4 weeks) - 48 hours

### Task 1: Increase Unit Test Coverage (40 hours)

**Objective:** Increase unit test coverage from 25% to 70% in AML and Compliance modules

**Current State:**
- AML module: 25% coverage
- Compliance module: 25% coverage
- Integration tests: 100% (202 tests)

**Target State:**
- AML module: 70% coverage
- Compliance module: 70% coverage
- Maintain 100% integration test pass rate

#### AML Module Test Expansion (20 hours)

**Files to Test:**
- `banking/aml/enhanced_structuring_detection.py`
- `banking/aml/sanctions_screening.py`

**Test Categories:**

1. **Enhanced Structuring Detection Tests** (10 hours)
   ```
   tests/unit/aml/test_enhanced_structuring_detection.py
   
   Test Coverage:
   - Graph pattern detection (3 methods)
   - Semantic pattern detection
   - Hybrid detection
   - Risk scoring algorithms
   - Edge case handling
   - Performance benchmarks
   ```

   **Test Cases (30+):**
   - Graph pattern detection:
     * Single-hop structuring
     * Multi-hop structuring (2-5 hops)
     * Circular patterns
     * Star patterns
     * Chain patterns
   - Semantic pattern detection:
     * Keyword matching
     * NLP-based detection
     * False positive filtering
   - Hybrid detection:
     * Combined graph + semantic
     * Confidence scoring
     * Threshold tuning
   - Risk scoring:
     * Score calculation
     * Severity classification
     * Alert generation
   - Edge cases:
     * Empty graph
     * Single transaction
     * Large transaction sets (10K+)
     * Missing data handling

2. **Sanctions Screening Tests** (10 hours)
   ```
   tests/unit/aml/test_sanctions_screening.py
   
   Test Coverage:
   - OFAC list screening
   - UN list screening
   - EU list screening
   - Fuzzy name matching
   - False positive reduction
   - Performance benchmarks
   ```

   **Test Cases (25+):**
   - Exact matching:
     * Full name match
     * Partial name match
     * Case sensitivity
   - Fuzzy matching:
     * Levenshtein distance
     * Soundex matching
     * Metaphone matching
   - Multi-list screening:
     * OFAC screening
     * UN screening
     * EU screening
     * Combined screening
   - False positive handling:
     * Common name filtering
     * Date of birth matching
     * Address matching
   - Performance:
     * Single name screening (<200ms)
     * Batch screening (1000 names <5s)
     * Large list handling (100K+ entries)

**Implementation Approach:**
```python
# Example test structure
import pytest
from banking.aml.enhanced_structuring_detection import EnhancedStructuringDetector

class TestEnhancedStructuringDetection:
    @pytest.fixture
    def detector(self):
        return EnhancedStructuringDetector(url="ws://localhost:18182/gremlin")
    
    def test_graph_pattern_single_hop(self, detector):
        """Test single-hop structuring pattern detection"""
        # Setup test data
        # Execute detection
        # Assert results
        pass
    
    def test_semantic_pattern_keyword_matching(self, detector):
        """Test keyword-based semantic detection"""
        pass
    
    @pytest.mark.benchmark
    def test_performance_large_dataset(self, detector, benchmark):
        """Benchmark detection on large dataset"""
        pass
```

#### Compliance Module Test Expansion (20 hours)

**Files to Test:**
- `banking/compliance/audit_logger.py`
- `banking/compliance/compliance_reporter.py`

**Test Categories:**

1. **Audit Logger Tests** (10 hours)
   ```
   tests/unit/compliance/test_audit_logger.py
   
   Test Coverage:
   - All 30+ event types
   - Severity filtering
   - Log rotation
   - JSON serialization
   - File I/O operations
   - Error handling
   ```

   **Test Cases (35+):**
   - Event logging:
     * Data access events (3 types)
     * Data modification events (3 types)
     * Authentication events (4 types)
     * Authorization events (3 types)
     * Administrative events (4 types)
     * Compliance events (5 types)
     * Security events (7 types)
     * System events (3 types)
   - Severity filtering:
     * INFO level filtering
     * WARNING level filtering
     * ERROR level filtering
     * CRITICAL level filtering
   - Log operations:
     * File creation
     * Append operations
     * Log rotation
     * Concurrent writes
   - Serialization:
     * JSON formatting
     * Timestamp formatting
     * Metadata handling
   - Error handling:
     * Invalid event types
     * Missing required fields
     * File permission errors
     * Disk space errors

2. **Compliance Reporter Tests** (10 hours)
   ```
   tests/unit/compliance/test_compliance_reporter.py
   
   Test Coverage:
   - Log parsing
   - Metrics calculation
   - Violation detection
   - Report generation (4 types)
   - Export formats (JSON, CSV, HTML)
   - Performance benchmarks
   ```

   **Test Cases (30+):**
   - Log parsing:
     * Valid JSON logs
     * Invalid JSON handling
     * Date range filtering
     * Large log files (1M+ events)
   - Metrics calculation:
     * Event counting
     * User aggregation
     * Resource aggregation
     * Time-based metrics
   - Violation detection:
     * Excessive failed auth
     * Unauthorized access attempts
     * Security incidents
     * Unencrypted data access
   - Report generation:
     * GDPR Article 30 report
     * SOC 2 Type II report
     * BSA/AML report
     * Comprehensive report
   - Export formats:
     * JSON export
     * CSV export
     * HTML export
     * Format validation
   - Performance:
     * 1M events parsing (<5s)
     * Report generation (<5s)
     * Export operations (<2s)

**Implementation Approach:**
```python
# Example test structure
import pytest
from banking.compliance.audit_logger import AuditLogger, AuditEventType, AuditSeverity
from banking.compliance.compliance_reporter import ComplianceReporter

class TestAuditLogger:
    @pytest.fixture
    def logger(self, tmp_path):
        return AuditLogger(log_dir=str(tmp_path), log_file="test_audit.log")
    
    def test_log_data_access(self, logger):
        """Test data access event logging"""
        logger.log_data_access(
            user="test@example.com",
            resource="customer:123",
            action="query",
            result="success"
        )
        # Assert log file contains event
        pass
    
    def test_severity_filtering(self, logger):
        """Test severity-based filtering"""
        pass
    
    @pytest.mark.parametrize("event_type", [
        AuditEventType.DATA_ACCESS,
        AuditEventType.AUTH_LOGIN,
        AuditEventType.GDPR_DATA_REQUEST,
        # ... all 30+ event types
    ])
    def test_all_event_types(self, logger, event_type):
        """Test all event types can be logged"""
        pass

class TestComplianceReporter:
    @pytest.fixture
    def reporter(self, tmp_path):
        return ComplianceReporter(log_dir=str(tmp_path))
    
    def test_gdpr_report_generation(self, reporter):
        """Test GDPR Article 30 report generation"""
        pass
    
    def test_violation_detection(self, reporter):
        """Test compliance violation detection"""
        pass
```

#### Test Coverage Tracking

**Tools:**
- pytest-cov for coverage measurement
- coverage.py for detailed reports
- codecov for CI integration

**Coverage Targets:**
```bash
# Run tests with coverage
pytest banking/aml/tests/ --cov=banking/aml --cov-report=html --cov-report=term-missing
pytest banking/compliance/tests/ --cov=banking/compliance --cov-report=html --cov-report=term-missing

# Coverage targets
# AML module: 70% (from 25%)
# Compliance module: 70% (from 25%)
```

**Acceptance Criteria:**
- [ ] AML module coverage ≥70%
- [ ] Compliance module coverage ≥70%
- [ ] All critical paths covered
- [ ] Edge cases tested
- [ ] Performance benchmarks included
- [ ] Integration tests still pass (100%)

---

### Task 2: Add API Documentation (8 hours)

**Objective:** Document REST API endpoints for all banking modules

**Current State:**
- No API documentation for banking modules
- OpenAPI spec exists for core API (`docs/api/openapi.yaml`)

**Target State:**
- Complete API documentation for all banking modules
- OpenAPI 3.0 specifications
- Interactive API documentation (Swagger UI)

#### API Documentation Structure

**Files to Create:**

1. **Banking API OpenAPI Spec** (3 hours)
   ```
   docs/api/banking-api.yaml
   
   Endpoints to Document:
   - /api/v1/aml/structuring/detect
   - /api/v1/aml/sanctions/screen
   - /api/v1/fraud/score
   - /api/v1/fraud/alerts
   - /api/v1/analytics/insider-trading/detect
   - /api/v1/analytics/tbml/detect
   - /api/v1/analytics/customer-360/{customer_id}
   - /api/v1/compliance/audit/log
   - /api/v1/compliance/reports/generate
   ```

   **OpenAPI Spec Structure:**
   ```yaml
   openapi: 3.0.0
   info:
     title: Banking Domain API
     version: 1.0.0
     description: REST API for banking analytics, AML, fraud detection, and compliance
   
   servers:
     - url: http://localhost:8000
       description: Development server
     - url: https://api.example.com
       description: Production server
   
   paths:
     /api/v1/aml/structuring/detect:
       post:
         summary: Detect AML structuring patterns
         description: Analyzes transactions for structuring patterns (smurfing)
         operationId: detectStructuring
         tags:
           - AML
         requestBody:
           required: true
           content:
             application/json:
               schema:
                 $ref: '#/components/schemas/StructuringDetectionRequest'
         responses:
           '200':
             description: Structuring patterns detected
             content:
               application/json:
                 schema:
                   $ref: '#/components/schemas/StructuringDetectionResponse'
           '400':
             description: Invalid request
           '500':
             description: Internal server error
   
   components:
     schemas:
       StructuringDetectionRequest:
         type: object
         required:
           - account_ids
           - start_date
           - end_date
         properties:
           account_ids:
             type: array
             items:
               type: string
             description: List of account IDs to analyze
           start_date:
             type: string
             format: date-time
             description: Start date for analysis
           end_date:
             type: string
             format: date-time
             description: End date for analysis
           threshold:
             type: number
             format: float
             default: 9500.0
             description: Structuring threshold amount
   
       StructuringDetectionResponse:
         type: object
         properties:
           patterns:
             type: array
             items:
               $ref: '#/components/schemas/StructuringPattern'
           summary:
             $ref: '#/components/schemas/DetectionSummary'
   
       StructuringPattern:
         type: object
         properties:
           account_id:
             type: string
           suspicious_tx_count:
             type: integer
           pattern:
             type: string
             enum: [STRUCTURING, LAYERING, RAPID_SUCCESSION]
           risk_level:
             type: string
             enum: [LOW, MEDIUM, HIGH, CRITICAL]
           recommendation:
             type: string
   ```

2. **API Reference Documentation** (2 hours)
   ```
   docs/api/banking-api-reference.md
   
   Sections:
   - Authentication
   - Rate Limiting
   - Error Handling
   - Endpoint Reference
   - Request/Response Examples
   - SDK Examples (Python, JavaScript)
   ```

   **Content Structure:**
   ```markdown
   # Banking Domain API Reference
   
   ## Authentication
   
   All API requests require authentication using JWT tokens:
   
   ```bash
   curl -H "Authorization: Bearer <token>" \
        https://api.example.com/api/v1/aml/structuring/detect
   ```
   
   ## Rate Limiting
   
   - 100 requests per minute per API key
   - 1000 requests per hour per API key
   - Rate limit headers included in responses
   
   ## Error Handling
   
   Standard HTTP status codes:
   - 200: Success
   - 400: Bad Request
   - 401: Unauthorized
   - 403: Forbidden
   - 429: Too Many Requests
   - 500: Internal Server Error
   
   Error response format:
   ```json
   {
     "error": {
       "code": "INVALID_REQUEST",
       "message": "Missing required field: account_ids",
       "details": {}
     }
   }
   ```
   
   ## Endpoints
   
   ### AML Structuring Detection
   
   **POST /api/v1/aml/structuring/detect**
   
   Detects AML structuring patterns in transaction data.
   
   **Request:**
   ```json
   {
     "account_ids": ["acc-123", "acc-456"],
     "start_date": "2026-01-01T00:00:00Z",
     "end_date": "2026-01-31T23:59:59Z",
     "threshold": 9500.0
   }
   ```
   
   **Response:**
   ```json
   {
     "patterns": [
       {
         "account_id": "acc-123",
         "suspicious_tx_count": 5,
         "pattern": "STRUCTURING",
         "risk_level": "HIGH",
         "recommendation": "File SAR"
       }
     ],
     "summary": {
       "total_accounts_analyzed": 2,
       "patterns_found": 1,
       "high_risk_accounts": 1
     }
   }
   ```
   
   **Python SDK Example:**
   ```python
   from banking_api import BankingAPIClient
   
   client = BankingAPIClient(api_key="your-api-key")
   
   result = client.aml.detect_structuring(
       account_ids=["acc-123", "acc-456"],
       start_date="2026-01-01T00:00:00Z",
       end_date="2026-01-31T23:59:59Z",
       threshold=9500.0
   )
   
   for pattern in result.patterns:
       print(f"Account: {pattern.account_id}")
       print(f"Risk Level: {pattern.risk_level}")
       print(f"Recommendation: {pattern.recommendation}")
   ```
   ```

3. **Swagger UI Integration** (2 hours)
   ```
   docs/api/swagger-ui.html
   
   Features:
   - Interactive API documentation
   - Try-it-out functionality
   - Request/response examples
   - Schema validation
   ```

4. **Postman Collection** (1 hour)
   ```
   docs/api/banking-api.postman_collection.json
   
   Collections:
   - AML Detection
   - Fraud Detection
   - Analytics
   - Compliance
   
   Includes:
   - Pre-configured requests
   - Environment variables
   - Test scripts
   - Example responses
   ```

**Implementation Timeline:**

**Week 1 (8 hours):**
- Day 1: OpenAPI spec creation (3 hours)
- Day 2: API reference documentation (2 hours)
- Day 3: Swagger UI integration (2 hours)
- Day 4: Postman collection creation (1 hour)

**Deliverables:**
- `docs/api/banking-api.yaml` (OpenAPI 3.0 spec)
- `docs/api/banking-api-reference.md` (API reference)
- `docs/api/swagger-ui.html` (Interactive docs)
- `docs/api/banking-api.postman_collection.json` (Postman collection)

**Acceptance Criteria:**
- [ ] All banking endpoints documented
- [ ] OpenAPI 3.0 spec validates
- [ ] Swagger UI functional
- [ ] Postman collection tested
- [ ] SDK examples included
- [ ] Error handling documented

---

## Implementation Timeline Summary

### Priority 1 (1-2 weeks, 25 hours)

| Task | Duration | Status |
|------|----------|--------|
| Compliance Module README | 2 hours | ✅ COMPLETE |
| Analytics Module README | 3 hours | ✅ COMPLETE |
| Banking Domain Skills (6 skills) | 20-30 hours | 🔄 PLANNED |

**Total P1:** 25-35 hours

### Priority 2 (2-4 weeks, 48 hours)

| Task | Duration | Status |
|------|----------|--------|
| AML Module Test Coverage (25% → 70%) | 20 hours | 📋 PLANNED |
| Compliance Module Test Coverage (25% → 70%) | 20 hours | 📋 PLANNED |
| API Documentation | 8 hours | 📋 PLANNED |

**Total P2:** 48 hours

### Combined Timeline (3-4 weeks, 73-83 hours)

**Week 1 (20 hours):**
- Banking Skills 1-4 (16 hours)
- API Documentation start (4 hours)

**Week 2 (20 hours):**
- Banking Skills 5-6 (9 hours)
- API Documentation complete (4 hours)
- AML Test Coverage start (7 hours)

**Week 3 (20 hours):**
- AML Test Coverage complete (13 hours)
- Compliance Test Coverage start (7 hours)

**Week 4 (13-23 hours):**
- Compliance Test Coverage complete (13 hours)
- Buffer for testing and documentation (0-10 hours)

---

## Resource Requirements

### Team Composition

**Option A: 2 Developers (4 weeks)**
- Developer 1: Banking Skills + API Documentation (33 hours)
- Developer 2: Test Coverage (40 hours)

**Option B: 3 Developers (2-3 weeks)**
- Developer 1: Banking Skills (30 hours)
- Developer 2: AML Test Coverage (20 hours)
- Developer 3: Compliance Test Coverage + API Documentation (28 hours)

### Tools & Infrastructure

**Required:**
- JanusGraph instance (running)
- Test environment with sample data
- CI/CD pipeline for test execution
- Code coverage tools (pytest-cov, codecov)
- API documentation tools (Swagger UI, Postman)

**Optional:**
- Property-based testing (Hypothesis)
- Mutation testing (mutmut)
- Performance profiling (py-spy)

---

## Success Metrics

### Priority 1 Success Criteria

- [ ] All 6 banking domain skills created and documented
- [ ] 30+ example scenarios across all skills
- [ ] 15+ templates for reports and workflows
- [ ] Integration with existing banking modules verified
- [ ] Skills tested with real-world scenarios

### Priority 2 Success Criteria

- [ ] AML module test coverage ≥70%
- [ ] Compliance module test coverage ≥70%
- [ ] All critical paths covered by tests
- [ ] Edge cases tested
- [ ] Performance benchmarks established
- [ ] API documentation complete for all endpoints
- [ ] OpenAPI spec validates
- [ ] Swagger UI functional
- [ ] Postman collection tested

### Overall Success Metrics

- **Documentation Quality:** All modules have comprehensive READMEs (100%)
- **Test Coverage:** AML and Compliance modules ≥70% (from 25%)
- **API Documentation:** All banking endpoints documented
- **Skills Coverage:** 6 banking domain skills operational
- **Integration:** All skills integrate with existing modules
- **Performance:** All benchmarks met

---

## Risk Management

### Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Skills complexity underestimated | Medium | High | Add 10-hour buffer per skill |
| Test coverage goals too aggressive | Low | Medium | Prioritize critical paths first |
| API documentation scope creep | Medium | Low | Stick to defined endpoints only |
| Integration issues with existing code | Low | High | Early integration testing |
| Resource availability | Medium | High | Cross-train team members |

### Contingency Plans

**If behind schedule:**
1. Reduce skills from 6 to 4 (prioritize retail fraud, AML structuring, sanctions, UBO)
2. Reduce test coverage target from 70% to 60%
3. Defer API documentation to Priority 3

**If ahead of schedule:**
1. Add 2 additional skills (TBML workflow, compliance reporting workflow)
2. Increase test coverage target to 80%
3. Add GraphQL API documentation

---

## Dependencies

### External Dependencies

- JanusGraph 1.0.0+ running
- HCD 1.2.3+ running
- Python 3.11+
- pytest 7.0+
- OpenAPI 3.0 tools

### Internal Dependencies

- Banking modules (AML, Fraud, Analytics, Compliance)
- Existing notebooks (01-11)
- Test infrastructure
- CI/CD pipeline

---

## Approval & Sign-off

**Plan Prepared By:** IBM Bob (AI Assistant)  
**Date:** 2026-02-20  
**Version:** 1.0

**Approval Required From:**
- [ ] Technical Lead
- [ ] Product Manager
- [ ] QA Lead
- [ ] Security Team

**Sign-off Date:** _________________

---

## Appendix

### A. Skill Template Structure

```markdown
# Skill Name

**Version:** 1.0.0
**Last Updated:** YYYY-MM-DD
**Status:** Active

## Overview

Brief description of the skill and its purpose.

## Prerequisites

- Required knowledge
- Required tools
- Required access

## Workflow

### Step 1: [Step Name]

Description and instructions.

**Commands:**
```bash
# Example commands
```

**Expected Output:**
```
# Example output
```

### Step 2: [Step Name]

...

## Examples

### Example 1: [Scenario Name]

Detailed walkthrough of a real-world scenario.

## Troubleshooting

Common issues and solutions.

## Related Documentation

- Links to related docs
- Links to related skills

## Support

Contact information and resources.
```

### B. Test Template Structure

```python
"""
Test module for [Module Name]

Test Coverage:
- [Feature 1]
- [Feature 2]
- [Feature 3]
"""

import pytest
from banking.[module] import [Class]

class Test[ClassName]:
    """Test suite for [ClassName]"""
    
    @pytest.fixture
    def instance(self):
        """Create test instance"""
        return [Class]()
    
    def test_[feature_name](self, instance):
        """Test [feature description]"""
        # Arrange
        # Act
        # Assert
        pass
    
    @pytest.mark.parametrize("input,expected", [
        (input1, expected1),
        (input2, expected2),
    ])
    def test_[feature_name]_parametrized(self, instance, input, expected):
        """Test [feature] with multiple inputs"""
        pass
    
    @pytest.mark.benchmark
    def test_[feature_name]_performance(self, instance, benchmark):
        """Benchmark [feature] performance"""
        result = benchmark(instance.method)
        assert result < threshold
```

### C. API Documentation Template

```yaml
paths:
  /api/v1/[module]/[endpoint]:
    post:
      summary: [Brief description]
      description: [Detailed description]
      operationId: [operationId]
      tags:
        - [Module]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/[RequestSchema]'
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/[ResponseSchema]'
        '400':
          description: Bad Request
        '500':
          description: Internal Server Error

components:
  schemas:
    [RequestSchema]:
      type: object
      required:
        - [field1]
        - [field2]
      properties:
        [field1]:
          type: string
          description: [Description]
        [field2]:
          type: integer
          description: [Description]
    
    [ResponseSchema]:
      type: object
      properties:
        [field1]:
          type: string
        [field2]:
          type: array
          items:
            $ref: '#/components/schemas/[NestedSchema]'
```

---

**End of Implementation Plan**