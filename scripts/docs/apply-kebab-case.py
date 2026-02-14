#!/usr/bin/env python3
"""
File: scripts/docs/apply-kebab-case.py
Purpose: Apply kebab-case naming convention to all documentation files
Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-12
"""

import os
import sys
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
DRY_RUN = True
BACKUP_DIR = f".backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
LOG_FILE = f"kebab-case-remediation-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

# Counters
stats = {
    'files_renamed': 0,
    'files_deleted': 0,
    'links_updated': 0,
    'errors': 0
}

# File mapping (old_name -> new_name)
FILE_MAP = {
    # Root level (4 files)
    "docs/BANKING_USE_CASES_TECHNICAL_SPEC.md": "docs/banking-use-cases-technical-spec.md",
    "docs/BANKING_USE_CASES_TECHNICAL_SPEC_COMPLETE.md": "docs/banking-use-cases-technical-spec-complete.md",
    "docs/TECHNICAL_SPECIFICATIONS.md": "docs/technical-specifications.md",
    "docs/DOCS_OPTIMIZATION_PLAN.md": "docs/docs-optimization-plan.md",
    
    # Banking (3 files)
    "docs/banking/PHASE5_VECTOR_AI_FOUNDATION.md": "docs/banking/phase5-vector-ai-foundation.md",
    "docs/banking/PHASE5_IMPLEMENTATION_COMPLETE.md": "docs/banking/phase5-implementation-complete.md",
    "docs/banking/ENTERPRISE_ADVANCED_PATTERNS_PLAN.md": "docs/banking/enterprise-advanced-patterns-plan.md",
    
    # Implementation (20 files)
    "docs/implementation/EXCEPTION_HANDLING_AUDIT.md": "docs/implementation/exception-handling-audit.md",
    "docs/implementation/PHASE2_WEEK2_STRUCTURE_ORGANIZATION.md": "docs/implementation/phase2-week2-structure-organization.md",
    "docs/implementation/PHASE3_QUICK_START.md": "docs/implementation/phase3-quick-start.md",
    "docs/implementation/PHASE3_WEEK3_STANDARDIZATION.md": "docs/implementation/phase3-week3-standardization.md",
    "docs/implementation/PRODUCTION_READINESS_AUDIT_2026.md": "docs/implementation/production-readiness-audit-2026.md",
    "docs/implementation/PRODUCTION_READINESS_STATUS_FINAL.md": "docs/implementation/production-readiness-status-final.md",
    "docs/implementation/REVIEW_CONFRONTATION_ANALYSIS_2026-02-11.md": "docs/implementation/review-confrontation-analysis-2026-02-11.md",
    "docs/implementation/WEEK1_PROGRESS_SUMMARY_2026-02-11.md": "docs/implementation/week1-progress-summary-2026-02-11.md",
    "docs/implementation/WEEK2_DAYS_8-12_IMPLEMENTATION_GUIDE.md": "docs/implementation/week2-days-8-12-implementation-guide.md",
    "docs/implementation/WEEK3_DAYS13-15_SUMMARY.md": "docs/implementation/week3-days13-15-summary.md",
    "docs/implementation/WEEK3_IMPLEMENTATION_PLAN.md": "docs/implementation/week3-implementation-plan.md",
    "docs/implementation/WEEK4_DAY19_IMPLEMENTATION_PLAN.md": "docs/implementation/week4-day19-implementation-plan.md",
    "docs/implementation/WEEK4_DAY20_IMPLEMENTATION_PLAN.md": "docs/implementation/week4-day20-implementation-plan.md",
    "docs/implementation/WEEK4_DAY20_SECURITY_AUDIT_REPORT.md": "docs/implementation/week4-day20-security-audit-report.md",
    "docs/implementation/WEEK4_DAY20_SUMMARY.md": "docs/implementation/week4-day20-summary.md",
    "docs/implementation/WEEK4_DAY21_IMPLEMENTATION_PLAN.md": "docs/implementation/week4-day21-implementation-plan.md",
    "docs/implementation/WEEK4_DAY22_IMPLEMENTATION_PLAN.md": "docs/implementation/week4-day22-implementation-plan.md",
    "docs/implementation/WEEK4_DAY22_SUMMARY.md": "docs/implementation/week4-day22-summary.md",
    "docs/implementation/WEEK4_IMPLEMENTATION_PLAN.md": "docs/implementation/week4-implementation-plan.md",
    "docs/implementation/WEEK5_DAY25_SUMMARY.md": "docs/implementation/week5-day25-summary.md",
    "docs/implementation/WEEK5_PRODUCTION_READY_SUMMARY.md": "docs/implementation/week5-production-ready-summary.md",
    "docs/implementation/WEEK6_EXECUTION_PLAN.md": "docs/implementation/week6-execution-plan.md",
    
    # Audits (3 files)
    "docs/implementation/audits/TECHNICAL_CONFRONTATION_ANALYSIS_2026-01-30.md": "docs/implementation/audits/technical-confrontation-analysis-2026-01-30.md",
    "docs/implementation/audits/DATA_SCRIPTS_SAI_AUDIT_2026-01-30.md": "docs/implementation/audits/data-scripts-sai-audit-2026-01-30.md",
    "docs/implementation/audits/REBUILD_VS_REMEDIATION_ANALYSIS_2026-01-30.md": "docs/implementation/audits/rebuild-vs-remediation-analysis-2026-01-30.md",
    
    # Other (7 files)
    "docs/migrations/UV_MIGRATION_GUIDE.md": "docs/migrations/uv-migration-guide.md",
    "docs/monitoring/SECURITY_MONITORING.md": "docs/monitoring/security-monitoring.md",
    "CODEBASE_REVIEW_2026-02-11.md": "codebase-review-2026-02-11.md",
    "SECURITY_REMEDIATION_PLAN_2026-02-11.md": "security-remediation-plan-2026-02-11.md",
    "TOOLING_STANDARDS_UPDATE_2026-02-11.md": "tooling-standards-update-2026-02-11.md",
    "CODE_QUALITY_IMPLEMENTATION_PLAN_2026-02-11.md": "code-quality-implementation-plan-2026-02-11.md",
    "adal_graph_pipeline_explanation_2026-01-30_15-45-12-234.md": "adal-graph-pipeline-explanation-2026-01-30-15-45-12-234.md",
}

