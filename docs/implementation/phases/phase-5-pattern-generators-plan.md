# Phase 5: Pattern Generators Implementation Plan

**Date:** 2026-04-08  
**Status:** 🚧 IN PROGRESS  
**Target:** 72% → 100% coverage  
**Current:** 161 tests passing

---

## Executive Summary

Pattern generators already have **excellent coverage** for most files. Only 2 files need significant work:

1. **`cato_pattern_generator.py`**: 44% → 100% (needs ~30 tests)
2. **`ownership_chain_generator.py`**: 0% → 100% (needs ~40 tests)

**Estimated Effort:** 1 week (40 hours) instead of 2 weeks

---

## Current Coverage Analysis

### Coverage by File

| File | Coverage | Lines | Missing | Priority | Status |
|------|----------|-------|---------|----------|--------|
| `fraud_ring_pattern_generator.py` | **98%** | 117 | 2 | ✅ Low | Excellent |
| `insider_trading_pattern_generator.py` | **97%** | 141 | 2 | ✅ Low | Excellent |
| `tbml_pattern_generator.py` | **98%** | 176 | 3 | ✅ Low | Excellent |
| `structuring_pattern_generator.py` | **90%** | 86 | 5 | ✅ Low | Good |
| `mule_chain_generator.py` | **87%** | 65 | 5 | ✅ Low | Good |
| `cato_pattern_generator.py` | **44%** | 266 | 145 | 🔴 **High** | **Needs Work** |
| `ownership_chain_generator.py` | **0%** | 207 | 207 | 🔴 **Critical** | **Needs Work** |

**Average:** ~72% (need +28% to reach 100%)

---

## Implementation Strategy

### Phase 5A: Ownership Chain Generator (Priority 1)

**File:** `ownership_chain_generator.py` (207 lines, 0% coverage)  
**Target:** 0% → 100%  
**Estimated Tests:** 40-45 tests  
**Estimated Time:** 20 hours

#### Missing Coverage Areas

1. **Initialization (lines 22-50)**
   - Default parameters
   - Custom configuration
   - Seed handling
   - Validation

2. **Chain Generation (lines 51-150)**
   - Simple chains (2-3 levels)
   - Complex chains (4-5 levels)
   - Multi-branch chains
   - Circular ownership detection
   - Cross-border chains

3. **UBO Discovery (lines 151-250)**
   - Direct ownership
   - Indirect ownership
   - Threshold-based UBO
   - Multiple UBO scenarios
   - Nominee structures

4. **Pattern Injection (lines 251-400)**
   - Shell company patterns
   - Tax haven structures
   - Layered ownership
   - Beneficial owner obfuscation
   - Regulatory evasion patterns

5. **Validation (lines 401-500)**
   - Ownership percentage validation
   - Chain integrity checks
   - Circular reference detection
   - Data consistency

6. **Edge Cases (lines 501-627)**
   - Empty entity lists
   - Single entity
   - Maximum depth chains
   - Zero ownership percentages
   - 100% ownership scenarios

#### Test Structure

```python
# test_ownership_chain_generator_unit.py

class TestOwnershipChainInitialization:
    """Test initialization and configuration"""
    def test_init_default_parameters()
    def test_init_custom_seed()
    def test_init_custom_max_depth()
    def test_init_custom_ubo_threshold()
    def test_init_validation()

class TestSimpleChainGeneration:
    """Test basic chain generation"""
    def test_generate_two_level_chain()
    def test_generate_three_level_chain()
    def test_generate_with_percentages()
    def test_generate_deterministic()

class TestComplexChainGeneration:
    """Test complex ownership structures"""
    def test_generate_multi_branch_chain()
    def test_generate_cross_border_chain()
    def test_generate_with_shell_companies()
    def test_generate_with_nominees()

class TestUBODiscovery:
    """Test Ultimate Beneficial Owner discovery"""
    def test_discover_direct_ubo()
    def test_discover_indirect_ubo()
    def test_discover_multiple_ubos()
    def test_discover_with_threshold()
    def test_discover_complex_structure()

class TestPatternInjection:
    """Test pattern injection"""
    def test_inject_shell_company_pattern()
    def test_inject_tax_haven_pattern()
    def test_inject_layered_ownership()
    def test_inject_obfuscation_pattern()

class TestValidation:
    """Test validation logic"""
    def test_validate_ownership_percentages()
    def test_validate_chain_integrity()
    def test_detect_circular_references()
    def test_validate_data_consistency()

class TestEdgeCases:
    """Test edge cases and error handling"""
    def test_empty_entity_list()
    def test_single_entity()
    def test_maximum_depth_chain()
    def test_zero_ownership()
    def test_full_ownership()
    def test_invalid_percentages()
```

---

### Phase 5B: CATO Pattern Generator (Priority 2)

**File:** `cato_pattern_generator.py` (266 lines, 44% coverage)  
**Target:** 44% → 100%  
**Estimated Tests:** 30-35 tests  
**Estimated Time:** 20 hours

#### Missing Coverage Areas

**Lines 96, 104-121:** Initialization edge cases
**Lines 247-305:** Account takeover pattern generation
**Lines 332-395:** Credential stuffing patterns
**Lines 422-479:** Phishing patterns
**Lines 507-557:** Social engineering patterns
**Lines 590-680:** Pattern validation and edge cases

#### Test Structure

