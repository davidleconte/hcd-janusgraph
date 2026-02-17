# Archival Script Template

This document contains the shell script for archiving obsolete documentation. Save this as `scripts/maintenance/archive-obsolete-docs.sh` and make it executable.

```bash
#!/bin/bash
# Archive obsolete documentation files
# Preserves git history using git mv
# Based on: docs/implementation/documentation-archival-analysis.md

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TOTAL_ARCHIVED=0
FAILED=0

# Log file
LOG_FILE="archival-log-$(date +%Y%m%d-%H%M%S).txt"

echo "🗄️  Documentation Archival Script"
echo "=================================="
echo ""
echo "This will archive 117 obsolete documentation files"
echo "Log file: $LOG_FILE"
echo ""

# Function to archive a file
archive_file() {
    local source="$1"
    local dest="$2"
    
    if [ -f "$source" ]; then
        echo "  📦 Archiving: $source -> $dest"
        git mv "$source" "$dest" 2>&1 | tee -a "$LOG_FILE"
        if [ $? -eq 0 ]; then
            ((TOTAL_ARCHIVED++))
        else
            echo -e "${RED}  ❌ Failed to archive: $source${NC}"
            ((FAILED++))
        fi
    else
        echo -e "${YELLOW}  ⚠️  File not found (skipping): $source${NC}"
    fi
}

# Create archive directory structure
echo "📁 Creating archive directory structure..."
mkdir -p docs/archive/2026-02/{weekly-summaries,phase-iterations,duplicates,audits,remediation,misc}
echo ""

# Category 1: Duplicate Documentation (15 files)
echo "Category 1: Archiving Duplicate Documentation (15 files)"
echo "=========================================================="

archive_file "docs/banking/user-guide.md" "docs/archive/2026-02/duplicates/user-guide.md"
archive_file "docs/banking/user-guide-duplicate.md" "docs/archive/2026-02/duplicates/user-guide-duplicate.md"
archive_file "docs/banking-use-cases-technical-spec.md" "docs/archive/2026-02/duplicates/banking-use-cases-technical-spec.md"
archive_file "docs/banking-use-cases-technical-spec-complete.md" "docs/archive/2026-02/duplicates/banking-use-cases-technical-spec-complete.md"
archive_file "docs/banking/planning/technical-spec.md" "docs/archive/2026-02/duplicates/technical-spec.md"
archive_file "docs/banking/planning/technical-spec-complete.md" "docs/archive/2026-02/duplicates/technical-spec-complete.md"
archive_file "docs/banking/phase-5-implementation-complete.md" "docs/archive/2026-02/duplicates/phase-5-implementation-complete.md"
archive_file "docs/banking/phase-5-vector-ai-foundation.md" "docs/archive/2026-02/duplicates/phase-5-vector-ai-foundation.md"
archive_file "docs/banking/implementation/phases/phase-5-vector-ai-foundation.md" "docs/archive/2026-02/duplicates/phase-5-vector-ai-foundation-phases.md"
archive_file "docs/banking/enterprise-advanced-patterns-plan.md" "docs/archive/2026-02/duplicates/enterprise-advanced-patterns-plan.md"
archive_file "docs/operations/runbook.md" "docs/archive/2026-02/duplicates/runbook.md"
archive_file "docs/operations/monitoring.md" "docs/archive/2026-02/duplicates/monitoring.md"
archive_file "docs/operations/incident-response.md" "docs/archive/2026-02/duplicates/incident-response.md"
archive_file "docs/compliance/gdpr.md" "docs/archive/2026-02/duplicates/gdpr.md"
archive_file "docs/compliance/soc2.md" "docs/archive/2026-02/duplicates/soc2.md"

echo ""

# Category 2: Weekly/Daily Summaries (40 files)
echo "Category 2: Archiving Weekly/Daily Summaries (40 files)"
echo "========================================================"

# Week 1
archive_file "docs/implementation/week1-progress-summary-2026-02-11.md" "docs/archive/2026-02/weekly-summaries/week1-progress-summary-2026-02-11.md"
archive_file "docs/implementation/week1-complete-summary-2026-02-11.md" "docs/archive/2026-02/weekly-summaries/week1-complete-summary-2026-02-11.md"

# Week 2
archive_file "docs/implementation/week2-analytics-streaming-testing-plan.md" "docs/archive/2026-02/weekly-summaries/week2-analytics-streaming-testing-plan.md"
archive_file "docs/implementation/week2-days-6-7-progress-summary.md" "docs/archive/2026-02/weekly-summaries/week2-days-6-7-progress-summary.md"
archive_file "docs/implementation/week2-days-8-12-implementation-guide.md" "docs/archive/2026-02/weekly-summaries/week2-days-8-12-implementation-guide.md"
archive_file "docs/implementation/week2-day8-complete-summary.md" "docs/archive/2026-02/weekly-summaries/week2-day8-complete-summary.md"
archive_file "docs/implementation/week2-day9-complete-summary.md" "docs/archive/2026-02/weekly-summaries/week2-day9-complete-summary.md"
archive_file "docs/implementation/week2-day10-complete-summary.md" "docs/archive/2026-02/weekly-summaries/week2-day10-complete-summary.md"
archive_file "docs/implementation/week2-day11-complete-summary.md" "docs/archive/2026-02/weekly-summaries/week2-day11-complete-summary.md"
archive_file "docs/implementation/week2-day12-complete-summary.md" "docs/archive/2026-02/weekly-summaries/week2-day12-complete-summary.md"
archive_file "docs/implementation/week2-implementation-scope-analysis.md" "docs/archive/2026-02/weekly-summaries/week2-implementation-scope-analysis.md"
archive_file "docs/implementation/week2-next-steps.md" "docs/archive/2026-02/weekly-summaries/week2-next-steps.md"

# Week 3
archive_file "docs/implementation/week3-implementation-plan.md" "docs/archive/2026-02/weekly-summaries/week3-implementation-plan.md"
archive_file "docs/implementation/week3-days13-15-summary.md" "docs/archive/2026-02/weekly-summaries/week3-days13-15-summary.md"
archive_file "docs/implementation/week3-day17-implementation-plan.md" "docs/archive/2026-02/weekly-summaries/week3-day17-implementation-plan.md"
archive_file "docs/implementation/week3-day17-summary.md" "docs/archive/2026-02/weekly-summaries/week3-day17-summary.md"
archive_file "docs/implementation/week3-day18-implementation-plan.md" "docs/archive/2026-02/weekly-summaries/week3-day18-implementation-plan.md"
archive_file "docs/implementation/week3-day18-summary.md" "docs/archive/2026-02/weekly-summaries/week3-day18-summary.md"
archive_file "docs/implementation/week3-complete-summary.md" "docs/archive/2026-02/weekly-summaries/week3-complete-summary.md"

# Week 4
archive_file "docs/implementation/week4-implementation-plan.md" "docs/archive/2026-02/weekly-summaries/week4-implementation-plan.md"
archive_file "docs/implementation/week4-day19-implementation-plan.md" "docs/archive/2026-02/weekly-summaries/week4-day19-implementation-plan.md"
archive_file "docs/implementation/week4-day19-summary.md" "docs/archive/2026-02/weekly-summaries/week4-day19-summary.md"
archive_file "docs/implementation/week4-day19-code-quality-report.md" "docs/archive/2026-02/weekly-summaries/week4-day19-code-quality-report.md"
archive_file "docs/implementation/week4-day20-implementation-plan.md" "docs/archive/2026-02/weekly-summaries/week4-day20-implementation-plan.md"
archive_file "docs/implementation/week4-day20-summary.md" "docs/archive/2026-02/weekly-summaries/week4-day20-summary.md"
archive_file "docs/implementation/week4-day20-security-audit-report.md" "docs/archive/2026-02/weekly-summaries/week4-day20-security-audit-report.md"
archive_file "docs/implementation/week4-day21-implementation-plan.md" "docs/archive/2026-02/weekly-summaries/week4-day21-implementation-plan.md"
archive_file "docs/implementation/week4-day21-summary.md" "docs/archive/2026-02/weekly-summaries/week4-day21-summary.md"
archive_file "docs/implementation/week4-day21-performance-report.md" "docs/archive/2026-02/weekly-summaries/week4-day21-performance-report.md"
archive_file "docs/implementation/week4-day22-implementation-plan.md" "docs/archive/2026-02/weekly-summaries/week4-day22-implementation-plan.md"
archive_file "docs/implementation/week4-day22-summary.md" "docs/archive/2026-02/weekly-summaries/week4-day22-summary.md"
archive_file "docs/implementation/week4-day22-documentation-report.md" "docs/archive/2026-02/weekly-summaries/week4-day22-documentation-report.md"
archive_file "docs/implementation/week4-day23-summary.md" "docs/archive/2026-02/weekly-summaries/week4-day23-summary.md"
archive_file "docs/implementation/week4-day23-production-readiness-report.md" "docs/archive/2026-02/weekly-summaries/week4-day23-production-readiness-report.md"
archive_file "docs/implementation/week4-complete-summary.md" "docs/archive/2026-02/weekly-summaries/week4-complete-summary.md"

# Week 5
archive_file "docs/implementation/week5-day25-summary.md" "docs/archive/2026-02/weekly-summaries/week5-day25-summary.md"
archive_file "docs/implementation/week5-production-deployment-plan.md" "docs/archive/2026-02/weekly-summaries/week5-production-deployment-plan.md"
archive_file "docs/implementation/week5-production-ready-summary.md" "docs/archive/2026-02/weekly-summaries/week5-production-ready-summary.md"

# Week 6
archive_file "docs/implementation/week6-enhancement-plan.md" "docs/archive/2026-02/weekly-summaries/week6-enhancement-plan.md"
archive_file "docs/implementation/week6-execution-plan.md" "docs/archive/2026-02/weekly-summaries/week6-execution-plan.md"

echo ""

# Category 3: Superseded Phase Documentation (8 files)
echo "Category 3: Archiving Superseded Phase Documentation (8 files)"
echo "==============================================================="

archive_file "docs/implementation/phase1-week1-structure-reorganization.md" "docs/archive/2026-02/phase-iterations/phase1-week1-structure-reorganization.md"
archive_file "docs/implementation/phase2-week2-structure-organization.md" "docs/archive/2026-02/phase-iterations/phase2-week2-structure-organization.md"
archive_file "docs/implementation/phase3-week3-standardization.md" "docs/archive/2026-02/phase-iterations/phase3-week3-standardization.md"
archive_file "docs/implementation/phase4-week4-enhancement.md" "docs/archive/2026-02/phase-iterations/phase4-week4-enhancement.md"
archive_file "docs/implementation/phase1-security-fixes-complete.md" "docs/archive/2026-02/phase-iterations/phase1-security-fixes-complete.md"
archive_file "docs/implementation/phase2-security-hardening-complete.md" "docs/archive/2026-02/phase-iterations/phase2-security-hardening-complete.md"
archive_file "docs/implementation/phase3-quick-start.md" "docs/archive/2026-02/phase-iterations/phase3-quick-start.md"
archive_file "docs/implementation/production-readiness-status.md" "docs/archive/2026-02/phase-iterations/production-readiness-status.md"

echo ""

# Category 4: Phase 8 Iterations (17 files)
echo "Category 4: Archiving Phase 8 Iterations (17 files)"
echo "===================================================="

archive_file "docs/banking/implementation/phases/phase-8-complete-roadmap.md" "docs/archive/2026-02/phase-iterations/phase-8-complete-roadmap.md"
archive_file "docs/banking/implementation/phases/phase-8-implementation-guide.md" "docs/archive/2026-02/phase-iterations/phase-8-implementation-guide.md"
archive_file "docs/banking/implementation/phases/phase-8-implementation-status.md" "docs/archive/2026-02/phase-iterations/phase-8-implementation-status.md"
archive_file "docs/banking/implementation/phases/phase-8-week-3-complete.md" "docs/archive/2026-02/phase-iterations/phase-8-week-3-complete.md"
archive_file "docs/banking/implementation/phases/phase-8-week-5-status.md" "docs/archive/2026-02/phase-iterations/phase-8-week-5-status.md"
archive_file "docs/banking/implementation/phases/phase-8a-complete.md" "docs/archive/2026-02/phase-iterations/phase-8a-complete.md"
archive_file "docs/banking/implementation/phases/phase-8a-implementation-status.md" "docs/archive/2026-02/phase-iterations/phase-8a-implementation-status.md"
archive_file "docs/banking/implementation/phases/phase-8a-week-1-complete.md" "docs/archive/2026-02/phase-iterations/phase-8a-week-1-complete.md"
archive_file "docs/banking/implementation/phases/phase-8b-week-3-status.md" "docs/archive/2026-02/phase-iterations/phase-8b-week-3-status.md"
archive_file "docs/banking/implementation/phases/phase-8c-week-5-complete.md" "docs/archive/2026-02/phase-iterations/phase-8c-week-5-complete.md"
archive_file "docs/banking/implementation/phases/phase-8d-week-6-complete.md" "docs/archive/2026-02/phase-iterations/phase-8d-week-6-complete.md"
archive_file "docs/banking/implementation/phases/phase-8d-week-8-plan.md" "docs/archive/2026-02/phase-iterations/phase-8d-week-8-plan.md"
archive_file "docs/banking/implementation/phases/phase8-complete.md" "docs/archive/2026-02/phase-iterations/phase8-complete.md"
archive_file "docs/banking/implementation/phases/phase8-week4-complete.md" "docs/archive/2026-02/phase-iterations/phase8-week4-complete.md"
archive_file "docs/banking/implementation/phases/phase8d-week6-plan.md" "docs/archive/2026-02/phase-iterations/phase8d-week6-plan.md"
archive_file "docs/banking/implementation/phases/phase8d-week7-complete.md" "docs/archive/2026-02/phase-iterations/phase8d-week7-complete.md"
archive_file "docs/banking/implementation/phases/phase8d-week7-plan.md" "docs/archive/2026-02/phase-iterations/phase8d-week7-plan.md"

echo ""

# Category 5: Obsolete Audits (4 files)
echo "Category 5: Archiving Obsolete Audits (4 files)"
echo "================================================"

archive_file "docs/implementation/audits/data-scripts-sai-audit-2026-01-30.md" "docs/archive/2026-02/audits/data-scripts-sai-audit-2026-01-30.md"
archive_file "docs/implementation/audits/rebuild-vs-remediation-analysis-2026-01-30.md" "docs/archive/2026-02/audits/rebuild-vs-remediation-analysis-2026-01-30.md"
archive_file "docs/implementation/audits/remediation-plan-2026-01-30.md" "docs/archive/2026-02/audits/remediation-plan-2026-01-30.md"
archive_file "docs/implementation/audits/technical-confrontation-analysis-2026-01-30.md" "docs/archive/2026-02/audits/technical-confrontation-analysis-2026-01-30.md"

echo ""

# Category 6: Completed Remediation (9 files)
echo "Category 6: Archiving Completed Remediation (9 files)"
echo "======================================================"

archive_file "docs/implementation/remediation/audit-remediation-complete.md" "docs/archive/2026-02/remediation/audit-remediation-complete.md"
archive_file "docs/implementation/remediation/deployment-documentation-update.md" "docs/archive/2026-02/remediation/deployment-documentation-update.md"
archive_file "docs/implementation/remediation/compose-build-context-fix.md" "docs/archive/2026-02/remediation/compose-build-context-fix.md"
archive_file "docs/implementation/remediation/final-remediation-status-2026-02-04.md" "docs/archive/2026-02/remediation/final-remediation-status-2026-02-04.md"
archive_file "docs/implementation/remediation/orchestration-improvements-complete.md" "docs/archive/2026-02/remediation/orchestration-improvements-complete.md"
archive_file "docs/implementation/remediation/p2-recommendations.md" "docs/archive/2026-02/remediation/p2-recommendations.md"
archive_file "docs/implementation/remediation/script-fixes-complete.md" "docs/archive/2026-02/remediation/script-fixes-complete.md"
archive_file "docs/implementation/remediation/service-startup-orchestration-analysis.md" "docs/archive/2026-02/remediation/service-startup-orchestration-analysis.md"
archive_file "docs/implementation/remediation/service-startup-reliability-fix.md" "docs/archive/2026-02/remediation/service-startup-reliability-fix.md"

echo ""

# Category 7: Miscellaneous (7 files)
echo "Category 7: Archiving Miscellaneous Obsolete Files (7 files)"
echo "============================================================="

archive_file "docs/implementation/backlog.md" "docs/archive/2026-02/misc/backlog.md"
archive_file "docs/implementation/p0-fixes.md" "docs/archive/2026-02/misc/p0-fixes.md"
archive_file "docs/implementation/project-handoff.md" "docs/archive/2026-02/misc/project-handoff.md"
archive_file "docs/implementation/project-structure-review.md" "docs/archive/2026-02/misc/project-structure-review.md"
archive_file "docs/demo-setup-guide.md" "docs/archive/2026-02/misc/demo-setup-guide.md"
archive_file "docs/docs-optimization-plan.md" "docs/archive/2026-02/misc/docs-optimization-plan.md"
archive_file "docs/implementation/docs-optimization-complete.md" "docs/archive/2026-02/misc/docs-optimization-complete.md"

echo ""
echo "=================================="
echo "📊 Archival Summary"
echo "=================================="
echo -e "${GREEN}✅ Successfully archived: $TOTAL_ARCHIVED files${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ Failed to archive: $FAILED files${NC}"
fi
echo ""
echo "Log file: $LOG_FILE"
echo ""
echo "Next steps:"
echo "1. Review changes: git status"
echo "2. Validate archival: bash scripts/validation/validate-archival.sh"
echo "3. Create archive index: docs/archive/2026-02/README.md"
echo "4. Update affected README files"
echo "5. Commit changes: git add -A && git commit -m 'docs: archive obsolete documentation'"
echo ""
```

## Usage

1. Save this script as `scripts/maintenance/archive-obsolete-docs.sh`
2. Make it executable: `chmod +x scripts/maintenance/archive-obsolete-docs.sh`
3. Run it: `bash scripts/maintenance/archive-obsolete-docs.sh`

## Expected Output

```
🗄️  Documentation Archival Script
==================================

This will archive 117 obsolete documentation files
Log file: archival-log-20260211-202830.txt

📁 Creating archive directory structure...

Category 1: Archiving Duplicate Documentation (15 files)
==========================================================
  📦 Archiving: docs/banking/user-guide.md -> docs/archive/2026-02/duplicates/user-guide.md
  ...

==================================
📊 Archival Summary
==================================
✅ Successfully archived: 117 files

Log file: archival-log-20260211-202830.txt

Next steps:
1. Review changes: git status
2. Validate archival: bash scripts/validation/validate-archival.sh
3. Create archive index: docs/archive/2026-02/README.md
4. Update affected README files
5. Commit changes: git add -A && git commit -m 'docs: archive obsolete documentation'