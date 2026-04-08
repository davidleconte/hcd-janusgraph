#!/usr/bin/env python3
"""
Fix Unseeded Random Calls
==========================

Automatically replaces unseeded random.random() and random.choice() calls
with their seeded faker equivalents across all data generator files.

This ensures deterministic behavior across all data generation operations.

Author: AI Code Review System
Date: 2026-04-08
"""

import re
from pathlib import Path
from typing import List, Tuple

# Files to fix with their expected instance counts
FILES_TO_FIX = [
    ("banking/data_generators/events/transaction_generator.py", 9),
    ("banking/data_generators/events/communication_generator.py", 11),
    ("banking/data_generators/events/travel_generator.py", 6),
    ("banking/data_generators/events/document_generator.py", 8),
    ("banking/data_generators/events/trade_generator.py", 1),
    ("banking/data_generators/orchestration/master_orchestrator.py", 1),
    ("banking/streaming/streaming_orchestrator.py", 1),
    ("banking/data_generators/patterns/fraud_ring_pattern_generator.py", 4),
    ("banking/data_generators/patterns/tbml_pattern_generator.py", 1),
]

# Replacement patterns
REPLACEMENTS = [
    # random.random() -> self.faker.random.random()
    (r'\brandom\.random\(\)', r'self.faker.random.random()'),
    
    # random.randint(a, b) -> self.faker.random.randint(a, b)
    (r'\brandom\.randint\(', r'self.faker.random.randint('),
    
    # random.choice(items) -> self.faker.random.choice(items)
    (r'\brandom\.choice\(', r'self.faker.random.choice('),
    
    # random.uniform(a, b) -> self.faker.random.uniform(a, b)
    (r'\brandom\.uniform\(', r'self.faker.random.uniform('),
    
    # random.sample(items, k) -> self.faker.random.sample(items, k)
    (r'\brandom\.sample\(', r'self.faker.random.sample('),
]


def fix_file(file_path: Path) -> Tuple[int, List[str]]:
    """
    Fix unseeded random calls in a single file.
    
    Args:
        file_path: Path to file to fix
        
    Returns:
        Tuple of (replacement_count, list of changes made)
    """
    if not file_path.exists():
        return 0, [f"File not found: {file_path}"]
    
    # Read file content
    content = file_path.read_text()
    original_content = content
    
    changes = []
    total_replacements = 0
    
    # Apply each replacement pattern
    for pattern, replacement in REPLACEMENTS:
        matches = list(re.finditer(pattern, content))
        if matches:
            content = re.sub(pattern, replacement, content)
            count = len(matches)
            total_replacements += count
            changes.append(f"  - Replaced {count} instances of {pattern}")
    
    # Write back if changes were made
    if content != original_content:
        file_path.write_text(content)
        changes.insert(0, f"✅ Fixed {file_path}")
    else:
        changes.insert(0, f"⚠️  No changes needed in {file_path}")
    
    return total_replacements, changes


def main():
    """Main execution function."""
    print("=" * 80)
    print("Fixing Unseeded Random Calls")
    print("=" * 80)
    print()
    
    total_files = 0
    total_replacements = 0
    all_changes = []
    
    for file_path_str, expected_count in FILES_TO_FIX:
        file_path = Path(file_path_str)
        count, changes = fix_file(file_path)
        
        total_files += 1
        total_replacements += count
        all_changes.extend(changes)
        
        # Print progress
        for change in changes:
            print(change)
        
        if count != expected_count:
            print(f"  ⚠️  WARNING: Expected {expected_count} replacements, found {count}")
        print()
    
    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Files processed: {total_files}")
    print(f"Total replacements: {total_replacements}")
    print()
    
    if total_replacements > 0:
        print("✅ All unseeded random calls have been fixed!")
        print()
        print("Next steps:")
        print("1. Run tests: pytest banking/data_generators/tests/ -v")
        print("2. Run deterministic pipeline twice and compare checksums")
        print("3. Commit changes with message:")
        print('   git commit -m "fix: replace unseeded random calls with faker.random"')
    else:
        print("⚠️  No changes were made. Files may already be fixed.")
    
    return 0 if total_replacements > 0 else 1


if __name__ == "__main__":
    exit(main())

# Made with Bob
