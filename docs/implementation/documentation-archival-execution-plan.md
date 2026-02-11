# Documentation Archival Execution Plan

**Date:** 2026-02-11  
**Status:** Ready for Execution  
**Based On:** [`documentation-archival-analysis.md`](documentation-archival-analysis.md)

---

## Overview

This plan provides step-by-step instructions to archive 117 obsolete documentation files (42% of total) while preserving git history and maintaining documentation integrity.

---

## Pre-Execution Checklist

- [ ] Review [`documentation-archival-analysis.md`](documentation-archival-analysis.md)
- [ ] Approve archival decisions
- [ ] Backup current documentation state
- [ ] Ensure working directory is clean (`git status`)
- [ ] Create feature branch for archival

---

## Execution Steps

### Step 1: Create Feature Branch

```bash
git checkout -b docs/archive-obsolete-documentation-2026-02
```

### Step 2: Create Archive Directory Structure

```bash
mkdir -p docs/archive/2026-02/{weekly-summaries,phase-iterations,duplicates,audits,remediation,misc}
```

### Step 3: Run Archival Script

The automated script will:
1. Move files using `git mv` to preserve history
2. Create archive index
3. Update affected README files
4. Generate archival report

```bash
bash scripts/maintenance/archive-obsolete-docs.sh
```

### Step 4: Validate Results

```bash
# Check that files were moved correctly
bash scripts/validation/validate-archival.sh

# Verify no broken links
bash scripts/validation/check-doc-links.sh
```

### Step 5: Review Changes

```bash
git status
git diff --stat
```

### Step 6: Commit Changes

```bash
git add -A
git commit -m "docs: archive 117 obsolete documentation files

- Archived 40 weekly/daily progress summaries
- Archived 25 superseded phase documents
- Archived 15 duplicate files
- Archived 17 Phase 8 iteration documents
- Archived 9 completed remediation docs
- Archived 4 obsolete audits
- Archived 7 miscellaneous obsolete files

Total: 117 files archived (42% reduction)
Remaining active docs: 159 files

Preserves git history using git mv
Creates organized archive structure in docs/archive/2026-02/

See: docs/implementation/documentation-archival-analysis.md"
```

### Step 7: Push and Create PR

```bash
git push origin docs/archive-obsolete-documentation-2026-02
```

---

## Archival Script

Location: `scripts/maintenance/archive-obsolete-docs.sh`

The script is organized into functions for each category:

1. `archive_duplicates()` - 15 files
2. `archive_weekly_summaries()` - 40 files
3. `archive_phase_docs()` - 25 files
4. `archive_audits()` - 4 files
5. `archive_remediation()` - 9 files
6. `archive_phase8_iterations()` - 17 files
7. `archive_miscellaneous()` - 7 files

Each function:
- Uses `git mv` to preserve history
- Logs actions to `archival-log.txt`
- Handles missing files gracefully
- Provides progress feedback

---

## Validation Script

Location: `scripts/validation/validate-archival.sh`

Validates:
- All expected files were moved
- No files were accidentally deleted
- Archive directory structure is correct
- README files were updated
- No broken links in active documentation

---

## Rollback Procedure

If issues are discovered:

```bash
# Rollback all changes
git reset --hard HEAD

# Or rollback specific files
git mv docs/archive/2026-02/duplicates/user-guide.md docs/banking/user-guide.md
```

---

## Post-Execution Tasks

### Update Documentation Index

Update `docs/index.md` to reflect new structure:

```markdown
## Archive

Historical documentation is available in:
- [`docs/archive/2026-02/`](archive/2026-02/) - February 2026 archival
  - Weekly progress summaries
  - Phase iteration documents
  - Superseded documentation
```

### Update README Files

Update README files in affected directories:

- `docs/implementation/README.md`
- `docs/banking/implementation/phases/README.md`
- `docs/implementation/audits/README.md`
- `docs/implementation/remediation/README.md`

### Create Archive Index

Create `docs/archive/2026-02/README.md` with:
- List of archived files
- Reason for archival
- How to access archived content
- Link to analysis document

---

## Expected Outcomes

### Before Archival
- **Total Files:** 276 markdown files
- **Active Docs:** 276 files
- **Archived Docs:** 0 files

### After Archival
- **Total Files:** 276 markdown files (preserved in git)
- **Active Docs:** 159 files (58%)
- **Archived Docs:** 117 files (42%)

### Benefits
- **42% reduction** in active documentation
- **Clearer navigation** - easier to find current docs
- **Eliminated duplicates** - single source of truth
- **Preserved history** - all files remain in git
- **Better maintainability** - focus on current content

---

## Risk Assessment

### Low Risk
- All changes use `git mv` (history preserved)
- Can be rolled back easily
- No data loss
- Automated validation

### Mitigation
- Feature branch (not main)
- Comprehensive validation
- Detailed commit message
- Archive index for reference

---

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| Review analysis | 15 min | Pending |
| Approve plan | 5 min | Pending |
| Create branch | 1 min | Pending |
| Run archival script | 5 min | Pending |
| Validate results | 10 min | Pending |
| Update README files | 15 min | Pending |
| Create archive index | 10 min | Pending |
| Commit and push | 5 min | Pending |
| **Total** | **~1 hour** | Pending |

---

## Success Criteria

- [ ] All 117 files moved to archive
- [ ] Git history preserved for all files
- [ ] No broken links in active documentation
- [ ] Archive index created
- [ ] README files updated
- [ ] Validation script passes
- [ ] Commit message is detailed
- [ ] PR created and reviewed

---

## References

- **Analysis Document:** [`documentation-archival-analysis.md`](documentation-archival-analysis.md)
- **Archival Script:** `scripts/maintenance/archive-obsolete-docs.sh`
- **Validation Script:** `scripts/validation/validate-archival.sh`
- **Documentation Standards:** [`docs/documentation-standards.md`](../documentation-standards.md)

---

**Plan Created:** 2026-02-11  
**Status:** Ready for Execution  
**Approval Required:** Yes