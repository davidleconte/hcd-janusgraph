#!/usr/bin/env python3
"""
Baseline Corruption Detection
==============================

Detects corruption or tampering in deterministic baseline files by:
1. Verifying file integrity (checksums match content)
2. Detecting unexpected modifications
3. Validating file formats
4. Checking for missing or extra files

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-04-06
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class BaselineCorruptionDetector:
    """Detect corruption in baseline files."""

    # Expected baseline structure
    REQUIRED_FILES = {
        "checksums.txt",
        "notebook-report.txt",
        "deterministic-status.json",
    }
    
    EXPECTED_NOTEBOOK_COUNT = 16  # Minimum expected notebooks
    
    def __init__(self, baseline_dir: Path):
        """
        Initialize detector.
        
        Args:
            baseline_dir: Directory containing baseline files
        """
        self.baseline_dir = baseline_dir
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.corrupted = False

    def verify_file_integrity(self) -> bool:
        """
        Verify that checksums match actual file content.
        
        Returns:
            True if all checksums match, False otherwise
        """
        checksums_file = self.baseline_dir / "checksums.txt"
        if not checksums_file.exists():
            self.issues.append("checksums.txt not found")
            self.corrupted = True
            return False

        try:
            with open(checksums_file, "r") as f:
                lines = f.readlines()

            all_valid = True
            for line in lines:
                parts = line.strip().split()
                if len(parts) != 2:
                    self.issues.append(f"Invalid checksum line: {line.strip()}")
                    all_valid = False
                    continue

                expected_checksum, filename = parts
                file_path = self.baseline_dir / filename

                if not file_path.exists():
                    self.issues.append(f"File referenced in checksums not found: {filename}")
                    all_valid = False
                    self.corrupted = True
                    continue

                # Calculate actual checksum
                actual_checksum = self._calculate_sha256(file_path)
                
                if actual_checksum != expected_checksum:
                    self.issues.append(
                        f"Checksum mismatch for {filename}: "
                        f"expected {expected_checksum[:16]}..., "
                        f"got {actual_checksum[:16]}..."
                    )
                    all_valid = False
                    self.corrupted = True

            return all_valid

        except Exception as e:
            self.issues.append(f"Error verifying checksums: {e}")
            self.corrupted = True
            return False

    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def check_required_files(self) -> bool:
        """
        Check that all required files are present.
        
        Returns:
            True if all required files exist, False otherwise
        """
        all_present = True
        for filename in self.REQUIRED_FILES:
            file_path = self.baseline_dir / filename
            if not file_path.exists():
                self.issues.append(f"Required file missing: {filename}")
                all_present = False
                self.corrupted = True

        return all_present

    def check_notebook_count(self) -> bool:
        """
        Check that expected number of notebooks are present.
        
        Returns:
            True if notebook count is sufficient, False otherwise
        """
        notebooks = list(self.baseline_dir.glob("*.ipynb"))
        count = len(notebooks)

        if count < self.EXPECTED_NOTEBOOK_COUNT:
            self.issues.append(
                f"Insufficient notebooks: expected ≥{self.EXPECTED_NOTEBOOK_COUNT}, "
                f"found {count}"
            )
            self.corrupted = True
            return False
        
        if count > self.EXPECTED_NOTEBOOK_COUNT + 5:
            self.warnings.append(
                f"Unexpected number of notebooks: expected ~{self.EXPECTED_NOTEBOOK_COUNT}, "
                f"found {count}"
            )

        return True

    def validate_json_files(self) -> bool:
        """
        Validate that JSON files are well-formed.
        
        Returns:
            True if all JSON files are valid, False otherwise
        """
        json_files = [
            "deterministic-status.json",
        ]

        all_valid = True
        for filename in json_files:
            file_path = self.baseline_dir / filename
            if not file_path.exists():
                continue  # Already reported in check_required_files

            try:
                with open(file_path, "r") as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                self.issues.append(f"Invalid JSON in {filename}: {e}")
                all_valid = False
                self.corrupted = True

        # Validate notebook JSON
        notebooks = list(self.baseline_dir.glob("*.ipynb"))
        for nb_file in notebooks:
            try:
                with open(nb_file, "r") as f:
                    nb = json.load(f)
                
                # Basic notebook structure validation
                if "cells" not in nb:
                    self.issues.append(f"Invalid notebook structure in {nb_file.name}: missing 'cells'")
                    all_valid = False
                    self.corrupted = True

            except json.JSONDecodeError as e:
                self.issues.append(f"Invalid JSON in {nb_file.name}: {e}")
                all_valid = False
                self.corrupted = True

        return all_valid

    def check_unexpected_files(self) -> bool:
        """
        Check for unexpected files that shouldn't be in baseline.
        
        Returns:
            True if no unexpected files found, False otherwise
        """
        # Expected file patterns
        expected_patterns = {
            "*.ipynb",  # Notebooks
            "checksums.txt",
            "notebook-report.txt",
            "deterministic-status.json",
            "README.md",  # Optional
        }

        all_files = set(f.name for f in self.baseline_dir.iterdir() if f.is_file())
        
        # Get files matching expected patterns
        expected_files = set()
        for pattern in expected_patterns:
            if "*" in pattern:
                expected_files.update(f.name for f in self.baseline_dir.glob(pattern))
            else:
                expected_files.add(pattern)

        unexpected = all_files - expected_files
        
        # Filter out known safe files
        safe_files = {".gitkeep", ".DS_Store"}
        unexpected = unexpected - safe_files

        if unexpected:
            for filename in unexpected:
                self.warnings.append(f"Unexpected file in baseline: {filename}")
            return False

        return True

    def validate_notebook_report(self) -> bool:
        """
        Validate notebook report format and content.
        
        Returns:
            True if report is valid, False otherwise
        """
        report_file = self.baseline_dir / "notebook-report.txt"
        if not report_file.exists():
            return False  # Already reported in check_required_files

        try:
            with open(report_file, "r") as f:
                content = f.read()

            # Check for expected format
            if not content.strip():
                self.issues.append("notebook-report.txt is empty")
                self.corrupted = True
                return False

            # Count PASS/FAIL entries
            pass_count = content.count("PASS")
            fail_count = content.count("FAIL")
            
            if pass_count == 0 and fail_count == 0:
                self.issues.append("notebook-report.txt contains no PASS/FAIL entries")
                self.corrupted = True
                return False

            # Check for suspicious patterns
            if "ERROR" in content.upper() or "EXCEPTION" in content.upper():
                self.warnings.append("notebook-report.txt contains ERROR/EXCEPTION keywords")

            return True

        except Exception as e:
            self.issues.append(f"Error reading notebook-report.txt: {e}")
            self.corrupted = True
            return False

    def detect_corruption(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all corruption detection checks.
        
        Returns:
            Tuple of (is_corrupted, issues, warnings)
        """
        # Run all checks
        self.check_required_files()
        self.check_notebook_count()
        self.validate_json_files()
        self.validate_notebook_report()
        self.verify_file_integrity()  # Must be last (checks checksums)
        self.check_unexpected_files()

        return self.corrupted, self.issues, self.warnings

    def generate_report(self) -> str:
        """Generate corruption detection report."""
        report = []
        report.append("=" * 80)
        report.append("BASELINE CORRUPTION DETECTION REPORT")
        report.append("=" * 80)
        report.append(f"\nBaseline Directory: {self.baseline_dir}")
        
        if self.corrupted:
            report.append("\nStatus: ❌ CORRUPTED - Integrity issues detected")
        else:
            report.append("\nStatus: ✅ CLEAN - No corruption detected")

        if self.issues:
            report.append("\n" + "-" * 80)
            report.append("CORRUPTION ISSUES")
            report.append("-" * 80)
            for issue in self.issues:
                report.append(f"❌ {issue}")

        if self.warnings:
            report.append("\n" + "-" * 80)
            report.append("WARNINGS")
            report.append("-" * 80)
            for warning in self.warnings:
                report.append(f"⚠️  {warning}")

        if not self.issues and not self.warnings:
            report.append("\n✅ All integrity checks passed")
            report.append("✅ All required files present")
            report.append("✅ All checksums verified")
            report.append("✅ All JSON files valid")
            report.append("✅ Notebook count correct")

        report.append("\n" + "=" * 80)
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Detect corruption in deterministic baseline files"
    )
    parser.add_argument(
        "baseline_dir",
        type=Path,
        help="Directory containing baseline files"
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="Output results as JSON to file"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if any corruption detected"
    )

    args = parser.parse_args()

    if not args.baseline_dir.exists():
        print(f"Error: {args.baseline_dir} does not exist", file=sys.stderr)
        return 1

    # Detect corruption
    detector = BaselineCorruptionDetector(args.baseline_dir)
    corrupted, issues, warnings = detector.detect_corruption()

    # Generate report
    report = detector.generate_report()
    print(report)

    # Output JSON if requested
    if args.json:
        output = {
            "baseline_dir": str(args.baseline_dir),
            "corrupted": corrupted,
            "issues": issues,
            "warnings": warnings,
            "status": "corrupted" if corrupted else "clean"
        }
        with open(args.json, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nResults written to {args.json}")

    # Exit with error in strict mode if corrupted
    if args.strict and corrupted:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