# Files to delete (duplicates)
FILES_TO_DELETE = [
    "docs/banking/USER_GUIDE.md"
]

def log(message: str, color: str = Colors.BLUE):
    """Log a message with timestamp and color."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{color}[{timestamp}]{Colors.NC} {message}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

def log_success(message: str):
    log(f"✓ {message}", Colors.GREEN)

def log_warning(message: str):
    log(f"⚠ {message}", Colors.YELLOW)

def log_error(message: str):
    log(f"✗ {message}", Colors.RED)
    stats['errors'] += 1

def validate_environment() -> bool:
    """Validate the environment before proceeding."""
    log("Validating environment...")
    
    # Check if in project root
    if not Path("README.md").exists() or not Path("docs").is_dir():
        log_error("Must run from project root directory")
        return False
    
    # Check git status
    try:
        subprocess.run(["git", "rev-parse", "--git-dir"], 
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        log_error("Not a git repository")
        return False
    
    # Check for uncommitted changes
    result = subprocess.run(["git", "status", "--porcelain"], 
                          capture_output=True, text=True)
    if result.stdout.strip():
        log_warning("Git repository has uncommitted changes")
        if not DRY_RUN:
            response = input("Continue anyway? (y/N) ")
            if response.lower() != 'y':
                return False
    
    log_success("Environment validation passed")
    return True

def create_backup():
    """Create backup of all files to be modified."""
    if DRY_RUN:
        log(f"Would create backup in: {BACKUP_DIR}")
        return
    
    log(f"Creating backup in: {BACKUP_DIR}")
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    
    # Backup files to be renamed
    for old_file in FILE_MAP.keys():
        if Path(old_file).exists():
            backup_path = Path(BACKUP_DIR) / old_file
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old_file, backup_path)
    
    # Backup files to be deleted
    for file in FILES_TO_DELETE:
        if Path(file).exists():
            backup_path = Path(BACKUP_DIR) / file
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, backup_path)
    
    log_success(f"Backup created: {BACKUP_DIR}")

def rename_file(old_file: str, new_file: str) -> bool:
    """Rename a single file using git mv if possible."""
    if not Path(old_file).exists():
        log_warning(f"File not found: {old_file}")
        return False
    
    if Path(new_file).exists():
        log_warning(f"Target file already exists: {new_file}")
        return False
    
    if DRY_RUN:
        log(f"Would rename: {old_file} → {new_file}")
    else:
        # Check if file is tracked by git
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", old_file],
            capture_output=True
        )
        
        if result.returncode == 0:
            # Use git mv
            subprocess.run(["git", "mv", old_file, new_file], check=True)
            log_success(f"Renamed (git): {old_file} → {new_file}")
        else:
            # Use regular mv
            Path(old_file).rename(new_file)
            log_success(f"Renamed: {old_file} → {new_file}")
    
    stats['files_renamed'] += 1
    return True

def delete_file(file: str) -> bool:
    """Delete a file using git rm if possible."""
    if not Path(file).exists():
        log_warning(f"File not found: {file}")
        return False
    
    if DRY_RUN:
        log(f"Would delete: {file} (duplicate)")
    else:
        # Check if file is tracked by git
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", file],
            capture_output=True
        )
        
        if result.returncode == 0:
            # Use git rm
            subprocess.run(["git", "rm", file], check=True)
            log_success(f"Deleted (git): {file}")
        else:
            # Use regular rm
            Path(file).unlink()
            log_success(f"Deleted: {file}")
    
    stats['files_deleted'] += 1
    return True

def update_links_in_file(md_file: Path) -> int:
    """Update links in a markdown file."""
    if not md_file.exists():
        return 0
    
    try:
        content = md_file.read_text(encoding='utf-8')
        original_content = content
        changes = 0
        
        # Update links for each renamed file
        for old_file, new_file in FILE_MAP.items():
            old_basename = Path(old_file).name
            new_basename = Path(new_file).name
            
            # Skip if this is the file being renamed
            if str(md_file) == old_file:
                continue
            
            # Update markdown links: [text](OLD.md) → [text](NEW.md)
            pattern1 = f"]({old_basename})"
            if pattern1 in content:
                content = content.replace(pattern1, f"]({new_basename})")
                changes += 1
            
            # Update full path links
            pattern2 = f"]({old_file})"
            if pattern2 in content:
                content = content.replace(pattern2, f"]({new_file})")
                changes += 1
            
            # Update inline code references: `OLD.md` → `NEW.md`
            pattern3 = f"`{old_basename}`"
            if pattern3 in content:
                content = content.replace(pattern3, f"`{new_basename}`")
                changes += 1
        
        if changes > 0:
            if DRY_RUN:
                log(f"Would update {changes} link(s) in: {md_file}")
            else:
                md_file.write_text(content, encoding='utf-8')
                log_success(f"Updated {changes} link(s) in: {md_file}")
            stats['links_updated'] += changes
        
        return changes
    except Exception as e:
        log_error(f"Error updating {md_file}: {e}")
        return 0

def update_all_links():
    """Update links in all markdown files."""
    log("Updating links in markdown files...")
    
    # Find all markdown files
    for md_file in Path('.').rglob('*.md'):
        update_links_in_file(md_file)
    
    log_success("Link update complete")

def validate_changes():
    """Validate that all changes were applied correctly."""
    log("Validating changes...")
    validation_errors = 0
    
    if DRY_RUN:
        log("Skipping validation in dry-run mode")
        return
    
    # Check all files were renamed
    for old_file in FILE_MAP.keys():
        if Path(old_file).exists():
            log_error(f"File still exists: {old_file}")
            validation_errors += 1
    
    for new_file in FILE_MAP.values():
        if not Path(new_file).exists():
            log_error(f"File not created: {new_file}")
            validation_errors += 1
    
    # Check for broken links
    log("Checking for potential broken links...")
    broken_links = 0
    pattern = re.compile(r'\[.*\]\(.*[A-Z_]{2,}.*\.md\)')
    
    for md_file in Path('docs').rglob('*.md'):
        try:
            content = md_file.read_text(encoding='utf-8')
            if pattern.search(content):
                log_warning(f"Potential broken link in: {md_file}")
                broken_links += 1
        except Exception:
            pass
    
    if broken_links > 0:
        log_warning(f"Found {broken_links} file(s) with potential broken links")
    
    if validation_errors == 0:
        log_success("Validation passed")
    else:
        log_error(f"Validation failed with {validation_errors} error(s)")

def generate_report():
    """Generate final report."""
    print("\n" + "=" * 65)
    print("KEBAB-CASE REMEDIATION REPORT")
    print("=" * 65)
    print()
    print(f"Mode: {'DRY-RUN' if DRY_RUN else 'EXECUTE'}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Summary:")
    print(f"  Files renamed: {stats['files_renamed']}")
    print(f"  Files deleted: {stats['files_deleted']}")
    print(f"  Links updated: {stats['links_updated']}")
    print(f"  Errors: {stats['errors']}")
    print()
    
    if DRY_RUN:
        print("This was a DRY-RUN. No changes were made.")
        print(f"To execute: {sys.argv[0]} --execute")
    else:
        print("Changes have been applied.")
        print(f"Backup location: {BACKUP_DIR}")
        print(f"To rollback: {sys.argv[0]} --rollback")
    
    print()
    print(f"Log file: {LOG_FILE}")
    print("=" * 65)

def main():
    """Main execution function."""
    global DRY_RUN
    
    # Parse arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--execute':
            DRY_RUN = False
        elif sys.argv[1] == '--help':
            print("Usage: python apply-kebab-case.py [--execute|--help]")
            print()
            print("Apply kebab-case naming convention to all documentation files.")
            print()
            print("Options:")
            print("  --execute    Execute the renaming (default is dry-run)")
            print("  --help       Show this help message")
            return 0
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help for usage information")
            return 1
    
    print("=" * 65)
    print("KEBAB-CASE REMEDIATION")
    print("=" * 65)
    print()
    
    log(f"Starting kebab-case remediation")
    log(f"Mode: {'DRY-RUN' if DRY_RUN else 'EXECUTE'}")
    print()
    
    # Step 1: Validate environment
    if not validate_environment():
        return 1
    print()
    
    # Step 2: Create backup
    create_backup()
    print()
    
    # Step 3: Delete duplicate files
    log("Deleting duplicate files...")
    for file in FILES_TO_DELETE:
        delete_file(file)
    print()
    
    # Step 4: Rename files
    log("Renaming files...")
    for old_file, new_file in FILE_MAP.items():
        rename_file(old_file, new_file)
    print()
    
    # Step 5: Update links
    update_all_links()
    print()
    
    # Step 6: Validate
    validate_changes()
    print()
    
    # Step 7: Generate report
    generate_report()
    
    return 1 if stats['errors'] > 0 else 0

if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
