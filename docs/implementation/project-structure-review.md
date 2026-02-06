# Project Structure Review and Documentation Audit

**Date:** 2026-01-28  
**Reviewer:** David Leconte  
**Scope:** Complete folder structure and documentation (.md) organization audit

---

## Executive Summary

This review analyzes the project's folder structure and documentation organization against industry best practices. The project demonstrates **good overall organization** with clear separation of concerns, but has **23 documentation placement issues** requiring attention.

**Key Findings:**
- ✅ **Strengths:** Clear module separation, comprehensive documentation coverage
- ⚠️ **Issues:** Root directory clutter (35+ .md files), inconsistent documentation hierarchy
- 🎯 **Priority:** Consolidate root-level documentation, standardize naming conventions

---

## 1. Current Folder Structure Analysis

### 1.1 Root Directory Structure

```
hcd-tarball-janusgraph/
├── .bob/                          # ✅ AI assistant configuration (good isolation)
├── .github/                       # ✅ GitHub workflows (standard location)
├── banking/                       # ✅ Banking domain module (well-organized)
├── config/                        # ✅ Configuration files (appropriate)
├── data/                          # ✅ Data storage (appropriate)
├── docker/                        # ✅ Docker configurations (standard)
├── docs/                          # ✅ Documentation hub (good practice)
├── hcd-1.2.3/                     # ✅ Third-party binary (acceptable)
├── notebooks/                     # ✅ Jupyter notebooks (standard location)
├── scripts/                       # ✅ Utility scripts (well-organized)
├── src/                           # ✅ Source code (standard location)
├── tests/                         # ✅ Test suite (standard location)
└── [35+ .md files]                # ⚠️ ISSUE: Too many root-level docs
```

**Assessment:** ✅ **GOOD** - Clear separation of concerns with standard directory names

### 1.2 Documentation Directory Structure

```
docs/
├── api/                           # ✅ API documentation (good organization)
│   ├── CHANGELOG.md
│   ├── GREMLIN_API.md
│   ├── INTEGRATION_GUIDE.md
│   ├── openapi.yaml
│   └── README.md
├── architecture/                  # ✅ Architecture decisions (ADRs)
│   ├── ADR-005-jwt-authentication.md
│   ├── ADR-010-distributed-tracing.md
│   ├── ADR-011-query-caching-strategy.md
│   ├── ADR-TEMPLATE.md
│   └── README.md
├── banking/                       # ✅ Banking-specific docs (domain-driven)
│   ├── [27 .md files]            # ⚠️ ISSUE: Too many files, needs sub-organization
│   └── README.md
├── compliance/                    # ✅ Compliance documentation
│   ├── DATA_RETENTION_POLICY.md
│   ├── GDPR_COMPLIANCE.md
│   └── SOC2_CONTROLS.md
├── development/                   # ✅ Development guides
│   └── CODE_REFACTORING_GUIDE.md
├── migration/                     # ✅ Migration guides
│   └── v1-to-v2.md
├── operations/                    # ✅ Operations documentation
│   └── OPERATIONS_RUNBOOK.md
├── performance/                   # ✅ Performance documentation
│   └── INFRASTRUCTURE_OPTIMIZATION.md
└── [18 .md files at root]        # ⚠️ ISSUE: Should be in subdirectories
```

**Assessment:** ⚠️ **NEEDS IMPROVEMENT** - Good structure but inconsistent file placement

### 1.3 Banking Module Structure

```
banking/
├── aml/                           # ✅ AML detection modules
├── data/                          # ✅ Banking data (well-organized)
│   ├── aml/
│   ├── customer360/
│   ├── fraud/
│   └── trade_surveillance/
├── data_generators/               # ✅ Synthetic data generation (excellent structure)
│   ├── core/                     # ✅ Core generators
│   ├── events/                   # ✅ Event generators
│   ├── examples/                 # ✅ Usage examples
│   ├── orchestration/            # ✅ Orchestration logic
│   ├── patterns/                 # ✅ Pattern generators
│   ├── relationships/            # ✅ Relationship modeling
│   ├── scenarios/                # ✅ Scenario templates
│   ├── tests/                    # ✅ Comprehensive test suite
│   └── utils/                    # ✅ Utility functions
├── docs/                          # ⚠️ ISSUE: Duplicates docs/banking/
├── fraud/                         # ✅ Fraud detection modules
├── notebooks/                     # ✅ Banking notebooks
├── queries/                       # ✅ Gremlin queries
├── schema/                        # ✅ Graph schemas
└── scripts/                       # ✅ Banking scripts
```

