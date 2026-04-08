#!/usr/bin/env python3
"""
Fix Orchestrator Random Calls
==============================

Reverts incorrect faker.random changes in orchestrator files that don't
inherit from BaseGenerator. These files use random.seed() directly.

Author: AI Code Review System
Date: 2026-04-08
"""

import re
from pathlib import Path

# Files to fix
FILES_TO_FIX = [
    "banking/data_generators/orchestration/master_orchestrator.py",
    "banking/streaming/streaming_orchestrator.py",
]

# Revert patterns
REVERT_PATTERNS = [
    (r'self\.faker\.random\.random\(\)', r'random.random()'),
    (r'self\.faker\.random\.randint\(', r'random.randint('),
    (r'self\.faker\.random\.choice\(', r'random.choice('),
    (r'self\.faker\.random\.uniform\(', r'random.uniform('),
    (r'self\.faker\.random\.sample\(', r'random.sample('),
]


def fix_file(file_path: Path) -> int:
    """Fix a single file by reverting incorrect changes."""
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return 0
    
    content = file_path.read_text()
    original_content = content
    
    total_replacements = 0
    for pattern, replacement in REVERT_PATTERNS:
        matches = list(re.finditer(pattern, content))
        if matches:
            content = re.sub(pattern, replacement, content)
            count = len(matches)
            total_replacements += count
            print(f"  - Reverted {count} instances of {pattern}")
    
    if content != original_content:
        file_path.write_text(content)
        print(f"✅ Fixed {file_path}")
    else:
        print(f"⚠️  No changes needed in {file_path}")
    
    return total_replacements


def main():
    """Main execution function."""
    print("=" * 80)
    print("Fixing Orchestrator Random Calls")
    print("=" * 80)
    print()
    
    total_replacements = 0
    for file_path_str in FILES_TO_FIX:
        file_path = Path(file_path_str)
        count = fix_file(file_path)
        total_replacements += count
        print()
    
    print("=" * 80)
    print(f"Total replacements: {total_replacements}")
    print("✅ Orchestrator files fixed!")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    exit(main())

# Made with Bob
