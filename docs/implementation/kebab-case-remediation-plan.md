# Kebab-Case Naming Remediation Plan

**Date:** 2026-02-11
**Status:** Planning
**Priority:** P2 - Documentation Standards Compliance

---

## Executive Summary

This document provides a comprehensive plan to enforce kebab-case naming conventions across all documentation files, as mandated by [`docs/documentation-standards.md`](../documentation-standards.md).

**Current State:** 100+ files violate kebab-case naming standards
**Target State:** All documentation files follow kebab-case (except approved exceptions)
**Estimated Effort:** 4-6 hours (automated + manual verification)

---

## Table of Contents

1. [Naming Standards](#naming-standards)
2. [Files Requiring Renaming](#files-requiring-renaming)
3. [Allowed Exceptions](#allowed-exceptions)
4. [Renaming Strategy](#renaming-strategy)
5. [Impact Analysis](#impact-analysis)
6. [Implementation Plan](#implementation-plan)
7. [Validation](#validation)

---

## Naming Standards

### Kebab-Case Rules

**Format:** `lowercase-words-separated-by-hyphens.md`

**Examples:**
- ✅ `user-guide.md`
- ✅ `api-reference.md`
- ✅ `phase-8-complete.md`
- ✅ `week-1-summary-2026-02-11.md`
- ❌ `USER_GUIDE.md` (UPPERCASE)
- ❌ `ApiReference.md` (PascalCase)
- ❌ `user_guide.md` (snake_case)
- ❌ `PHASE8_COMPLETE.md` (UPPERCASE with underscores)

### Date Format in Filenames

When including dates in filenames:
- ✅ `audit-report-2026-01-30.md`
- ✅ `week-1-summary-2026-02-11.md`
- ❌ `AUDIT_REPORT_2026-01-30.md`

---

## Files Requiring Renaming

### Root Directory (3 files)

| Current Name | New Name | Reason |
|--------------|----------|--------|
| `CODE_QUALITY_BEST_PRACTICES_REVIEW_2026-02-11.md` | `code-quality-best-practices-review-2026-02-11.md` | UPPERCASE violation |
| `CODE_QUALITY_IMPLEMENTATION_PLAN_2026-02-11.md` | `code-quality-implementation-plan-2026-02-11.md` | UPPERCASE violation |
| `CODEBASE_REVIEW_2026-02-11.md` | `codebase-review-2026-02-11.md` | UPPERCASE violation |
| `SECURITY_REMEDIATION_PLAN_2026-02-11.md` | `security-remediation-plan-2026-02-11.md` | UPPERCASE violation |
| `TOOLING_STANDARDS_UPDATE_2026-02-11.md` | `tooling-standards-update-2026-02-11.md` | UPPERCASE violation |

### docs/ Directory (3 files)

| Current Name | New Name | Reason |
|--------------|----------|--------|
| `BANKING_USE_CASES_TECHNICAL_SPEC.md` | `banking-use-cases-technical-spec.md` | UPPERCASE violation |
| `BANKING_USE_CASES_TECHNICAL_SPEC_COMPLETE.md` | `banking-use-cases-technical-spec-complete.md` | UPPERCASE violation |
| `DEMO_SETUP_GUIDE.md` | `demo-setup-guide.md` | UPPERCASE violation |
| `DOCS_OPTIMIZATION_PLAN.md` | `docs-optimization-plan.md` | UPPERCASE violation |

### docs/banking/ Directory (4 files)

| Current Name | New Name | Reason |
|--------------|----------|--------|
| `ENTERPRISE_ADVANCED_PATTERNS_PLAN.md` | `enterprise-advanced-patterns-plan.md` | UPPERCASE violation |
| `PHASE5_IMPLEMENTATION_COMPLETE.md` | `phase-5-implementation-complete.md` | UPPERCASE + number format |
| `PHASE5_VECTOR_AI_FOUNDATION.md` | `phase-5-vector-ai-foundation.md` | UPPERCASE + number format |
| `USER_GUIDE.md` | `user-guide.md` | UPPERCASE violation |

**Note:** `user-guide.md` already exists in this directory, so `USER_GUIDE.md` is a duplicate that should be removed after content merge.

### docs/implementation/ Directory (60+ files)

| Current Name | New Name | Reason |
|--------------|----------|--------|
| `BACKLOG.md` | `backlog.md` | UPPERCASE violation |
| `CODEBASE_REVIEW_2026-02-11_FINAL.md` | `codebase-review-2026-02-11-final.md` | UPPERCASE violation |
| `DOCS_OPTIMIZATION_COMPLETE.md` | `docs-optimization-complete.md` | UPPERCASE violation |
| `DOCUMENTATION_LINK_VALIDATION.md` | `documentation-link-validation.md` | UPPERCASE violation |
| `EXCEPTION_HANDLING_AUDIT.md` | `exception-handling-audit.md` | UPPERCASE violation |
| `PHASE1_SECURITY_FIXES_COMPLETE.md` | `phase-1-security-fixes-complete.md` | UPPERCASE + number format |
| `PHASE1_WEEK1_STRUCTURE_REORGANIZATION.md` | `phase-1-week-1-structure-reorganization.md` | UPPERCASE + number format |
| `PHASE2_COMPLETION_SUMMARY.md` | `phase-2-completion-summary.md` | UPPERCASE + number format |
| `PHASE2_SECURITY_HARDENING_COMPLETE.md` | `phase-2-security-hardening-complete.md` | UPPERCASE + number format |
| `PHASE2_WEEK2_STRUCTURE_ORGANIZATION.md` | `phase-2-week-2-structure-organization.md` | UPPERCASE + number format |
| `PHASE3_COMPLETION_SUMMARY.md` | `phase-3-completion-summary.md` | UPPERCASE + number format |
| `PHASE3_QUICK_START.md` | `phase-3-quick-start.md` | UPPERCASE + number format |
| `PHASE3_WEEK3_STANDARDIZATION.md` | `phase-3-week-3-standardization.md` | UPPERCASE + number format |
| `PHASE4_WEEK4_ENHANCEMENT.md` | `phase-4-week-4-enhancement.md` | UPPERCASE + number format |
| `PRODUCTION_READINESS_AUDIT_2026.md` | `production-readiness-audit-2026.md` | UPPERCASE violation |
| `PRODUCTION_READINESS_AUDIT.md` | `production-readiness-audit.md` | UPPERCASE violation |
| `PRODUCTION_READINESS_STATUS_FINAL.md` | `production-readiness-status-final.md` | UPPERCASE violation |
| `PRODUCTION_READINESS_STATUS.md` | `production-readiness-status.md` | UPPERCASE violation |
| `REVIEW_CONFRONTATION_ANALYSIS_2026-02-11.md` | `review-confrontation-analysis-2026-02-11.md` | UPPERCASE violation |
| `WEEK1_COMPLETE_SUMMARY_2026-02-11.md` | `week-1-complete-summary-2026-02-11.md` | UPPERCASE + number format |
| `WEEK1_PROGRESS_SUMMARY_2026-02-11.md` | `week-1-progress-summary-2026-02-11.md` | UPPERCASE + number format |
| `WEEK2_ANALYTICS_STREAMING_TESTING_PLAN.md` | `week-2-analytics-streaming-testing-plan.md` | UPPERCASE + number format |
| `WEEK2_DAY8_COMPLETE_SUMMARY.md` | `week-2-day-8-complete-summary.md` | UPPERCASE + number format |
| `WEEK2_DAY9_COMPLETE_SUMMARY.md` | `week-2-day-9-complete-summary.md` | UPPERCASE + number format |
| `WEEK2_DAY10_COMPLETE_SUMMARY.md` | `week-2-day-10-complete-summary.md` | UPPERCASE + number format |
| `WEEK2_DAY11_COMPLETE_SUMMARY.md` | `week-2-day-11-complete-summary.md` | UPPERCASE + number format |
| `WEEK2_DAY12_COMPLETE_SUMMARY.md` | `week-2-day-12-complete-summary.md` | UPPERCASE + number format |
| `WEEK2_DAYS_6-7_PROGRESS_SUMMARY.md` | `week-2-days-6-7-progress-summary.md` | UPPERCASE + number format |
| `WEEK2_DAYS_8-12_IMPLEMENTATION_GUIDE.md` | `week-2-days-8-12-implementation-guide.md` | UPPERCASE + number format |
| `WEEK2_IMPLEMENTATION_SCOPE_ANALYSIS.md` | `week-2-implementation-scope-analysis.md` | UPPERCASE + number format |
| `WEEK2_NEXT_STEPS.md` | `week-2-next-steps.md` | UPPERCASE + number format |
| `WEEK3_COMPLETE_SUMMARY.md` | `week-3-complete-summary.md` | UPPERCASE + number format |
| `WEEK3_DAY17_IMPLEMENTATION_PLAN.md` | `week-3-day-17-implementation-plan.md` | UPPERCASE + number format |
| `WEEK3_DAY17_SUMMARY.md` | `week-3-day-17-summary.md` | UPPERCASE + number format |
| `WEEK3_DAY18_IMPLEMENTATION_PLAN.md` | `week-3-day-18-implementation-plan.md` | UPPERCASE + number format |
| `WEEK3_DAY18_SUMMARY.md` | `week-3-day-18-summary.md` | UPPERCASE + number format |
| `WEEK3_DAYS13-15_SUMMARY.md` | `week-3-days-13-15-summary.md` | UPPERCASE + number format |
| `WEEK3_IMPLEMENTATION_PLAN.md` | `week-3-implementation-plan.md` | UPPERCASE + number format |
| `WEEK4_COMPLETE_SUMMARY.md` | `week-4-complete-summary.md` | UPPERCASE + number format |
| `WEEK4_DAY19_CODE_QUALITY_REPORT.md` | `week-4-day-19-code-quality-report.md` | UPPERCASE + number format |
| `WEEK4_DAY19_IMPLEMENTATION_PLAN.md` | `week-4-day-19-implementation-plan.md` | UPPERCASE + number format |
| `WEEK4_DAY19_SUMMARY.md` | `week-4-day-19-summary.md` | UPPERCASE + number format |
| `WEEK4_DAY20_IMPLEMENTATION_PLAN.md` | `week-4-day-20-implementation-plan.md` | UPPERCASE + number format |
| `WEEK4_DAY20_SECURITY_AUDIT_REPORT.md` | `week-4-day-20-security-audit-report.md` | UPPERCASE + number format |
| `WEEK4_DAY20_SUMMARY.md` | `week-4-day-20-summary.md` | UPPERCASE + number format |
| `WEEK4_DAY21_IMPLEMENTATION_PLAN.md` | `week-4-day-21-implementation-plan.md` | UPPERCASE + number format |
| `WEEK4_DAY21_PERFORMANCE_REPORT.md` | `week-4-day-21-performance-report.md` | UPPERCASE + number format |
| `WEEK4_DAY21_SUMMARY.md` | `week-4-day-21-summary.md` | UPPERCASE + number format |
| `WEEK4_DAY22_DOCUMENTATION_REPORT.md` | `week-4-day-22-documentation-report.md` | UPPERCASE + number format |
| `WEEK4_DAY22_IMPLEMENTATION_PLAN.md` | `week-4-day-22-implementation-plan.md` | UPPERCASE + number format |
| `WEEK4_DAY22_SUMMARY.md` | `week-4-day-22-summary.md` | UPPERCASE + number format |
| `WEEK4_DAY23_PRODUCTION_READINESS_REPORT.md` | `week-4-day-23-production-readiness-report.md` | UPPERCASE + number format |
| `WEEK4_DAY23_SUMMARY.md` | `week-4-day-23-summary.md` | UPPERCASE + number format |
| `WEEK4_IMPLEMENTATION_PLAN.md` | `week-4-implementation-plan.md` | UPPERCASE + number format |
| `WEEK5_DAY25_SUMMARY.md` | `week-5-day-25-summary.md` | UPPERCASE + number format |
| `WEEK5_PRODUCTION_DEPLOYMENT_PLAN.md` | `week-5-production-deployment-plan.md` | UPPERCASE + number format |
| `WEEK5_PRODUCTION_READY_SUMMARY.md` | `week-5-production-ready-summary.md` | UPPERCASE + number format |
| `WEEK6_ENHANCEMENT_PLAN.md` | `week-6-enhancement-plan.md` | UPPERCASE + number format |
| `WEEK6_EXECUTION_PLAN.md` | `week-6-execution-plan.md` | UPPERCASE + number format |

### docs/implementation/audits/ Directory (10+ files)

| Current Name | New Name | Reason |
|--------------|----------|--------|
| `COMPREHENSIVE_PROJECT_AUDIT_2026-01-30.md` | `comprehensive-project-audit-2026-01-30.md` | UPPERCASE violation |
| `DATA_SCRIPTS_SAI_AUDIT_2026-01-30.md` | `data-scripts-sai-audit-2026-01-30.md` | UPPERCASE violation |
| `FINAL_CROSS_AUDIT_RECONCILIATION_2026-01-30.md` | `final-cross-audit-reconciliation-2026-01-30.md` | UPPERCASE violation |
| `REMEDIATION_PLAN_2026-01-30.md` | `remediation-plan-2026-01-30.md` | UPPERCASE violation |
| `SECOND_AUDIT_SERVICES_NOTEBOOKS_2026-01-30.md` | `second-audit-services-notebooks-2026-01-30.md` | UPPERCASE violation |
| `TECHNICAL_CONFRONTATION_ANALYSIS_2026-01-30.md` | `technical-confrontation-analysis-2026-01-30.md` | UPPERCASE violation |
| `WORKFLOW_PIP_AUDIT_2026-02-11.md` | `workflow-pip-audit-2026-02-11.md` | UPPERCASE violation |

### docs/implementation/phases/ Directory (20+ files)

| Current Name | New Name | Reason |
|--------------|----------|--------|
| `PHASE2_WEEK2_COMPLETE_SUMMARY.md` | `phase-2-week-2-complete-summary.md` | UPPERCASE + number format |
| `PHASE8_COMPLETE.md` | `phase-8-complete.md` | UPPERCASE + number format |
| `PHASE8_COMPLETE_ROADMAP.md` | `phase-8-complete-roadmap.md` | UPPERCASE + number format |

### docs/implementation/remediation/ Directory (10+ files)

| Current Name | New Name | Reason |
|--------------|----------|--------|
| `AUDIT_REMEDIATION_COMPLETE.md` | `audit-remediation-complete.md` | UPPERCASE violation |
| `DEPLOYMENT_DOCUMENTATION_UPDATE.md` | `deployment-documentation-update.md` | UPPERCASE violation |
| `DOCKER_COMPOSE_BUILD_CONTEXT_FIX.md` | `docker-compose-build-context-fix.md` | UPPERCASE violation |
| `NETWORK_ISOLATION_ANALYSIS.md` | `network-isolation-analysis.md` | UPPERCASE violation |

---

## Allowed Exceptions

Per [`docs/documentation-standards.md`](../documentation-standards.md), the following files are **EXEMPT** from kebab-case requirements:

### Root-Level Standard Files (7 files)
- ✅ `README.md` - Standard convention
- ✅ `LICENSE` - Standard convention
- ✅ `CHANGELOG.md` - Standard convention
- ✅ `CONTRIBUTING.md` - Standard convention
- ✅ `CODE_OF_CONDUCT.md` - Standard convention
- ✅ `SECURITY.md` - Standard convention
- ✅ `AGENTS.md` - Project-specific standard (documented in rules)

### Directory README Files
- ✅ All `README.md` files in subdirectories

**Total Exempt Files:** ~50+ (all README.md files across project)

---

## Renaming Strategy

### Phase 1: Automated Renaming (2 hours)

1. **Create Renaming Script**
   - Generate `git mv` commands for all files
   - Preserve git history
   - Handle special characters safely

2. **Execute Renames**
   - Run script in test branch first
   - Verify no file conflicts
   - Commit with descriptive message

### Phase 2: Reference Updates (2 hours)

1. **Update Internal Links**
   - Search for all markdown links to renamed files
   - Update relative paths
   - Update absolute paths

2. **Update Code References**
   - Search Python code for hardcoded paths
   - Update import statements if needed
   - Update configuration files

3. **Update Documentation Indexes**
   - Update `docs/index.md`
   - Update all `README.md` files
   - Update table of contents

### Phase 3: Validation (1 hour)

1. **Link Validation**
   - Run markdown link checker
   - Verify all internal links work
   - Check external links

2. **Build Verification**
   - Test documentation builds (if using MkDocs)
   - Verify no broken references
   - Check CI/CD pipelines

### Phase 4: Documentation (1 hour)

1. **Update Standards**
   - Document completed remediation
   - Update examples in standards doc
   - Add validation script to CI

2. **Create Migration Guide**
   - Document old→new mappings
   - Provide search/replace patterns
   - Add to CHANGELOG.md

---

## Impact Analysis

### High Impact Areas

1. **Documentation Links** (94+ links identified)
   - Internal markdown links
   - Cross-references between docs
   - Table of contents entries

2. **CI/CD Workflows** (Low risk)
   - GitHub Actions may reference docs
   - Build scripts may check for files
   - Deployment scripts may copy docs

3. **Code References** (Low risk)
   - Python code rarely references docs directly
   - Configuration files may have paths
   - Scripts may generate doc links

### Low Impact Areas

1. **External Links** (No impact)
   - External sites don't link to our docs
   - No public documentation site yet

2. **User Workflows** (Minimal impact)
   - Users access docs through index
   - README files guide navigation
   - Search still works after rename

---

## Implementation Plan

### Step 1: Preparation (30 min)

```bash
# Create feature branch
git checkout -b docs/kebab-case-remediation

# Create backup
git tag backup-before-kebab-case-remediation

# Generate file list
find . -name "*.md" -type f | grep -E '[A-Z_]{2,}' > files-to-rename.txt
```

### Step 2: Create Renaming Script (30 min)

Create `scripts/documentation/rename-to-kebab-case.sh`:

```bash
#!/bin/bash
# Rename documentation files to kebab-case

set -e

# Function to convert to kebab-case
to_kebab_case() {
    echo "$1" | \
        sed 's/_/-/g' | \
        sed 's/\([A-Z]\)/-\1/g' | \
        sed 's/^-//' | \
        tr '[:upper:]' '[:lower:]' | \
        sed 's/--/-/g'
}

# Root directory files
git mv CODE_QUALITY_BEST_PRACTICES_REVIEW_2026-02-11.md code-quality-best-practices-review-2026-02-11.md
git mv CODE_QUALITY_IMPLEMENTATION_PLAN_2026-02-11.md code-quality-implementation-plan-2026-02-11.md
git mv CODEBASE_REVIEW_2026-02-11.md codebase-review-2026-02-11.md
git mv SECURITY_REMEDIATION_PLAN_2026-02-11.md security-remediation-plan-2026-02-11.md
git mv TOOLING_STANDARDS_UPDATE_2026-02-11.md tooling-standards-update-2026-02-11.md

# docs/ directory
cd docs
git mv BANKING_USE_CASES_TECHNICAL_SPEC.md banking-use-cases-technical-spec.md
git mv BANKING_USE_CASES_TECHNICAL_SPEC_COMPLETE.md banking-use-cases-technical-spec-complete.md
git mv DEMO_SETUP_GUIDE.md demo-setup-guide.md
git mv DOCS_OPTIMIZATION_PLAN.md docs-optimization-plan.md

# docs/banking/ directory
cd banking
git mv ENTERPRISE_ADVANCED_PATTERNS_PLAN.md enterprise-advanced-patterns-plan.md
git mv PHASE5_IMPLEMENTATION_COMPLETE.md phase-5-implementation-complete.md
git mv PHASE5_VECTOR_AI_FOUNDATION.md phase-5-vector-ai-foundation.md
# Note: USER_GUIDE.md needs content merge with user-guide.md

# Continue for all other directories...
```

### Step 3: Update References (1 hour)

Create `scripts/documentation/update-doc-references.sh`:

```bash
#!/bin/bash
# Update all references to renamed files

set -e

# Update markdown links
find . -name "*.md" -type f -exec sed -i '' \
    -e 's|CODE_QUALITY_BEST_PRACTICES_REVIEW_2026-02-11\.md|code-quality-best-practices-review-2026-02-11.md|g' \
    -e 's|CODEBASE_REVIEW_2026-02-11\.md|codebase-review-2026-02-11.md|g' \
    -e 's|PHASE5_IMPLEMENTATION_COMPLETE\.md|phase-5-implementation-complete.md|g' \
    {} +

# Update Python code references (if any)
find . -name "*.py" -type f -exec sed -i '' \
    -e 's|"CODEBASE_REVIEW_2026-02-11\.md"|"codebase-review-2026-02-11.md"|g' \
    {} +

# Update configuration files
find . -name "*.yml" -o -name "*.yaml" -type f -exec sed -i '' \
    -e 's|PHASE5_IMPLEMENTATION_COMPLETE\.md|phase-5-implementation-complete.md|g' \
    {} +
```

### Step 4: Validation (30 min)

```bash
# Check for broken links
npm install -g markdown-link-check
find docs -name "*.md" -exec markdown-link-check {} \;

# Check for remaining UPPERCASE files
find docs -name "*.md" -type f | grep -E '[A-Z_]{2,}' || echo "✅ All files renamed"

# Verify git history preserved
git log --follow docs/banking/phase-5-implementation-complete.md
```

### Step 5: Documentation (30 min)

1. Update `CHANGELOG.md`:
```markdown
## [Unreleased]

### Changed
- **BREAKING:** Renamed 100+ documentation files to kebab-case format
  - See `docs/implementation/KEBAB_CASE_REMEDIATION_PLAN.md` for mappings
  - All internal links updated automatically
  - Git history preserved via `git mv`
```

2. Update `docs/documentation-standards.md`:
```markdown
## Enforcement

As of 2026-02-11, all documentation files follow kebab-case naming.
A validation script runs in CI to prevent future violations.
```

3. Create `docs/implementation/KEBAB_CASE_MIGRATION_GUIDE.md` with old→new mappings

---

## Validation

### Automated Checks

Create `.github/workflows/validate-doc-naming.yml`:

```yaml
name: Validate Documentation Naming

on:
  pull_request:
    paths:
      - 'docs/**/*.md'
      - '*.md'

jobs:
  check-naming:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check for UPPERCASE violations
        run: |
          # Find files violating kebab-case (excluding exceptions)
          VIOLATIONS=$(find docs -name "*.md" -type f | \
            grep -v "README.md" | \
            grep -E '[A-Z_]{2,}' || true)
          
          if [ -n "$VIOLATIONS" ]; then
            echo "❌ Found files violating kebab-case:"
            echo "$VIOLATIONS"
            exit 1
          fi
          
          echo "✅ All documentation files follow kebab-case"
```

### Manual Verification Checklist

- [ ] All files renamed successfully
- [ ] Git history preserved (`git log --follow`)
- [ ] No broken internal links
- [ ] Documentation builds successfully
- [ ] CI/CD pipelines pass
- [ ] README files updated
- [ ] Index files updated
- [ ] CHANGELOG.md updated
- [ ] Migration guide created
- [ ] Validation script added to CI

---

## Rollback Plan

If issues arise during implementation:

```bash
# Restore from backup tag
git reset --hard backup-before-kebab-case-remediation

# Or revert specific commits
git revert <commit-hash>

# Or restore specific files
git checkout HEAD~1 -- docs/banking/PHASE5_IMPLEMENTATION_COMPLETE.md
```

---

## Timeline

| Phase | Duration | Completion Date |
|-------|----------|-----------------|
| Preparation | 30 min | Day 1 Morning |
| Script Creation | 30 min | Day 1 Morning |
| Automated Renaming | 1 hour | Day 1 Afternoon |
| Reference Updates | 2 hours | Day 1 Afternoon |
| Validation | 1 hour | Day 2 Morning |
| Documentation | 1 hour | Day 2 Morning |
| **Total** | **6 hours** | **2 days** |

---

## Success Criteria

1. ✅ All documentation files follow kebab-case (except approved exceptions)
2. ✅ No broken internal links
3. ✅ Git history preserved for all renamed files
4. ✅ CI/CD validation prevents future violations
5. ✅ Migration guide documents all changes
6. ✅ CHANGELOG.md updated
7. ✅ All tests pass
8. ✅ Documentation builds successfully

---

## References

- [`docs/documentation-standards.md`](../documentation-standards.md) - Official naming standards
- [`docs/implementation/DOCS_OPTIMIZATION_COMPLETE.md`](DOCS_OPTIMIZATION_COMPLETE.md) - Previous reorganization
- [`docs/implementation/DOCUMENTATION_LINK_VALIDATION.md`](DOCUMENTATION_LINK_VALIDATION.md) - Link validation results

---

**Next Steps:**

1. Review and approve this plan
2. Create feature branch
3. Execute renaming script
4. Update references
5. Validate changes
6. Merge to main

**Estimated Completion:** 2026-02-13