**Assessment:** ✅ **EXCELLENT** - Well-organized with clear domain boundaries

---

## 2. Documentation Placement Issues

### 2.1 Critical Issues (Priority 1)

#### Issue #1: Root Directory Clutter
**Severity:** HIGH  
**Location:** `/` (root directory)  
**Problem:** 35+ markdown files in root directory

**Current State:**
```
Root directory contains:
- AGENTS.md
- audit_comparison.md
- AUDIT_REPORT.md
- AUDIT_REPORT_OPENSEARCH_ADDENDUM.md
- CHANGELOG.md
- CODE_OF_CONDUCT.md
- EXECUTIVE_SUMMARY.md
- PHASE1_IMPLEMENTATION_SUMMARY.md
- PHASE2_WEEK2_COMPLETE_SUMMARY.md
- PHASE2_WEEK2_IMPLEMENTATION_SUMMARY.md
- project_audit_and_plan_Gemini_.md
- QUICKSTART.md
- README.md
- remediation_plan_Gemini_.md
- REMEDIATION_PLAN.md
- SECURITY.md
- [and 19 more...]
```

**Recommendation:**
```
Move to appropriate subdirectories:
- Audit reports → docs/audits/
- Phase summaries → docs/implementation/phases/
- Remediation plans → docs/implementation/remediation/
- Gemini files → docs/archive/gemini/
- Keep only: README.md, QUICKSTART.md, LICENSE, SECURITY.md, CODE_OF_CONDUCT.md
```

**Impact:** Improves discoverability, reduces cognitive load, follows best practices

---

#### Issue #2: Duplicate Documentation Hierarchy
**Severity:** HIGH  
**Location:** `banking/docs/` vs `docs/banking/`  
**Problem:** Two separate documentation locations for banking domain

**Current State:**
```
banking/docs/
├── 00_OVERVIEW.md
└── 01_AML_PHASE1_SETUP.md

docs/banking/
├── [27 comprehensive .md files]
└── All Phase 8 documentation
```

**Recommendation:**
```
Consolidate to single location:
1. Move banking/docs/* → docs/banking/setup/
2. Remove empty banking/docs/ directory
3. Update all references in code and documentation
```

**Impact:** Eliminates confusion, single source of truth

---

#### Issue #3: Inconsistent Naming Conventions
**Severity:** MEDIUM  
**Location:** Multiple directories  
**Problem:** Mixed naming styles (UPPERCASE, lowercase, PascalCase)

**Examples:**
```
❌ Inconsistent:
- PHASE8_COMPLETE.md
- phase8_implementation_guide.md (doesn't exist but would be inconsistent)
- API_REFERENCE.md
- user_guide.md (doesn't exist)

✅ Should be:
- phase8-complete.md (kebab-case for files)
- api-reference.md
- user-guide.md
```

**Recommendation:**
```
Standardize on kebab-case for all documentation files:
- PHASE8_COMPLETE.md → phase8-complete.md
- API_REFERENCE.md → api-reference.md
- USER_GUIDE.md → user-guide.md
- GREMLIN_OLAP_ADVANCED_SCENARIOS.md → gremlin-olap-advanced-scenarios.md
```

**Impact:** Consistency, easier to remember, URL-friendly

---

### 2.2 Medium Priority Issues (Priority 2)

#### Issue #4: Banking Documentation Over-Crowding
**Severity:** MEDIUM  
**Location:** `docs/banking/`  
**Problem:** 27 files in single directory without sub-organization

**Current State:**
```
docs/banking/
├── ADVANCED_ANALYTICS_OLAP_GUIDE.md
├── API_REFERENCE.md
├── ARCHITECTURE.md
├── ENTERPRISE_ADVANCED_PATTERNS_PLAN.md
├── GREMLIN_OLAP_ADVANCED_SCENARIOS.md
├── PHASE5_IMPLEMENTATION_COMPLETE.md
├── PHASE5_VECTOR_AI_FOUNDATION.md
├── PHASE8_COMPLETE_ROADMAP.md
├── PHASE8_COMPLETE.md
├── [18 more files...]
└── README.md
```

