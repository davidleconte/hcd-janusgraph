# Kebab-Case Remediation Implementation Plan

**Date:** 2026-02-12  
**Version:** 1.0  
**Status:** Ready for Execution  
**Author:** David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

---

## Executive Summary

This document provides a comprehensive plan for applying kebab-case naming conventions to all documentation files in the project, including an automated script specification, dry-run execution strategy, and validation procedures.

**Scope:** 38 documentation files requiring renaming  
**Estimated Time:** 2-3 hours (automated) or 6-8 hours (manual)  
**Risk Level:** MEDIUM (mitigated by dry-run and backups)

---

## Table of Contents

1. [Files Requiring Renaming](#1-files-requiring-renaming)
2. [Automated Script Specification](#2-automated-script-specification)
3. [Dry-Run Execution Strategy](#3-dry-run-execution-strategy)
4. [Link Update Strategy](#4-link-update-strategy)
5. [Validation Procedures](#5-validation-procedures)
6. [Rollback Plan](#6-rollback-plan)
7. [Execution Checklist](#7-execution-checklist)

---

## 1. Files Requiring Renaming

### 1.1 Root Level Documentation (4 files)

| Current Name | New Name | Priority |
|--------------|----------|----------|
| `docs/BANKING_USE_CASES_TECHNICAL_SPEC.md` | `docs/banking-use-cases-technical-spec.md` | P0 |
| `docs/BANKING_USE_CASES_TECHNICAL_SPEC_COMPLETE.md` | `docs/banking-use-cases-technical-spec-complete.md` | P0 |
| `docs/TECHNICAL_SPECIFICATIONS.md` | `docs/technical-specifications.md` | P0 |
| `docs/DOCS_OPTIMIZATION_PLAN.md` | `docs/docs-optimization-plan.md` | P1 |

### 1.2 Banking Directory (4 files)

| Current Name | New Name | Priority |
|--------------|----------|----------|
| `docs/banking/PHASE5_VECTOR_AI_FOUNDATION.md` | `docs/banking/phase5-vector-ai-foundation.md` | P0 |
| `docs/banking/PHASE5_IMPLEMENTATION_COMPLETE.md` | `docs/banking/phase5-implementation-complete.md` | P0 |
| `docs/banking/ENTERPRISE_ADVANCED_PATTERNS_PLAN.md` | `docs/banking/enterprise-advanced-patterns-plan.md` | P1 |
| `docs/banking/USER_GUIDE.md` | **DUPLICATE** - Delete (user-guide.md exists) | P0 |

### 1.3 Implementation Directory (20 files)

| Current Name | New Name | Priority |
|--------------|----------|----------|
| `docs/implementation/EXCEPTION_HANDLING_AUDIT.md` | `docs/implementation/exception-handling-audit.md` | P1 |
| `docs/implementation/PHASE2_WEEK2_STRUCTURE_ORGANIZATION.md` | `docs/implementation/phase2-week2-structure-organization.md` | P2 |
| `docs/implementation/PHASE3_QUICK_START.md` | `docs/implementation/phase3-quick-start.md` | P2 |
| `docs/implementation/PHASE3_WEEK3_STANDARDIZATION.md` | `docs/implementation/phase3-week3-standardization.md` | P2 |
| `docs/implementation/PRODUCTION_READINESS_AUDIT_2026.md` | `docs/implementation/production-readiness-audit-2026.md` | P0 |
| `docs/implementation/PRODUCTION_READINESS_STATUS_FINAL.md` | `docs/implementation/production-readiness-status-final.md` | P0 |
| `docs/implementation/REVIEW_CONFRONTATION_ANALYSIS_2026-02-11.md` | `docs/implementation/review-confrontation-analysis-2026-02-11.md` | P1 |
| `docs/implementation/WEEK1_PROGRESS_SUMMARY_2026-02-11.md` | `docs/implementation/week1-progress-summary-2026-02-11.md` | P1 |
| `docs/implementation/WEEK2_DAYS_8-12_IMPLEMENTATION_GUIDE.md` | `docs/implementation/week2-days-8-12-implementation-guide.md` | P2 |
| `docs/implementation/WEEK3_DAYS13-15_SUMMARY.md` | `docs/implementation/week3-days13-15-summary.md` | P2 |
| `docs/implementation/WEEK3_IMPLEMENTATION_PLAN.md` | `docs/implementation/week3-implementation-plan.md` | P2 |
| `docs/implementation/WEEK4_DAY19_IMPLEMENTATION_PLAN.md` | `docs/implementation/week4-day19-implementation-plan.md` | P2 |
| `docs/implementation/WEEK4_DAY20_IMPLEMENTATION_PLAN.md` | `docs/implementation/week4-day20-implementation-plan.md` | P2 |
| `docs/implementation/WEEK4_DAY20_SECURITY_AUDIT_REPORT.md` | `docs/implementation/week4-day20-security-audit-report.md` | P2 |
| `docs/implementation/WEEK4_DAY20_SUMMARY.md` | `docs/implementation/week4-day20-summary.md` | P2 |
| `docs/implementation/WEEK4_DAY21_IMPLEMENTATION_PLAN.md` | `docs/implementation/week4-day21-implementation-plan.md` | P2 |
| `docs/implementation/WEEK4_DAY22_IMPLEMENTATION_PLAN.md` | `docs/implementation/week4-day22-implementation-plan.md` | P2 |
| `docs/implementation/WEEK4_DAY22_SUMMARY.md` | `docs/implementation/week4-day22-summary.md` | P2 |
| `docs/implementation/WEEK4_IMPLEMENTATION_PLAN.md` | `docs/implementation/week4-implementation-plan.md` | P2 |
| `docs/implementation/WEEK5_DAY25_SUMMARY.md` | `docs/implementation/week5-day25-summary.md` | P2 |
| `docs/implementation/WEEK5_PRODUCTION_READY_SUMMARY.md` | `docs/implementation/week5-production-ready-summary.md` | P1 |
| `docs/implementation/WEEK6_EXECUTION_PLAN.md` | `docs/implementation/week6-execution-plan.md` | P0 |

### 1.4 Audits Directory (3 files)

| Current Name | New Name | Priority |
|--------------|----------|----------|
| `docs/implementation/audits/TECHNICAL_CONFRONTATION_ANALYSIS_2026-01-30.md` | `docs/implementation/audits/technical-confrontation-analysis-2026-01-30.md` | P1 |
| `docs/implementation/audits/DATA_SCRIPTS_SAI_AUDIT_2026-01-30.md` | `docs/implementation/audits/data-scripts-sai-audit-2026-01-30.md` | P1 |
| `docs/implementation/audits/REBUILD_VS_REMEDIATION_ANALYSIS_2026-01-30.md` | `docs/implementation/audits/rebuild-vs-remediation-analysis-2026-01-30.md` | P1 |

### 1.5 Other Directories (7 files)

| Current Name | New Name | Priority |
|--------------|----------|----------|
| `docs/migrations/UV_MIGRATION_GUIDE.md` | `docs/migrations/uv-migration-guide.md` | P1 |
| `docs/monitoring/SECURITY_MONITORING.md` | `docs/monitoring/security-monitoring.md` | P1 |
| `codebase-review-2026-02-11.md` | `codebase-review-2026-02-11.md` | P0 |
| `security-remediation-plan-2026-02-11.md` | `security-remediation-plan-2026-02-11.md` | P0 |
| `tooling-standards-update-2026-02-11.md` | `tooling-standards-update-2026-02-11.md` | P0 |
| `code-quality-implementation-plan-2026-02-11.md` | `code-quality-implementation-plan-2026-02-11.md` | P0 |
| `adal-graph-pipeline-explanation-2026-01-30-15-45-12-234.md` | `adal-graph-pipeline-explanation-2026-01-30-15-45-12-234.md` | P2 |

**Total Files:** 38 files (37 renames + 1 deletion)

---

## 2. Automated Script Specification

### 2.1 Script Requirements

**File:** `scripts/docs/apply-kebab-case.sh`

**Features:**
1. Dry-run mode (default)
2. Backup creation before execution
3. Automatic link updates in all markdown files
4. Git-aware renaming (`git mv` for history preservation)
5. Validation checks
6. Rollback capability
7. Progress reporting
8. Error handling

### 2.2 Script Pseudocode

```bash
#!/bin/bash
# File: scripts/docs/apply-kebab-case.sh

# Configuration
DRY_RUN=true  # Default to dry-run
BACKUP_DIR=".backup-$(date +%Y%m%d-%H%M%S)"
LOG_FILE="kebab-case-remediation.log"

# File mapping (old_name -> new_name)
declare -A FILE_MAP=(
    ["docs/BANKING_USE_CASES_TECHNICAL_SPEC.md"]="docs/banking-use-cases-technical-spec.md"
    ["docs/BANKING_USE_CASES_TECHNICAL_SPEC_COMPLETE.md"]="docs/banking-use-cases-technical-spec-complete.md"
    # ... (all 38 files)
)

# Functions
function log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
function error() { log "ERROR: $*"; exit 1; }
function backup() { ... }
function rename_file() { ... }
function update_links() { ... }
function validate() { ... }
function rollback() { ... }

# Main execution
main() {
    log "Starting kebab-case remediation"
    log "Mode: $([ "$DRY_RUN" = true ] && echo 'DRY-RUN' || echo 'EXECUTE')"
    
    # Step 1: Validate environment
    validate_environment
    
    # Step 2: Create backup (if not dry-run)
    [ "$DRY_RUN" = false ] && backup
    
    # Step 3: Rename files
    for old_file in "${!FILE_MAP[@]}"; do
        new_file="${FILE_MAP[$old_file]}"
        rename_file "$old_file" "$new_file"
    done
    
    # Step 4: Update links in all markdown files
    update_links
    
    # Step 5: Validate changes
    validate_changes
    
    # Step 6: Report results
    generate_report
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --execute) DRY_RUN=false ;;
        --rollback) rollback; exit 0 ;;
        --help) show_help; exit 0 ;;
        *) error "Unknown option: $1" ;;
    esac
    shift
done

main
```

### 2.3 Link Update Strategy

**Pattern Matching:**
```bash
# Find all markdown links to renamed files
grep -r '\[.*\](.*BANKING_USE_CASES_TECHNICAL_SPEC\.md)' docs/

# Replace with new name
sed -i 's|BANKING_USE_CASES_TECHNICAL_SPEC\.md|banking-use-cases-technical-spec.md|g' file.md
```

**Files to Update:**
- All markdown files in `docs/`
- `README.md`
- `QUICKSTART.md`
- `AGENTS.md`
- `.bob/rules-plan/AGENTS.md`

---

## 3. Dry-Run Execution Strategy

### 3.1 Dry-Run Output Format

```
=================================================================
KEBAB-CASE REMEDIATION - DRY-RUN MODE
=================================================================

[2026-02-12 11:00:00] Starting dry-run analysis...

Phase 1: File Renaming (38 files)
----------------------------------
✓ Would rename: docs/BANKING_USE_CASES_TECHNICAL_SPEC.md
  → docs/banking-use-cases-technical-spec.md
  
✓ Would rename: docs/BANKING_USE_CASES_TECHNICAL_SPEC_COMPLETE.md
  → docs/banking-use-cases-technical-spec-complete.md
  
⚠ Would delete: docs/banking/USER_GUIDE.md (duplicate of user-guide.md)

... (36 more files)

Phase 2: Link Updates (estimated 150+ links)
---------------------------------------------
✓ Would update: docs/index.md (5 links)
✓ Would update: README.md (2 links)
✓ Would update: AGENTS.md (3 links)
... (more files)

Phase 3: Validation
-------------------
✓ All target files available for renaming
✓ No naming conflicts detected
✓ Git repository clean
⚠ 3 files currently open in VSCode (will need reload)

Summary
-------
Files to rename: 37
Files to delete: 1
Links to update: 152
Estimated time: 2-3 minutes

To execute: ./scripts/docs/apply-kebab-case.sh --execute
=================================================================
```

### 3.2 Execution Commands

```bash
# Step 1: Dry-run (default)
./scripts/docs/apply-kebab-case.sh

# Step 2: Review output
cat kebab-case-remediation.log

# Step 3: Execute if satisfied
./scripts/docs/apply-kebab-case.sh --execute

# Step 4: Rollback if needed
./scripts/docs/apply-kebab-case.sh --rollback
```

---

## 4. Link Update Strategy

### 4.1 Link Patterns to Update

**Markdown Links:**
```markdown
[Text](banking-use-cases-technical-spec.md)
[Text](docs/banking-use-cases-technical-spec.md)
[Text](../BANKING_USE_CASES_TECHNICAL_SPEC.md)
```

**Reference Links:**
```markdown
[link-ref]: BANKING_USE_CASES_TECHNICAL_SPEC.md
```

**Inline Code:**
```markdown
See `banking-use-cases-technical-spec.md` for details
```

### 4.2 Files Requiring Link Updates

**High Priority (P0):**
- `docs/index.md` - Central navigation
- `README.md` - Project overview
- `QUICKSTART.md` - Quick start guide
- `.bob/rules-plan/AGENTS.md` - Agent rules
- `docs/documentation-standards.md` - Standards reference

**Medium Priority (P1):**
- All files in `docs/implementation/`
- All files in `docs/banking/`
- All files in `docs/architecture/`

**Low Priority (P2):**
- Archive documents
- Historical reports

### 4.3 Automated Link Update Algorithm

```bash
# For each renamed file
for old_file in "${!FILE_MAP[@]}"; do
    new_file="${FILE_MAP[$old_file]}"
    old_basename=$(basename "$old_file")
    new_basename=$(basename "$new_file")
    
    # Find all markdown files
    find . -name "*.md" -type f | while read -r md_file; do
        # Skip the file being renamed
        [ "$md_file" = "./$old_file" ] && continue
        
        # Update all link patterns
        sed -i "s|]($old_basename)|]($new_basename)|g" "$md_file"
        sed -i "s|]($old_file)|]($new_file)|g" "$md_file"
        sed -i "s|\`$old_basename\`|\`$new_basename\`|g" "$md_file"
    done
done
```

---

## 5. Validation Procedures

### 5.1 Pre-Execution Validation

```bash
# Check 1: Git repository clean
git status --porcelain | wc -l  # Should be 0

# Check 2: All files exist
for file in "${!FILE_MAP[@]}"; do
    [ -f "$file" ] || echo "ERROR: $file not found"
done

# Check 3: No naming conflicts
for new_file in "${FILE_MAP[@]}"; do
    [ -f "$new_file" ] && echo "WARNING: $new_file already exists"
done

# Check 4: Backup directory available
[ -d "$BACKUP_DIR" ] && echo "ERROR: Backup directory exists"
```

### 5.2 Post-Execution Validation

```bash
# Check 1: All files renamed
for old_file in "${!FILE_MAP[@]}"; do
    [ ! -f "$old_file" ] || echo "ERROR: $old_file still exists"
done

for new_file in "${FILE_MAP[@]}"; do
    [ -f "$new_file" ] || echo "ERROR: $new_file not created"
done

# Check 2: No broken links
find docs -name "*.md" -exec grep -l '\[.*\](.*[A-Z_][A-Z_].*\.md)' {} \;

# Check 3: Git history preserved
for new_file in "${FILE_MAP[@]}"; do
    git log --follow "$new_file" | head -n 1
done

# Check 4: Markdown syntax valid
find docs -name "*.md" -exec markdownlint {} \;
```

### 5.3 Manual Validation Checklist

- [ ] All 38 files renamed successfully
- [ ] No broken links in documentation
- [ ] Git history preserved for all files
- [ ] VSCode tabs updated (reload required)
- [ ] Documentation index updated
- [ ] CI/CD workflows still pass
- [ ] No markdown syntax errors

---

## 6. Rollback Plan

### 6.1 Automatic Rollback

```bash
# Restore from backup
./scripts/docs/apply-kebab-case.sh --rollback

# This will:
# 1. Restore all files from backup directory
# 2. Revert all link updates
# 3. Clean up temporary files
# 4. Validate restoration
```

### 6.2 Manual Rollback

```bash
# Option 1: Git reset (if committed)
git reset --hard HEAD~1

# Option 2: Restore from backup
cp -r .backup-YYYYMMDD-HHMMSS/* .

# Option 3: Git revert (if pushed)
git revert <commit-hash>
```

### 6.3 Rollback Validation

```bash
# Verify all original files restored
for old_file in "${!FILE_MAP[@]}"; do
    [ -f "$old_file" ] || echo "ERROR: $old_file not restored"
done

# Verify no new files remain
for new_file in "${FILE_MAP[@]}"; do
    [ ! -f "$new_file" ] || echo "WARNING: $new_file still exists"
done
```

---

## 7. Execution Checklist

### 7.1 Pre-Execution

- [ ] Review this plan completely
- [ ] Ensure git repository is clean (`git status`)
- [ ] Close all affected files in VSCode
- [ ] Create manual backup: `tar -czf docs-backup-$(date +%Y%m%d).tar.gz docs/`
- [ ] Notify team of upcoming changes
- [ ] Schedule execution during low-activity period

### 7.2 Execution

- [ ] Run dry-run: `./scripts/docs/apply-kebab-case.sh`
- [ ] Review dry-run output carefully
- [ ] Verify no unexpected changes
- [ ] Execute: `./scripts/docs/apply-kebab-case.sh --execute`
- [ ] Monitor execution for errors
- [ ] Review execution log

### 7.3 Post-Execution

- [ ] Run validation checks (Section 5.2)
- [ ] Test documentation navigation
- [ ] Verify links in key documents (README, QUICKSTART, index.md)
- [ ] Reload VSCode workspace
- [ ] Run CI/CD pipeline
- [ ] Commit changes: `git commit -m "docs: apply kebab-case naming convention to all documentation"`
- [ ] Push to repository
- [ ] Update team on completion

### 7.4 Rollback (if needed)

- [ ] Execute rollback: `./scripts/docs/apply-kebab-case.sh --rollback`
- [ ] Verify restoration
- [ ] Analyze failure cause
- [ ] Fix issues
- [ ] Retry execution

---

## 8. Risk Mitigation

### 8.1 Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Broken links | HIGH | HIGH | Automated link update + validation |
| Lost git history | LOW | HIGH | Use `git mv` instead of `mv` |
| VSCode confusion | MEDIUM | LOW | Document reload procedure |
| CI/CD failures | MEDIUM | MEDIUM | Update workflow references |
| Concurrent edits | LOW | HIGH | Execute during low-activity period |

### 8.2 Mitigation Strategies

**Broken Links:**
- Automated link scanning and update
- Post-execution validation
- Manual review of key documents

**Git History:**
- Use `git mv` for all renames
- Verify history with `git log --follow`

**VSCode Issues:**
- Document reload procedure
- Provide list of renamed files
- Update workspace settings if needed

**CI/CD:**
- Review all workflow files
- Update any hardcoded paths
- Test pipeline after execution

---

## 9. Communication Plan

### 9.1 Pre-Execution Announcement

**Subject:** Documentation Renaming - Kebab-Case Convention

**Message:**
```
Team,

We will be applying kebab-case naming convention to all documentation 
files on [DATE] at [TIME]. This will rename 38 files to comply with 
our documentation standards.

Impact:
- 38 files will be renamed
- All links will be automatically updated
- Git history will be preserved
- VSCode workspace reload required

Duration: ~5 minutes
Downtime: None (documentation only)

Please:
1. Commit/push any pending documentation changes before [TIME]
2. Close all documentation files in your editor
3. Reload workspace after completion

Questions? Contact [CONTACT]
```

### 9.2 Post-Execution Announcement

**Subject:** Documentation Renaming Complete

**Message:**
```
Team,

Kebab-case renaming is complete. All documentation files now follow 
the kebab-case convention.

Changes:
- 37 files renamed
- 1 duplicate file removed
- 152 links updated
- Git history preserved

Action Required:
1. Pull latest changes: git pull
2. Reload VSCode workspace
3. Update any local bookmarks

New file locations documented in:
docs/implementation/kebab-case-remediation-plan.md

Questions? Contact [CONTACT]
```

---

## 10. Success Criteria

### 10.1 Technical Success

- ✅ All 38 files renamed successfully
- ✅ Zero broken links in documentation
- ✅ Git history preserved for all files
- ✅ All validation checks pass
- ✅ CI/CD pipeline passes
- ✅ No markdown syntax errors

### 10.2 Operational Success

- ✅ Execution completed within estimated time (2-3 hours)
- ✅ No rollback required
- ✅ Team notified and updated
- ✅ Documentation standards compliance achieved
- ✅ No user-reported issues

### 10.3 Quality Success

- ✅ Consistent naming across all documentation
- ✅ Improved navigation and discoverability
- ✅ Professional appearance
- ✅ Easier automation and tooling integration

---

## 11. Next Steps After Completion

### 11.1 Immediate (Day 1)

1. Monitor for any reported issues
2. Fix any broken links discovered
3. Update any external references
4. Document lessons learned

### 11.2 Short-Term (Week 1)

1. Add kebab-case validation to pre-commit hooks
2. Update documentation standards guide
3. Create naming convention linter
4. Train team on new standards

### 11.3 Long-Term (Month 1)

1. Review compliance across all documentation
2. Extend standards to other file types
3. Automate compliance checking in CI/CD
4. Update contribution guidelines

---

## Appendix A: Complete File Mapping

```bash
# Root level (4 files)
docs/BANKING_USE_CASES_TECHNICAL_SPEC.md → docs/banking-use-cases-technical-spec.md
docs/BANKING_USE_CASES_TECHNICAL_SPEC_COMPLETE.md → docs/banking-use-cases-technical-spec-complete.md
docs/TECHNICAL_SPECIFICATIONS.md → docs/technical-specifications.md
docs/DOCS_OPTIMIZATION_PLAN.md → docs/docs-optimization-plan.md

# Banking (4 files)
docs/banking/PHASE5_VECTOR_AI_FOUNDATION.md → docs/banking/phase5-vector-ai-foundation.md
docs/banking/PHASE5_IMPLEMENTATION_COMPLETE.md → docs/banking/phase5-implementation-complete.md
docs/banking/ENTERPRISE_ADVANCED_PATTERNS_PLAN.md → docs/banking/enterprise-advanced-patterns-plan.md
docs/banking/USER_GUIDE.md → DELETE (duplicate)

# Implementation (20 files)
docs/implementation/EXCEPTION_HANDLING_AUDIT.md → docs/implementation/exception-handling-audit.md
docs/implementation/PHASE2_WEEK2_STRUCTURE_ORGANIZATION.md → docs/implementation/phase2-week2-structure-organization.md
docs/implementation/PHASE3_QUICK_START.md → docs/implementation/phase3-quick-start.md
docs/implementation/PHASE3_WEEK3_STANDARDIZATION.md → docs/implementation/phase3-week3-standardization.md
docs/implementation/PRODUCTION_READINESS_AUDIT_2026.md → docs/implementation/production-readiness-audit-2026.md
docs/implementation/PRODUCTION_READINESS_STATUS_FINAL.md → docs/implementation/production-readiness-status-final.md
docs/implementation/REVIEW_CONFRONTATION_ANALYSIS_2026-02-11.md → docs/implementation/review-confrontation-analysis-2026-02-11.md
docs/implementation/WEEK1_PROGRESS_SUMMARY_2026-02-11.md → docs/implementation/week1-progress-summary-2026-02-11.md
docs/implementation/WEEK2_DAYS_8-12_IMPLEMENTATION_GUIDE.md → docs/implementation/week2-days-8-12-implementation-guide.md
docs/implementation/WEEK3_DAYS13-15_SUMMARY.md → docs/implementation/week3-days13-15-summary.md
docs/implementation/WEEK3_IMPLEMENTATION_PLAN.md → docs/implementation/week3-implementation-plan.md
docs/implementation/WEEK4_DAY19_IMPLEMENTATION_PLAN.md → docs/implementation/week4-day19-implementation-plan.md
docs/implementation/WEEK4_DAY20_IMPLEMENTATION_PLAN.md → docs/implementation/week4-day20-implementation-plan.md
docs/implementation/WEEK4_DAY20_SECURITY_AUDIT_REPORT.md → docs/implementation/week4-day20-security-audit-report.md
docs/implementation/WEEK4_DAY20_SUMMARY.md → docs/implementation/week4-day20-summary.md
docs/implementation/WEEK4_DAY21_IMPLEMENTATION_PLAN.md → docs/implementation/week4-day21-implementation-plan.md
docs/implementation/WEEK4_DAY22_IMPLEMENTATION_PLAN.md → docs/implementation/week4-day22-implementation-plan.md
docs/implementation/WEEK4_DAY22_SUMMARY.md → docs/implementation/week4-day22-summary.md
docs/implementation/WEEK4_IMPLEMENTATION_PLAN.md → docs/implementation/week4-implementation-plan.md
docs/implementation/WEEK5_DAY25_SUMMARY.md → docs/implementation/week5-day25-summary.md
docs/implementation/WEEK5_PRODUCTION_READY_SUMMARY.md → docs/implementation/week5-production-ready-summary.md
docs/implementation/WEEK6_EXECUTION_PLAN.md → docs/implementation/week6-execution-plan.md

# Audits (3 files)
docs/implementation/audits/TECHNICAL_CONFRONTATION_ANALYSIS_2026-01-30.md → docs/implementation/audits/technical-confrontation-analysis-2026-01-30.md
docs/implementation/audits/DATA_SCRIPTS_SAI_AUDIT_2026-01-30.md → docs/implementation/audits/data-scripts-sai-audit-2026-01-30.md
docs/implementation/audits/REBUILD_VS_REMEDIATION_ANALYSIS_2026-01-30.md → docs/implementation/audits/rebuild-vs-remediation-analysis-2026-01-30.md

# Other (7 files)
docs/migrations/UV_MIGRATION_GUIDE.md → docs/migrations/uv-migration-guide.md
docs/monitoring/SECURITY_MONITORING.md → docs/monitoring/security-monitoring.md
CODEBASE_REVIEW_2026-02-11.md → codebase-review-2026-02-11.md
SECURITY_REMEDIATION_PLAN_2026-02-11.md → security-remediation-plan-2026-02-11.md
TOOLING_STANDARDS_UPDATE_2026-02-11.md → tooling-standards-update-2026-02-11.md
CODE_QUALITY_IMPLEMENTATION_PLAN_2026-02-11.md → code-quality-implementation-plan-2026-02-11.md
adal_graph_pipeline_explanation_2026-01-30_15-45-12-234.md → adal-graph-pipeline-explanation-2026-01-30-15-45-12-234.md
```

---

## Appendix B: Script Implementation

**Note:** Since Plan mode restricts script creation, the actual bash script must be created in Code mode. The script should implement all features specified in Section 2.

**Required Script:** `scripts/docs/apply-kebab-case.sh`

**Minimum Requirements:**
- Dry-run mode (default)
- Backup creation
- Git-aware renaming
- Link updates
- Validation
- Rollback capability
- Progress reporting

**To create the script, switch to Code mode and use the specification in Section 2.2.**

---

## Summary

This plan provides a comprehensive strategy for applying kebab-case naming conventions to all documentation files. The automated approach with dry-run capability minimizes risk while ensuring consistent, professional documentation standards.

**Recommended Execution:**
1. Review this plan thoroughly
2. Switch to Code mode to create the script
3. Run dry-run to validate
4. Execute during low-activity period
5. Validate and commit changes

**Estimated Total Time:** 2-3 hours (automated) or 6-8 hours (manual)

**Status:** Ready for implementation - awaiting mode switch to Code for script creation.

---

**Version:** 1.0  
**Date:** 2026-02-12  
**Author:** David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
**Status:** Ready for Execution