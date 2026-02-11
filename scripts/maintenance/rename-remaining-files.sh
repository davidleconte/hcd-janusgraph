#!/bin/bash
# Rename remaining files to kebab-case
# This script renames all remaining files that violate kebab-case naming

set -e

echo "🔄 Renaming remaining files to kebab-case..."

# Function to rename a file if it exists
rename_if_exists() {
    local old_path="$1"
    local new_path="$2"
    
    if [ -f "$old_path" ]; then
        echo "  Renaming: $old_path -> $new_path"
        git mv "$old_path" "$new_path" 2>/dev/null || mv "$old_path" "$new_path"
    else
        echo "  ⚠️  Skipping (not found): $old_path"
    fi
}

# Root level files
rename_if_exists "tests/TEST_RESULTS.md" "tests/test-results.md"

# docs/migrations
rename_if_exists "docs/migrations/UV_MIGRATION_GUIDE.md" "docs/migrations/uv-migration-guide.md"

# docs/monitoring
rename_if_exists "docs/monitoring/SECURITY_MONITORING.md" "docs/monitoring/security-monitoring.md"

# scripts/testing
rename_if_exists "scripts/testing/TEST_RESULTS.md" "scripts/testing/test-results.md"

# docs/implementation - Week files
rename_if_exists "docs/implementation/WEEK1_PROGRESS_SUMMARY_2026-02-11.md" "docs/implementation/week1-progress-summary-2026-02-11.md"
rename_if_exists "docs/implementation/WEEK1_COMPLETE_SUMMARY_2026-02-11.md" "docs/implementation/week1-complete-summary-2026-02-11.md"
rename_if_exists "docs/implementation/WEEK2_ANALYTICS_STREAMING_TESTING_PLAN.md" "docs/implementation/week2-analytics-streaming-testing-plan.md"
rename_if_exists "docs/implementation/WEEK2_DAYS_6-7_PROGRESS_SUMMARY.md" "docs/implementation/week2-days-6-7-progress-summary.md"
rename_if_exists "docs/implementation/WEEK2_DAYS_8-12_IMPLEMENTATION_GUIDE.md" "docs/implementation/week2-days-8-12-implementation-guide.md"
rename_if_exists "docs/implementation/WEEK2_DAY8_COMPLETE_SUMMARY.md" "docs/implementation/week2-day8-complete-summary.md"
rename_if_exists "docs/implementation/WEEK2_DAY9_COMPLETE_SUMMARY.md" "docs/implementation/week2-day9-complete-summary.md"
rename_if_exists "docs/implementation/WEEK2_DAY10_COMPLETE_SUMMARY.md" "docs/implementation/week2-day10-complete-summary.md"
rename_if_exists "docs/implementation/WEEK2_DAY11_COMPLETE_SUMMARY.md" "docs/implementation/week2-day11-complete-summary.md"
rename_if_exists "docs/implementation/WEEK2_DAY12_COMPLETE_SUMMARY.md" "docs/implementation/week2-day12-complete-summary.md"
rename_if_exists "docs/implementation/WEEK2_IMPLEMENTATION_SCOPE_ANALYSIS.md" "docs/implementation/week2-implementation-scope-analysis.md"
rename_if_exists "docs/implementation/WEEK2_NEXT_STEPS.md" "docs/implementation/week2-next-steps.md"
rename_if_exists "docs/implementation/WEEK3_IMPLEMENTATION_PLAN.md" "docs/implementation/week3-implementation-plan.md"
rename_if_exists "docs/implementation/WEEK3_DAYS13-15_SUMMARY.md" "docs/implementation/week3-days13-15-summary.md"
rename_if_exists "docs/implementation/WEEK3_DAY17_IMPLEMENTATION_PLAN.md" "docs/implementation/week3-day17-implementation-plan.md"
rename_if_exists "docs/implementation/WEEK3_DAY17_SUMMARY.md" "docs/implementation/week3-day17-summary.md"
rename_if_exists "docs/implementation/WEEK3_DAY18_IMPLEMENTATION_PLAN.md" "docs/implementation/week3-day18-implementation-plan.md"
rename_if_exists "docs/implementation/WEEK3_DAY18_SUMMARY.md" "docs/implementation/week3-day18-summary.md"
rename_if_exists "docs/implementation/WEEK3_COMPLETE_SUMMARY.md" "docs/implementation/week3-complete-summary.md"
rename_if_exists "docs/implementation/WEEK4_IMPLEMENTATION_PLAN.md" "docs/implementation/week4-implementation-plan.md"
rename_if_exists "docs/implementation/WEEK4_DAY19_IMPLEMENTATION_PLAN.md" "docs/implementation/week4-day19-implementation-plan.md"
rename_if_exists "docs/implementation/WEEK4_DAY19_SUMMARY.md" "docs/implementation/week4-day19-summary.md"
rename_if_exists "docs/implementation/WEEK4_DAY19_CODE_QUALITY_REPORT.md" "docs/implementation/week4-day19-code-quality-report.md"
rename_if_exists "docs/implementation/WEEK4_DAY20_IMPLEMENTATION_PLAN.md" "docs/implementation/week4-day20-implementation-plan.md"
rename_if_exists "docs/implementation/WEEK4_DAY20_SUMMARY.md" "docs/implementation/week4-day20-summary.md"
rename_if_exists "docs/implementation/WEEK4_DAY20_SECURITY_AUDIT_REPORT.md" "docs/implementation/week4-day20-security-audit-report.md"
rename_if_exists "docs/implementation/WEEK4_DAY21_IMPLEMENTATION_PLAN.md" "docs/implementation/week4-day21-implementation-plan.md"
rename_if_exists "docs/implementation/WEEK4_DAY21_SUMMARY.md" "docs/implementation/week4-day21-summary.md"
rename_if_exists "docs/implementation/WEEK4_DAY21_PERFORMANCE_REPORT.md" "docs/implementation/week4-day21-performance-report.md"
rename_if_exists "docs/implementation/WEEK4_DAY22_IMPLEMENTATION_PLAN.md" "docs/implementation/week4-day22-implementation-plan.md"
rename_if_exists "docs/implementation/WEEK4_DAY22_SUMMARY.md" "docs/implementation/week4-day22-summary.md"
rename_if_exists "docs/implementation/WEEK4_DAY22_DOCUMENTATION_REPORT.md" "docs/implementation/week4-day22-documentation-report.md"
rename_if_exists "docs/implementation/WEEK4_DAY23_SUMMARY.md" "docs/implementation/week4-day23-summary.md"
rename_if_exists "docs/implementation/WEEK4_DAY23_PRODUCTION_READINESS_REPORT.md" "docs/implementation/week4-day23-production-readiness-report.md"
rename_if_exists "docs/implementation/WEEK4_COMPLETE_SUMMARY.md" "docs/implementation/week4-complete-summary.md"
rename_if_exists "docs/implementation/WEEK5_DAY25_SUMMARY.md" "docs/implementation/week5-day25-summary.md"
rename_if_exists "docs/implementation/WEEK5_PRODUCTION_DEPLOYMENT_PLAN.md" "docs/implementation/week5-production-deployment-plan.md"
rename_if_exists "docs/implementation/WEEK5_PRODUCTION_READY_SUMMARY.md" "docs/implementation/week5-production-ready-summary.md"
rename_if_exists "docs/implementation/WEEK6_ENHANCEMENT_PLAN.md" "docs/implementation/week6-enhancement-plan.md"
rename_if_exists "docs/implementation/WEEK6_EXECUTION_PLAN.md" "docs/implementation/week6-execution-plan.md"

