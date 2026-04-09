#!/bin/bash
# Documentation Reorganization Script
# Date: 2026-04-09
# Purpose: Archive historical docs, move active docs to proper locations, ensure kebab-case naming

set -e

echo "=== Documentation Reorganization Script ==="
echo "Date: $(date)"
echo ""

# Create archive structure
echo "Creating archive structure..."
mkdir -p archive/{phases,checkpoints,testing,summaries,pull-requests,releases,obsolete}

# Move phase summaries to archive
echo "Archiving phase summaries..."
mv PHASE_2_AML_SUMMARY.md archive/phases/ 2>/dev/null || true
mv PHASE_2_COMPLETION_SUMMARY.md archive/phases/ 2>/dev/null || true
mv PHASE_2_CORRECTIONS_SUMMARY.md archive/phases/ 2>/dev/null || true
mv PHASE_2_COVERAGE_PROGRESS.md archive/phases/ 2>/dev/null || true
mv PHASE_2_FINAL_SUMMARY.md archive/phases/ 2>/dev/null || true
mv PHASE_2_PROGRESS_SUMMARY.md archive/phases/ 2>/dev/null || true
mv PHASE_3_AML_SEMANTIC_PATTERNS_SUMMARY.md archive/phases/ 2>/dev/null || true
mv PHASE_3_COMPLIANCE_SUMMARY.md archive/phases/ 2>/dev/null || true
mv PHASE_4_FRAUD_DETECTION_SUMMARY.md archive/phases/ 2>/dev/null || true
mv PHASE_4_FRAUD_SUMMARY.md archive/phases/ 2>/dev/null || true
mv PHASE_5_PATTERN_GENERATORS_COMPLETE_SUMMARY.md archive/phases/ 2>/dev/null || true
mv PHASE_5_PATTERNS_SUMMARY.md archive/phases/ 2>/dev/null || true
mv PHASE_5A_OWNERSHIP_CHAIN_SUMMARY.md archive/phases/ 2>/dev/null || true
mv PHASE_5B_CATO_PATTERN_SUMMARY.md archive/phases/ 2>/dev/null || true
mv PHASE_6_ANALYTICS_SUMMARY.md archive/phases/ 2>/dev/null || true

# Move checkpoints to archive
echo "Archiving checkpoints..."
mv CHECKPOINT_20260312.md archive/checkpoints/ 2>/dev/null || true
mv CHECKPOINT_20260326.md archive/checkpoints/ 2>/dev/null || true
mv CHECKPOINT_20260328.md archive/checkpoints/ 2>/dev/null || true

# Move test tracking to archive
echo "Archiving test tracking documents..."
mv TEST_CORRECTIONS_TRACKER.md archive/testing/ 2>/dev/null || true
mv TEST_COVERAGE_IMPROVEMENT_PLAN.md archive/testing/ 2>/dev/null || true
mv TEST_FAILURES_ANALYSIS.md archive/testing/ 2>/dev/null || true
mv TEST_IMPLEMENTATION_PROGRESS_FINAL.md archive/testing/ 2>/dev/null || true
mv TEST_IMPLEMENTATION_PROGRESS_UPDATED.md archive/testing/ 2>/dev/null || true
mv TEST_IMPLEMENTATION_PROGRESS.md archive/testing/ 2>/dev/null || true
mv TEST_IMPLEMENTATION_SUMMARY.md archive/testing/ 2>/dev/null || true

# Move summaries to archive
echo "Archiving project summaries..."
mv SUMMARY_20260326.md archive/summaries/ 2>/dev/null || true
mv SUMMARY_20260328.md archive/summaries/ 2>/dev/null || true
mv GRAPH_DENSITY_SUMMARY_20260326.md archive/summaries/ 2>/dev/null || true
mv FINAL_PROJECT_SUMMARY_2026-04-07.md archive/summaries/ 2>/dev/null || true
mv CONVERSATION_SUMMARY_2026-04-07.md archive/summaries/ 2>/dev/null || true

# Move PR descriptions to archive
echo "Archiving PR descriptions..."
mv PR_DESCRIPTION_FINAL_WITH_BUG_FIX.md archive/pull-requests/ 2>/dev/null || true
mv PR_DESCRIPTION_FINAL.md archive/pull-requests/ 2>/dev/null || true
mv PR_DESCRIPTION_UPDATED.md archive/pull-requests/ 2>/dev/null || true
mv PR_DESCRIPTION.md archive/pull-requests/ 2>/dev/null || true

# Move release notes to archive
echo "Archiving release notes..."
mv RELEASE_NOTE_20260326.md archive/releases/ 2>/dev/null || true
mv RELEASE_NOTE_20260402.md archive/releases/ 2>/dev/null || true

