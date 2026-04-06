#!/usr/bin/env python3
"""
Notebook Determinism Scanner
=============================

Scans Jupyter notebooks for non-deterministic patterns and provides
recommendations for fixes.

Hard Patterns (must fix):
- datetime.now()
- random.random() without seed
- uuid.uuid4()
- time.time()

Warn Patterns (document):
- Network calls (requests, urllib)
- File system operations
- External service dependencies

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-04-06
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Hard patterns that MUST be fixed
HARD_PATTERNS = {
    "datetime.now()": {
        "pattern": r"datetime\.now\(\)",
        "fix": "Use REFERENCE_TIMESTAMP from banking.data_generators.utils.deterministic",
        "severity": "ERROR",
    },
    "random.random()": {
        "pattern": r"random\.random\(\)",
        "fix": "Use random.Random(seed).random() with explicit seed",
        "severity": "ERROR",
    },
    "uuid.uuid4()": {
        "pattern": r"uuid\.uuid4\(\)",
        "fix": "Use generate_deterministic_uuid(seed, counter) from deterministic.py",
        "severity": "ERROR",
    },
    "time.time()": {
        "pattern": r"time\.time\(\)",
        "fix": "Use fixed timestamp or REFERENCE_TIMESTAMP.timestamp()",
        "severity": "ERROR",
    },
    "np.random without seed": {
        "pattern": r"np\.random\.(rand|randn|randint|choice|shuffle)\(",
        "fix": "Use np.random.seed(42) before np.random calls or use np.random.RandomState(seed)",
        "severity": "ERROR",
        "check_seed": True,  # Special flag to check if seed is set in cell
    },
}

# Warn patterns that should be documented
WARN_PATTERNS = {
    "requests": {
        "pattern": r"requests\.(get|post|put|delete|patch)",
        "fix": "Document as non-deterministic or mock in tests",
        "severity": "WARNING",
    },
    "urllib": {
        "pattern": r"urllib\.request\.",
        "fix": "Document as non-deterministic or mock in tests",
        "severity": "WARNING",
    },
    "open file": {
        "pattern": r"open\(['\"](?!.*\/tmp\/)[^'\"]+['\"]",
        "fix": "Document expected file state or use fixtures",
        "severity": "WARNING",
    },
    "subprocess": {
        "pattern": r"subprocess\.(run|call|Popen)",
        "fix": "Document as non-deterministic or mock in tests",
        "severity": "WARNING",
    },
}


class NotebookScanner:
    """Scanner for Jupyter notebooks."""

    def __init__(self, notebook_path: Path):
        self.notebook_path = notebook_path
        self.violations: List[Dict] = []
        self.warnings: List[Dict] = []

    def scan(self) -> Tuple[List[Dict], List[Dict]]:
        """Scan notebook for determinism issues."""
        try:
            with open(self.notebook_path, "r", encoding="utf-8") as f:
                notebook = json.load(f)
        except Exception as e:
            print(f"Error loading {self.notebook_path}: {e}", file=sys.stderr)
            return [], []

        # Scan all code cells
        for cell_idx, cell in enumerate(notebook.get("cells", [])):
            if cell.get("cell_type") != "code":
                continue

            source = "".join(cell.get("source", []))
            cell_number = cell_idx + 1

            # Check hard patterns
            for pattern_name, pattern_info in HARD_PATTERNS.items():
                matches = re.finditer(pattern_info["pattern"], source)
                for match in matches:
                    line_num = source[: match.start()].count("\n") + 1
                    
                    # Special handling for np.random - check if seed is set in cell
                    if pattern_info.get("check_seed"):
                        # Check if np.random.seed appears before this match in the cell
                        before_match = source[: match.start()]
                        if "np.random.seed(" in before_match:
                            continue  # Skip this violation, seed is set
                    
                    self.violations.append(
                        {
                            "cell": cell_number,
                            "line": line_num,
                            "pattern": pattern_name,
                            "match": match.group(0),
                            "fix": pattern_info["fix"],
                            "severity": pattern_info["severity"],
                        }
                    )

            # Check warn patterns
            for pattern_name, pattern_info in WARN_PATTERNS.items():
                matches = re.finditer(pattern_info["pattern"], source)
                for match in matches:
                    line_num = source[: match.start()].count("\n") + 1
                    self.warnings.append(
                        {
                            "cell": cell_number,
                            "line": line_num,
                            "pattern": pattern_name,
                            "match": match.group(0),
                            "fix": pattern_info["fix"],
                            "severity": pattern_info["severity"],
                        }
                    )

        return self.violations, self.warnings


def scan_directory(directory: Path, recursive: bool = True) -> Dict[str, Tuple[List, List]]:
    """Scan all notebooks in directory."""
    results = {}

    if recursive:
        notebooks = list(directory.rglob("*.ipynb"))
    else:
        notebooks = list(directory.glob("*.ipynb"))

    # Filter out checkpoints and trash
    notebooks = [
        nb
        for nb in notebooks
        if ".ipynb_checkpoints" not in str(nb) and ".Trash" not in str(nb)
    ]

    for notebook_path in notebooks:
        scanner = NotebookScanner(notebook_path)
        violations, warnings = scanner.scan()
        if violations or warnings:
            results[str(notebook_path)] = (violations, warnings)

    return results


def print_results(results: Dict[str, Tuple[List, List]], verbose: bool = False):
    """Print scan results."""
    total_violations = 0
    total_warnings = 0

    print("\n" + "=" * 80)
    print("NOTEBOOK DETERMINISM SCAN RESULTS")
    print("=" * 80 + "\n")

    if not results:
        print("✅ No determinism issues found!\n")
        return

    for notebook_path, (violations, warnings) in sorted(results.items()):
        total_violations += len(violations)
        total_warnings += len(warnings)

        print(f"\n📓 {notebook_path}")
        print("-" * 80)

        if violations:
            print(f"\n❌ ERRORS ({len(violations)}):")
            for v in violations:
                print(f"  Cell {v['cell']}, Line {v['line']}: {v['pattern']}")
                print(f"    Found: {v['match']}")
                print(f"    Fix: {v['fix']}")
                if verbose:
                    print()

        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for w in warnings:
                print(f"  Cell {w['cell']}, Line {w['line']}: {w['pattern']}")
                print(f"    Found: {w['match']}")
                print(f"    Fix: {w['fix']}")
                if verbose:
                    print()

    print("\n" + "=" * 80)
    print(f"SUMMARY: {total_violations} errors, {total_warnings} warnings")
    print("=" * 80 + "\n")

    if total_violations > 0:
        print("❌ FAILED: Fix all errors before proceeding")
        return 1
    elif total_warnings > 0:
        print("⚠️  WARNING: Document all warnings")
        return 0
    else:
        print("✅ PASSED: No issues found")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Scan Jupyter notebooks for determinism issues"
    )
    parser.add_argument(
        "path", type=Path, help="Notebook file or directory to scan"
    )
    parser.add_argument(
        "--recursive", "-r", action="store_true", help="Scan directories recursively"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--json", "-j", type=Path, help="Output results as JSON to file"
    )

    args = parser.parse_args()

    if not args.path.exists():
        print(f"Error: {args.path} does not exist", file=sys.stderr)
        return 1

    # Scan
    if args.path.is_file():
        scanner = NotebookScanner(args.path)
        violations, warnings = scanner.scan()
        results = {str(args.path): (violations, warnings)}
    else:
        results = scan_directory(args.path, args.recursive)

    # Output JSON if requested
    if args.json:
        with open(args.json, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results written to {args.json}")

    # Print results
    return print_results(results, args.verbose)


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