# docs/implementation - Phase files
rename_if_exists "docs/implementation/PHASE2_COMPLETION_SUMMARY.md" "docs/implementation/phase2-completion-summary.md"
rename_if_exists "docs/implementation/PHASE2_SECURITY_HARDENING_COMPLETE.md" "docs/implementation/phase2-security-hardening-complete.md"
rename_if_exists "docs/implementation/PHASE3_QUICK_START.md" "docs/implementation/phase3-quick-start.md"
rename_if_exists "docs/implementation/PHASE3_COMPLETION_SUMMARY.md" "docs/implementation/phase3-completion-summary.md"

# docs/implementation - Other files
rename_if_exists "docs/implementation/EXCEPTION_HANDLING_AUDIT.md" "docs/implementation/exception-handling-audit.md"
rename_if_exists "docs/implementation/REVIEW_CONFRONTATION_ANALYSIS_2026-02-11.md" "docs/implementation/review-confrontation-analysis-2026-02-11.md"
rename_if_exists "docs/implementation/CODEBASE_REVIEW_2026-02-11_FINAL.md" "docs/implementation/codebase-review-2026-02-11-final.md"
rename_if_exists "docs/implementation/KEBAB_CASE_REMEDIATION_PLAN.md" "docs/implementation/kebab-case-remediation-plan.md"
rename_if_exists "docs/implementation/KEBAB_CASE_VALIDATION_SCRIPTS.md" "docs/implementation/kebab-case-validation-scripts.md"

# docs/implementation/audits
rename_if_exists "docs/implementation/audits/DEPLOYMENT_SCRIPTS_AUDIT_2026-02-11.md" "docs/implementation/audits/deployment-scripts-audit-2026-02-11.md"
rename_if_exists "docs/implementation/audits/WORKFLOW_PIP_AUDIT_2026-02-11.md" "docs/implementation/audits/workflow-pip-audit-2026-02-11.md"

echo ""
echo "✅ Renaming complete!"
echo ""
echo "Next steps:"
echo "1. Run validation: bash scripts/validation/validate-kebab-case.sh"
echo "2. Check for broken links: grep -r 'WEEK[0-9]' docs/"
echo "3. Commit changes: git add -A && git commit -m 'refactor: rename remaining files to kebab-case'"

# Made with Bob