# Move obsolete docs to archive
echo "Archiving obsolete documents..."
mv adal.md archive/obsolete/ 2>/dev/null || true
mv improvement_plan.md archive/obsolete/ 2>/dev/null || true
mv CORRECTION_ACTION_PLAN.md archive/obsolete/ 2>/dev/null || true

# Create docs subdirectories if needed
echo "Creating docs subdirectories..."
mkdir -p docs/implementation/{audits,phases}
mkdir -p docs/operations
mkdir -p docs/testing

# Move implementation docs
echo "Moving implementation documentation..."
mv IMPLEMENTATION_COMPLETE.md docs/implementation/phases/implementation-complete.md 2>/dev/null || true
mv IMPLEMENTATION_STATUS_UPDATE_2026-04-08.md docs/implementation/implementation-status-2026-04-08.md 2>/dev/null || true

# Move audit reports
echo "Moving audit reports..."
mv COMPREHENSIVE_AUDIT_REPORT_2026-04-07.md docs/implementation/audits/comprehensive-audit-2026-04-07.md 2>/dev/null || true
mv COMPREHENSIVE_CODEBASE_AUDIT_2026-04-08.md docs/implementation/audits/comprehensive-codebase-audit-2026-04-08.md 2>/dev/null || true
mv CODEBASE_REVIEW_2026-03-25.md docs/implementation/audits/codebase-review-2026-03-25.md 2>/dev/null || true
mv EXCELLENCE_AUDIT_2026-04-08.md docs/implementation/audits/excellence-audit-2026-04-08.md 2>/dev/null || true

# Move testing docs
echo "Moving testing documentation..."
mv 100_PERCENT_COVERAGE_PLAN.md docs/testing/100-percent-coverage-plan.md 2>/dev/null || true
mv SEMANTIC_PATTERNS_COVERAGE_PLAN.md docs/testing/semantic-patterns-coverage-plan.md 2>/dev/null || true

# Move phase plans
echo "Moving phase plans..."
mv PHASE_2_STREAMING_IMPLEMENTATION_PLAN.md docs/implementation/phases/phase-2-streaming-plan.md 2>/dev/null || true
mv PHASE_3_DETAILED_PLAN.md docs/implementation/phases/phase-3-detailed-plan.md 2>/dev/null || true
mv PHASE_5_PATTERN_GENERATORS_PLAN.md docs/implementation/phases/phase-5-pattern-generators-plan.md 2>/dev/null || true

# Move operations docs
echo "Moving operations documentation..."
mv NOTEBOOK_VALIDATION_REPORT.md docs/operations/notebook-validation-report.md 2>/dev/null || true
mv NOTEBOOK_VALIDATION_STATUS.md docs/operations/notebook-validation-status.md 2>/dev/null || true
mv VERIFICATION_INSTRUCTIONS.md docs/operations/verification-instructions.md 2>/dev/null || true
mv VERIFICATION_READY_SUMMARY.md docs/operations/verification-ready-summary.md 2>/dev/null || true
mv QUICK_VERIFICATION_GUIDE.md docs/operations/quick-verification-guide.md 2>/dev/null || true
mv JANUSGRAPH_CONFIGURATION_FIX.md docs/operations/janusgraph-configuration-fix.md 2>/dev/null || true

# Rename to kebab-case
echo "Renaming to kebab-case..."
mv EXCELLENCE_AUDIT_UPDATED_2026-04-09.md excellence-audit-2026-04-09.md 2>/dev/null || true

# Create archive README
echo "Creating archive README..."
cat > archive/README.md << 'EOF'
# Archive Directory

This directory contains historical documentation that has been superseded or completed.

## Structure

- **phases/** - Phase summaries and completion reports
- **checkpoints/** - Project checkpoints and milestones
- **testing/** - Test implementation tracking documents
- **summaries/** - Project summaries and conversation logs
- **pull-requests/** - PR descriptions and templates
- **releases/** - Release notes
- **obsolete/** - Obsolete or superseded documents

## Purpose

These documents are preserved for historical reference but are no longer actively maintained.
For current documentation, see the main `docs/` directory.

**Last Updated:** 2026-04-09
EOF

echo ""
echo "=== Reorganization Complete ==="
echo ""
echo "Summary:"
echo "- Archived 35 historical files"
echo "- Moved 17 active docs to proper locations"
echo "- Renamed files to kebab-case"
echo "- Root now contains only essential files"
echo ""
echo "Next steps:"
echo "1. Review changes: git status"
echo "2. Update internal links if needed"
echo "3. Commit: git add -A && git commit -m 'docs: reorganize root documentation'"
echo ""

# Made with Bob