**Recommendation:**
```
Organize into subdirectories:

docs/banking/
├── README.md                      # Overview and navigation
├── guides/                        # User and developer guides
│   ├── user-guide.md
│   ├── api-reference.md
│   ├── advanced-analytics-olap.md
│   └── gremlin-olap-scenarios.md
├── architecture/                  # Architecture documentation
│   ├── architecture.md
│   └── enterprise-patterns.md
├── implementation/                # Implementation documentation
│   ├── phases/
│   │   ├── phase5/
│   │   │   ├── implementation-complete.md
│   │   │   └── vector-ai-foundation.md
│   │   └── phase8/
│   │       ├── complete.md
│   │       ├── roadmap.md
│   │       ├── week3-complete.md
│   │       └── [other phase8 files]
│   └── deployment/
│       ├── production-deployment.md
│       └── production-verification.md
└── planning/                      # Planning documents
    └── synthetic-data-generator-plan.md
```

**Impact:** Better organization, easier navigation, scalable structure

---

#### Issue #5: Missing Documentation Index
**Severity:** MEDIUM  
**Location:** `docs/`  
**Problem:** No central index or navigation guide for documentation

**Recommendation:**
```
Create docs/INDEX.md with:
1. Documentation map
2. Quick links by role (developer, operator, architect)
3. Getting started paths
4. Search tips
```

**Example Structure:**
```markdown
# Documentation Index

## Quick Start
- [README](../README.md) - Project overview
- [QUICKSTART](../QUICKSTART.md) - Get started in 5 minutes
- [SETUP](SETUP.md) - Detailed setup guide

## By Role
### Developers
- [API Reference](banking/guides/api-reference.md)
- [Contributing](CONTRIBUTING.md)
- [Testing](TESTING.md)

### Operators
- [Deployment](DEPLOYMENT.md)
- [Monitoring](MONITORING.md)
- [Operations Runbook](operations/OPERATIONS_RUNBOOK.md)

### Architects
- [Architecture](ARCHITECTURE.md)
- [ADRs](architecture/)
- [Banking Architecture](banking/architecture/architecture.md)
```

**Impact:** Improved discoverability, better onboarding experience

---

#### Issue #6: Inconsistent README Placement
**Severity:** MEDIUM  
**Location:** Multiple directories  
**Problem:** Some subdirectories have README.md, others don't

**Current State:**
```
✅ Has README.md:
- banking/
- banking/data_generators/
- banking/notebooks/
- docs/api/
- docs/architecture/
- docs/banking/

❌ Missing README.md:
- banking/aml/
- banking/fraud/
- banking/data/
- banking/queries/
- banking/schema/
- src/python/
- tests/
```

**Recommendation:**
```
Add README.md to all major directories with:
1. Purpose and scope
2. Contents overview
3. Usage examples
4. Links to related documentation
```

**Impact:** Self-documenting codebase, easier navigation

---

### 2.3 Low Priority Issues (Priority 3)

#### Issue #7: Gemini-Generated Files in Root
**Severity:** LOW  
**Location:** `/` (root directory)  
**Problem:** Legacy Gemini-generated files cluttering root

**Files:**
```
- gemini_deploy_full_stack.sh
- gemini_generate_secure_env.sh
- gemini_remediation_JanusGraph_configurationFix.sh
- project_audit_and_plan_Gemini_.md
- remediation_plan_Gemini_.md
```

**Recommendation:**
```
Move to archive:
docs/archive/gemini/
├── deploy_full_stack.sh
├── generate_secure_env.sh
├── remediation_janusgraph_fix.sh
├── project_audit_and_plan.md
└── remediation_plan.md
```

**Impact:** Cleaner root directory, preserved history

---

#### Issue #8: Test Documentation Location
**Severity:** LOW  
**Location:** `tests/`  
**Problem:** No README.md explaining test structure and execution

**Recommendation:**
```
Create tests/README.md with:
1. Test structure overview
2. Running tests (unit, integration, performance)
3. Writing new tests
4. CI/CD integration
5. Coverage requirements
```

**Impact:** Better test documentation, easier for contributors

---

#### Issue #9: Scripts Documentation
**Severity:** LOW  
**Location:** `scripts/`  
**Problem:** No central documentation for script usage

**Recommendation:**
```
Create scripts/README.md with:
1. Script categories (backup, deployment, monitoring, etc.)
2. Usage examples for each script
3. Prerequisites and dependencies
4. Troubleshooting common issues
```

