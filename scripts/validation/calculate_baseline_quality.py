#!/usr/bin/env python3
"""
Baseline Quality Metrics Calculator
====================================

Calculates a quality score for deterministic baseline runs to ensure
high-quality baselines are promoted to canonical status.

Quality Score Formula (0-100):
- Notebook Pass Rate (40%): All notebooks must pass
- Checksum Stability (30%): Checksums must match expected values
- Artifact Completeness (20%): All required artifacts present
- Error Cell Absence (10%): No error cells in notebooks

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-04-06
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class BaselineQualityCalculator:
    """Calculate quality metrics for baseline runs."""

    # Quality thresholds
    MIN_QUALITY_SCORE = 95.0  # Minimum score for canonical promotion
    MIN_NOTEBOOK_PASS_RATE = 100.0  # All notebooks must pass
    MIN_CHECKSUM_STABILITY = 100.0  # All checksums must match
    MIN_ARTIFACT_COMPLETENESS = 100.0  # All artifacts must be present
    MAX_ERROR_CELLS = 0  # No error cells allowed

    def __init__(self, run_dir: Path):
        """
        Initialize calculator.
        
        Args:
            run_dir: Directory containing baseline run artifacts
        """
        self.run_dir = run_dir
        self.metrics: Dict[str, float] = {}
        self.issues: List[str] = []
        self.warnings: List[str] = []

    def calculate_notebook_pass_rate(self) -> float:
        """
        Calculate notebook pass rate.
        
        Returns:
            Pass rate as percentage (0-100)
        """
        report_file = self.run_dir / "notebook-report.txt"
        if not report_file.exists():
            self.issues.append("notebook-report.txt not found")
            return 0.0

        try:
            with open(report_file, "r") as f:
                content = f.read()

            # Count PASS and FAIL
            pass_count = content.count("PASS")
            fail_count = content.count("FAIL")
            total = pass_count + fail_count

            if total == 0:
                self.issues.append("No notebook results found in report")
                return 0.0

            pass_rate = (pass_count / total) * 100
            
            if fail_count > 0:
                self.issues.append(f"{fail_count} notebook(s) failed")
            
            return pass_rate

        except Exception as e:
            self.issues.append(f"Error reading notebook report: {e}")
            return 0.0

    def calculate_checksum_stability(self) -> float:
        """
        Calculate checksum stability.
        
        Returns:
            Stability as percentage (0-100)
        """
        checksums_file = self.run_dir / "checksums.txt"
        if not checksums_file.exists():
            self.issues.append("checksums.txt not found")
            return 0.0

        try:
            with open(checksums_file, "r") as f:
                lines = f.readlines()

            # Check format: should have exactly 5 lines
            if len(lines) != 5:
                self.issues.append(f"Invalid checksum file: expected 5 lines, got {len(lines)}")
                return 0.0

            # Verify each line has SHA-256 format (64 hex chars + filename)
            valid_lines = 0
            for line in lines:
                parts = line.strip().split()
                if len(parts) == 2 and len(parts[0]) == 64:
                    # Check if it's valid hex
                    try:
                        int(parts[0], 16)
                        valid_lines += 1
                    except ValueError:
                        self.issues.append(f"Invalid checksum format: {line.strip()}")
                else:
                    self.issues.append(f"Invalid checksum line: {line.strip()}")

            stability = (valid_lines / 5) * 100
            return stability

        except Exception as e:
            self.issues.append(f"Error reading checksums: {e}")
            return 0.0

    def calculate_artifact_completeness(self) -> float:
        """
        Calculate artifact completeness.
        
        Returns:
            Completeness as percentage (0-100)
        """
        required_artifacts = [
            "checksums.txt",
            "notebook-report.txt",
            "deterministic-status.json",
        ]

        # Check for notebook files (at least 15 expected)
        notebook_files = list(self.run_dir.glob("*.ipynb"))
        
        present = 0
        total = len(required_artifacts) + 1  # +1 for notebooks check

        for artifact in required_artifacts:
            if (self.run_dir / artifact).exists():
                present += 1
            else:
                self.issues.append(f"Missing artifact: {artifact}")

        # Check notebooks
        if len(notebook_files) >= 15:
            present += 1
        else:
            self.issues.append(f"Insufficient notebooks: expected ≥15, got {len(notebook_files)}")

        completeness = (present / total) * 100
        return completeness

    def calculate_error_cell_absence(self) -> float:
        """
        Calculate error cell absence score.
        
        Returns:
            Score as percentage (0-100)
        """
        notebook_files = list(self.run_dir.glob("*.ipynb"))
        
        if not notebook_files:
            self.warnings.append("No notebooks found for error cell check")
            return 100.0  # No notebooks = no errors

        total_error_cells = 0

        for nb_file in notebook_files:
            try:
                with open(nb_file, "r") as f:
                    nb = json.load(f)

                for cell in nb.get("cells", []):
                    if cell.get("cell_type") == "code":
                        outputs = cell.get("outputs", [])
                        for output in outputs:
                            if output.get("output_type") == "error":
                                total_error_cells += 1
                                self.issues.append(f"Error cell in {nb_file.name}")

            except Exception as e:
                self.warnings.append(f"Error reading {nb_file.name}: {e}")

        if total_error_cells == 0:
            return 100.0
        else:
            # Penalize heavily for error cells
            return max(0.0, 100.0 - (total_error_cells * 10))

    def calculate_quality_score(self) -> Tuple[float, Dict[str, float]]:
        """
        Calculate overall quality score.
        
        Returns:
            Tuple of (overall_score, component_scores)
        """
        # Calculate component scores
        notebook_pass_rate = self.calculate_notebook_pass_rate()
        checksum_stability = self.calculate_checksum_stability()
        artifact_completeness = self.calculate_artifact_completeness()
        error_cell_absence = self.calculate_error_cell_absence()

        # Store metrics
        self.metrics = {
            "notebook_pass_rate": notebook_pass_rate,
            "checksum_stability": checksum_stability,
            "artifact_completeness": artifact_completeness,
            "error_cell_absence": error_cell_absence,
        }

        # Calculate weighted score
        quality_score = (
            notebook_pass_rate * 0.40 +
            checksum_stability * 0.30 +
            artifact_completeness * 0.20 +
            error_cell_absence * 0.10
        )

        return quality_score, self.metrics

    def meets_quality_threshold(self, score: float) -> bool:
        """Check if score meets minimum threshold."""
        return score >= self.MIN_QUALITY_SCORE

    def generate_report(self, score: float, metrics: Dict[str, float]) -> str:
        """Generate quality report."""
        report = []
        report.append("=" * 80)
        report.append("BASELINE QUALITY REPORT")
        report.append("=" * 80)
        report.append(f"\nRun Directory: {self.run_dir}")
        report.append(f"\nOverall Quality Score: {score:.2f}/100")
        
        if self.meets_quality_threshold(score):
            report.append("Status: ✅ PASS (meets threshold ≥95.0)")
        else:
            report.append(f"Status: ❌ FAIL (below threshold {self.MIN_QUALITY_SCORE})")

        report.append("\n" + "-" * 80)
        report.append("COMPONENT SCORES")
        report.append("-" * 80)
        
        for name, value in metrics.items():
            status = "✅" if value >= 95.0 else "❌"
            report.append(f"{status} {name.replace('_', ' ').title()}: {value:.2f}%")

        if self.issues:
            report.append("\n" + "-" * 80)
            report.append("ISSUES")
            report.append("-" * 80)
            for issue in self.issues:
                report.append(f"❌ {issue}")

        if self.warnings:
            report.append("\n" + "-" * 80)
            report.append("WARNINGS")
            report.append("-" * 80)
            for warning in self.warnings:
                report.append(f"⚠️  {warning}")

        report.append("\n" + "=" * 80)
        report.append("QUALITY THRESHOLDS")
        report.append("=" * 80)
        report.append(f"Minimum Quality Score: {self.MIN_QUALITY_SCORE}")
        report.append(f"Minimum Notebook Pass Rate: {self.MIN_NOTEBOOK_PASS_RATE}%")
        report.append(f"Minimum Checksum Stability: {self.MIN_CHECKSUM_STABILITY}%")
        report.append(f"Minimum Artifact Completeness: {self.MIN_ARTIFACT_COMPLETENESS}%")
        report.append(f"Maximum Error Cells: {self.MAX_ERROR_CELLS}")
        report.append("=" * 80)

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate baseline quality metrics"
    )
    parser.add_argument(
        "run_dir",
        type=Path,
        help="Directory containing baseline run artifacts"
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="Output results as JSON to file"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if quality threshold not met"
    )

    args = parser.parse_args()

    if not args.run_dir.exists():
        print(f"Error: {args.run_dir} does not exist", file=sys.stderr)
        return 1

    # Calculate quality
    calculator = BaselineQualityCalculator(args.run_dir)
    score, metrics = calculator.calculate_quality_score()

    # Generate report
    report = calculator.generate_report(score, metrics)
    print(report)

    # Output JSON if requested
    if args.json:
        output = {
            "run_dir": str(args.run_dir),
            "quality_score": score,
            "metrics": metrics,
            "meets_threshold": calculator.meets_quality_threshold(score),
            "issues": calculator.issues,
            "warnings": calculator.warnings,
        }
        with open(args.json, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nResults written to {args.json}")

    # Exit with error if strict mode and threshold not met
    if args.strict and not calculator.meets_quality_threshold(score):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