```python
# test_cato_pattern_generator_unit.py

class TestCATOInitialization:
    """Test CATO pattern generator initialization"""
    def test_init_default_parameters()
    def test_init_custom_seed()
    def test_init_custom_attack_vectors()
    def test_init_validation()

class TestAccountTakeoverPatterns:
    """Test account takeover pattern generation"""
    def test_generate_credential_theft()
    def test_generate_session_hijacking()
    def test_generate_password_reset_abuse()
    def test_generate_multi_factor_bypass()

class TestCredentialStuffingPatterns:
    """Test credential stuffing patterns"""
    def test_generate_automated_login_attempts()
    def test_generate_distributed_attacks()
    def test_generate_rate_limited_attacks()
    def test_generate_success_patterns()

class TestPhishingPatterns:
    """Test phishing pattern generation"""
    def test_generate_email_phishing()
    def test_generate_smishing()
    def test_generate_vishing()
    def test_generate_spear_phishing()

class TestSocialEngineeringPatterns:
    """Test social engineering patterns"""
    def test_generate_pretexting()
    def test_generate_baiting()
    def test_generate_quid_pro_quo()
    def test_generate_tailgating()

class TestPatternValidation:
    """Test pattern validation"""
    def test_validate_attack_timeline()
    def test_validate_victim_selection()
    def test_validate_success_indicators()
    def test_validate_data_consistency()

class TestEdgeCases:
    """Test edge cases"""
    def test_empty_entity_list()
    def test_single_victim()
    def test_multiple_concurrent_attacks()
    def test_failed_attacks()
```

---

## Test Quality Requirements

### Deterministic Testing
- ✅ Use fixed seeds (42, 123, 999)
- ✅ Fixed timestamps (REFERENCE_TIMESTAMP)
- ✅ Reproducible entity generation
- ✅ Consistent pattern injection

### Mock Strategy
```python
# Mock external dependencies
@patch("banking.data_generators.patterns.ownership_chain_generator.random")
@patch("banking.data_generators.patterns.ownership_chain_generator.Faker")

# Mock JanusGraph loader
@patch("banking.data_generators.loaders.janusgraph_loader.JanusGraphLoader")
```

### Coverage Targets
- **Line Coverage:** 100%
- **Branch Coverage:** 95%+
- **Function Coverage:** 100%
- **Edge Cases:** Comprehensive

---

## Implementation Timeline

### Week 1: Ownership Chain Generator

**Days 1-2:** Initialization & Simple Chains (10 tests)
- Initialization tests (5 tests)
- Simple chain generation (5 tests)

**Days 3-4:** Complex Chains & UBO Discovery (15 tests)
- Complex chain generation (8 tests)
- UBO discovery (7 tests)

**Day 5:** Pattern Injection & Validation (15 tests)
- Pattern injection (8 tests)
- Validation (7 tests)

### Week 2: CATO Pattern Generator

**Days 1-2:** Account Takeover & Credential Stuffing (15 tests)
- Account takeover patterns (8 tests)
- Credential stuffing (7 tests)

**Days 3-4:** Phishing & Social Engineering (15 tests)
- Phishing patterns (8 tests)
- Social engineering (7 tests)

**Day 5:** Validation & Edge Cases (5 tests)
- Pattern validation (3 tests)
- Edge cases (2 tests)

---

## Success Criteria

### Coverage Metrics
- ✅ `ownership_chain_generator.py`: 0% → 100%
- ✅ `cato_pattern_generator.py`: 44% → 100%
- ✅ Overall pattern generators: 72% → 100%

### Test Quality
- ✅ All tests passing (target: 230+ tests)
- ✅ Deterministic (reproducible results)
- ✅ Fast execution (<30 seconds)
- ✅ Comprehensive edge cases

### Documentation
- ✅ Test documentation
- ✅ Coverage report
- ✅ Phase summary

---

## Risk Assessment

### Low Risk
- ✅ Most pattern generators already at 90%+ coverage
- ✅ Existing test infrastructure in place
- ✅ Clear test patterns established

### Medium Risk
- ⚠️ Ownership chain complexity (circular references, multi-level)
- ⚠️ CATO pattern variety (many attack vectors)

### Mitigation
- Start with simple test cases
- Build complexity incrementally
- Use existing pattern generator tests as templates
- Regular coverage checks

---

## Dependencies

### Required
- ✅ `pytest` (already installed)
- ✅ `pytest-cov` (already installed)
- ✅ `Faker` (already installed)
- ✅ Existing test infrastructure

### Optional
- Property-based testing (Hypothesis) - already available
- Performance benchmarking - already available

---

## Next Steps

1. **Start with Ownership Chain Generator** (Priority 1)
   - Create `test_ownership_chain_generator_unit.py`
   - Implement 40-45 comprehensive tests
   - Target: 0% → 100% coverage

2. **Then CATO Pattern Generator** (Priority 2)
   - Enhance existing `test_cato_pattern_generator_unit.py`
   - Add 30-35 missing tests
   - Target: 44% → 100% coverage

3. **Verification**
   - Run full test suite
   - Verify 100% coverage
   - Create phase summary

---

## Comparison with Original Estimate

**Original Estimate:**
- 60-70 tests
- 2 weeks (80 hours)
- 72% → 100% coverage

**Revised Estimate:**
- 70-80 tests (10 more for thoroughness)
- 1 week (40 hours) - **50% faster!**
- 72% → 100% coverage

**Why Faster:**
- 5 of 7 files already at 87-98% coverage
- Only 2 files need significant work
- Existing test infrastructure mature
- Clear patterns established

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-08  
**Author:** David LECONTE - IBM Worldwide | Data & AI | Tiger Team  
**Status:** Ready to implement