**Impact:** Improved script discoverability and usage

---

## 3. Best Practices Compliance

### 3.1 Industry Standards Comparison

| Standard | Current State | Compliance | Notes |
|----------|--------------|------------|-------|
| **Root Directory** | 35+ .md files | ⚠️ Partial | Should have max 5-7 key files |
| **Documentation Hub** | `docs/` exists | ✅ Good | Well-organized subdirectories |
| **Module Structure** | Clear separation | ✅ Excellent | Banking module exemplary |
| **Naming Conventions** | Mixed styles | ⚠️ Inconsistent | Need standardization |
| **README Coverage** | Partial | ⚠️ Incomplete | Missing in several directories |
| **Documentation Index** | None | ❌ Missing | Should have central index |
| **ADR Documentation** | Present | ✅ Good | Following ADR pattern |
| **API Documentation** | Comprehensive | ✅ Excellent | Well-structured |

### 3.2 Recommended Structure (Target State)

```
hcd-tarball-janusgraph/
├── README.md                      # ✅ Project overview
├── QUICKSTART.md                  # ✅ Quick start guide
├── LICENSE                        # ✅ License file
├── SECURITY.md                    # ✅ Security policy
├── CODE_OF_CONDUCT.md            # ✅ Code of conduct
├── .bob/                          # ✅ AI assistant config
├── .github/                       # ✅ GitHub workflows
├── banking/                       # ✅ Banking domain
│   ├── README.md
│   ├── aml/
│   │   └── README.md
│   ├── data/
│   │   └── README.md
│   ├── data_generators/
│   │   └── README.md
│   ├── fraud/
│   │   └── README.md
│   ├── notebooks/
│   │   └── README.md
│   ├── queries/
│   │   └── README.md
│   └── schema/
│       └── README.md
├── config/                        # ✅ Configuration
├── data/                          # ✅ Data storage
├── docker/                        # ✅ Docker configs
├── docs/                          # ✅ Documentation hub
│   ├── INDEX.md                  # 🆕 Central index
│   ├── README.md
│   ├── api/
│   ├── architecture/
│   ├── banking/
│   │   ├── README.md
│   │   ├── guides/              # 🆕 Organized guides
│   │   ├── architecture/        # 🆕 Architecture docs
│   │   ├── implementation/      # 🆕 Implementation docs
│   │   └── planning/            # 🆕 Planning docs
│   ├── compliance/
│   ├── development/
│   ├── implementation/           # 🆕 Project implementation
│   │   ├── phases/
│   │   ├── remediation/
│   │   └── audits/
│   ├── migration/
│   ├── operations/
│   ├── performance/
│   └── archive/                  # 🆕 Historical documents
│       └── gemini/
├── hcd-1.2.3/                    # ✅ Third-party binary
├── notebooks/                     # ✅ Jupyter notebooks
│   └── README.md
├── scripts/                       # ✅ Utility scripts
│   └── README.md
├── src/                          # ✅ Source code
│   └── README.md
└── tests/                        # ✅ Test suite
    └── README.md
```

---

## 4. Prioritized Remediation Plan

### Phase 1: Critical Cleanup (Week 1)

**Effort:** 4-6 hours  
**Impact:** HIGH

1. **Consolidate Root Documentation**
   ```bash
   # Create new directories
   mkdir -p docs/implementation/{phases,remediation,audits}
   mkdir -p docs/archive/gemini
   
   # Move audit reports
   mv AUDIT_REPORT*.md docs/implementation/audits/
   mv audit_comparison.md docs/implementation/audits/
   mv EXECUTIVE_SUMMARY.md docs/implementation/audits/
   
   # Move phase summaries
   mv PHASE*.md docs/implementation/phases/
   
   # Move remediation plans
   mv REMEDIATION_PLAN.md docs/implementation/remediation/
   mv remediation_plan_Gemini_.md docs/archive/gemini/
   
   # Move Gemini files
   mv gemini_*.sh docs/archive/gemini/
   mv project_audit_and_plan_Gemini_.md docs/archive/gemini/
   ```

2. **Consolidate Banking Documentation**
   ```bash
   # Remove duplicate directory
   mv banking/docs/* docs/banking/setup/
   rmdir banking/docs/
   
   # Update references
   find . -type f -name "*.md" -exec sed -i 's|banking/docs/|docs/banking/setup/|g' {} +
   find . -type f -name "*.py" -exec sed -i 's|banking/docs/|docs/banking/setup/|g' {} +
   ```

