#!/usr/bin/env python3
"""
Per-package coverage threshold checker.

Reads coverage.json output and validates against package thresholds.
Exits with error if any package is below its minimum threshold.

Usage:
    python scripts/validation/check_package_coverage.py --coverage-file coverage.json
"""

import argparse
import json
import sys
from pathlib import Path


def load_coverage_data(coverage_file: Path) -> dict:
    """Load coverage data from JSON file."""
    with open(coverage_file) as f:
        return json.load(f)


def load_thresholds(thresholds_file: Path) -> dict:
    """Load package thresholds from config file."""
    with open(thresholds_file) as f:
        return json.load(f)


def get_package_coverage(coverage_data: dict, package: str) -> float | None:
    """Get coverage percentage for a specific package."""
    files = coverage_data.get("files", {})
    package_prefix = package.rstrip("/") + "/"
    
    total_lines = 0
    covered_lines = 0
    
    for file_path, file_data in files.items():
        if file_path.startswith(package_prefix):
            summary = file_data.get("summary", {})
            total_lines += summary.get("num_statements", 0)
            covered_lines += summary.get("covered_lines", 0)
    
    if total_lines == 0:
        return None
    
    return (covered_lines / total_lines) * 100


def main():
    parser = argparse.ArgumentParser(description="Check per-package coverage thresholds")
    parser.add_argument(
        "--coverage-file",
        type=Path,
        default=Path("coverage.json"),
        help="Path to coverage JSON file",
    )
    parser.add_argument(
        "--thresholds-file",
        type=Path,
        default=Path("config/coverage/package_thresholds.json"),
        help="Path to package thresholds config",
    )
    args = parser.parse_args()
    
    if not args.coverage_file.exists():
        print(f"❌ Coverage file not found: {args.coverage_file}")
        sys.exit(1)
    
    if not args.thresholds_file.exists():
        print(f"❌ Thresholds file not found: {args.thresholds_file}")
        sys.exit(1)
    
    coverage_data = load_coverage_data(args.coverage_file)
    thresholds = load_thresholds(args.thresholds_file)
    
    package_thresholds = thresholds.get("package_thresholds", {})
    all_passed = True
    warnings = []
    
    print("📊 Per-Package Coverage Check")
    print("=" * 60)
    
    for package, config in package_thresholds.items():
        minimum = config.get("minimum", 70)
        target = config.get("target", 80)
        current = get_package_coverage(coverage_data, package)
        
        if current is None:
            print(f"⚠️  {package}: No coverage data found")
            continue
        
        status = "✅"
        if current < minimum:
            status = "❌"
            all_passed = False
        elif current < target:
            status = "⚠️"
            warnings.append(package)
        
        print(f"{status} {package}: {current:.1f}% (min: {minimum}%, target: {target}%)")
    
    print("=" * 60)
    
    if not all_passed:
        print("❌ Coverage check FAILED - packages below minimum threshold")
        sys.exit(1)
    
    if warnings:
        print(f"⚠️  Coverage warnings - packages below target: {', '.join(warnings)}")
    
    print("✅ All package coverage thresholds met")
    sys.exit(0)


if __name__ == "__main__":
    main()