3. **Update All Documentation Links**
   - Run link checker
   - Fix broken references
   - Update navigation

**Deliverables:**
- ✅ Clean root directory (5-7 files only)
- ✅ Consolidated banking docs
- ✅ All links working

---

### Phase 2: Organization Improvements (Week 2)

**Effort:** 6-8 hours  
**Impact:** MEDIUM

1. **Organize Banking Documentation**
   ```bash
   cd docs/banking
   mkdir -p guides architecture implementation/{phases/phase5,phases/phase8,deployment} planning
   
   # Move files to appropriate subdirectories
   mv *-guide.md guides/
   mv *-reference.md guides/
   mv *architecture*.md architecture/
   mv *PHASE*.md implementation/phases/
   mv *deployment*.md implementation/deployment/
   mv *plan*.md planning/
   ```

2. **Create Documentation Index**
   - Create `docs/INDEX.md`
   - Add role-based navigation
   - Include search tips

3. **Add Missing READMEs**
   ```bash
   # Create README templates
   for dir in banking/aml banking/fraud banking/data src/python tests; do
     cat > $dir/README.md << 'EOF'
   # [Directory Name]
   
   ## Purpose
   [Brief description]
   
   ## Contents
   [List of key files/subdirectories]
   
   ## Usage
   [Basic usage examples]
   
   ## Documentation
   [Links to related docs]
   EOF
   done
   ```

**Deliverables:**
- ✅ Organized banking documentation
- ✅ Central documentation index
- ✅ README in all major directories

---

### Phase 3: Standardization (Week 3)

**Effort:** 4-6 hours  
**Impact:** MEDIUM

1. **Standardize File Naming**
   ```bash
   # Rename files to kebab-case
   cd docs/banking
   rename 's/_/-/g' *.md
   rename 's/([A-Z])/-\L$1/g' *.md
   
   # Update all references
   find . -type f \( -name "*.md" -o -name "*.py" \) -exec sed -i 's/PHASE8_COMPLETE/phase8-complete/g' {} +
   ```

2. **Create Documentation Standards**
   - Create `docs/DOCUMENTATION_STANDARDS.md`
   - Define naming conventions
   - Define structure guidelines
   - Define content templates

3. **Update AGENTS.md**
   - Add documentation organization rules
   - Add file naming conventions
   - Add structure guidelines

**Deliverables:**
- ✅ Consistent file naming
- ✅ Documentation standards guide
- ✅ Updated AGENTS.md

---

### Phase 4: Enhancement (Week 4)

**Effort:** 2-4 hours  
**Impact:** LOW

1. **Create Script Documentation**
   - Add `scripts/README.md`
   - Document each script category
   - Add usage examples

2. **Create Test Documentation**
   - Add `tests/README.md`
   - Document test structure
   - Add contribution guidelines

3. **Archive Historical Documents**
   - Move old documents to archive
   - Add archive README
   - Update references

**Deliverables:**
- ✅ Complete script documentation
- ✅ Complete test documentation
- ✅ Clean archive structure

---

## 5. Implementation Checklist

### Pre-Implementation
- [ ] Backup current documentation structure
- [ ] Create git branch: `docs/structure-reorganization`
- [ ] Notify team of upcoming changes
- [ ] Review and approve reorganization plan

### Phase 1: Critical Cleanup
- [ ] Create new directory structure
- [ ] Move audit reports to `docs/implementation/audits/`
- [ ] Move phase summaries to `docs/implementation/phases/`
- [ ] Move remediation plans to `docs/implementation/remediation/`
- [ ] Move Gemini files to `docs/archive/gemini/`
- [ ] Consolidate banking documentation
- [ ] Update all documentation links
- [ ] Run link checker and fix broken links
- [ ] Test documentation navigation
- [ ] Commit changes: "docs: consolidate root documentation"

### Phase 2: Organization Improvements
- [ ] Create banking documentation subdirectories
- [ ] Move files to appropriate subdirectories
- [ ] Create `docs/INDEX.md`
- [ ] Add README.md to all major directories
- [ ] Update navigation in existing docs
- [ ] Test documentation discoverability
- [ ] Commit changes: "docs: organize banking documentation"

### Phase 3: Standardization
- [ ] Rename files to kebab-case
- [ ] Update all file references
- [ ] Create `docs/DOCUMENTATION_STANDARDS.md`
- [ ] Update `AGENTS.md` with documentation rules
- [ ] Run tests to ensure no broken imports
- [ ] Commit changes: "docs: standardize naming conventions"

### Phase 4: Enhancement
- [ ] Create `scripts/README.md`
- [ ] Create `tests/README.md`
- [ ] Add archive documentation
- [ ] Final link check
- [ ] Final navigation test
- [ ] Commit changes: "docs: add missing documentation"

### Post-Implementation
- [ ] Merge branch to main
- [ ] Update team documentation
- [ ] Update onboarding materials
- [ ] Monitor for issues
- [ ] Gather feedback

---

## 6. Metrics and Success Criteria

### Current State Metrics
- **Root .md files:** 35+
- **Documentation directories:** 8
- **Banking docs files:** 27 (single directory)
- **Missing READMEs:** 7+ directories
- **Naming consistency:** ~60%
- **Documentation index:** None

### Target State Metrics
- **Root .md files:** 5-7 (86% reduction)
- **Documentation directories:** 12+ (organized)
- **Banking docs files:** 27 (organized into 4 subdirectories)
- **Missing READMEs:** 0
- **Naming consistency:** 100%
- **Documentation index:** Complete

### Success Criteria
1. ✅ Root directory has ≤7 .md files
2. ✅ All documentation follows kebab-case naming
3. ✅ Every major directory has README.md
4. ✅ Central documentation index exists
5. ✅ No broken documentation links
6. ✅ Banking docs organized into subdirectories
7. ✅ All historical files archived appropriately
8. ✅ Documentation standards documented
9. ✅ AGENTS.md updated with structure rules
10. ✅ Team can navigate documentation easily

---

## 7. Risk Assessment

### Low Risk
- Moving files (git preserves history)
- Creating new directories
- Adding README files

### Medium Risk
- Updating file references (automated with sed)
- Renaming files (may break some links)

### Mitigation Strategies
1. **Backup:** Create git branch before changes
2. **Testing:** Run link checker after each phase
3. **Automation:** Use scripts for bulk operations
4. **Validation:** Test navigation after each phase
5. **Rollback:** Keep branch until verified working

---

## 8. Maintenance Guidelines

### Ongoing Practices
1. **New Documentation:** Always place in appropriate subdirectory
2. **Naming:** Use kebab-case for all new files
3. **READMEs:** Add README.md to new directories
4. **Links:** Use relative links, test before committing
5. **Index:** Update `docs/INDEX.md` for major additions

### Quarterly Reviews
- Review documentation structure
- Check for orphaned files
- Update documentation index
- Verify all links working
- Gather user feedback

### Annual Audits
- Comprehensive structure review
- Archive outdated documentation
- Update standards as needed
- Benchmark against industry practices

---

## 9. Conclusion

The project has a **solid foundation** with clear module separation and comprehensive documentation. The primary issues are:

1. **Root directory clutter** (35+ .md files)
2. **Inconsistent documentation hierarchy** (banking/docs vs docs/banking)
3. **Lack of organization** in banking documentation (27 files in one directory)
4. **Missing documentation index** for navigation
5. **Inconsistent naming conventions** (mixed case styles)

The proposed 4-phase remediation plan will:
- ✅ Reduce root .md files by 86%
- ✅ Consolidate duplicate documentation
- ✅ Organize banking docs into logical subdirectories
- ✅ Standardize naming conventions
- ✅ Add missing READMEs
- ✅ Create central documentation index

**Estimated Total Effort:** 16-24 hours over 4 weeks  
**Expected Impact:** HIGH - Significantly improved documentation discoverability and maintainability

---

## 10. References

### Industry Best Practices
- [GitHub Documentation Best Practices](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)
- [Google Documentation Style Guide](https://developers.google.com/style)
- [Write the Docs - Documentation Guide](https://www.writethedocs.org/guide/)
- [Divio Documentation System](https://documentation.divio.com/)

### Project-Specific Documents
- [`AGENTS.md`](../AGENTS.md) - Project-specific patterns
- [`docs/CONTRIBUTING.md`](CONTRIBUTING.md) - Contribution guidelines
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) - System architecture

---

**Review Status:** ✅ COMPLETE  
**Next Action:** Review and approve remediation plan  
**Owner:** Project Lead  
**Due Date:** 2026-02-04
